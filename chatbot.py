"""Le chatbot : un LLM (Groq, compatible OpenAI) qui répond en appelant les outils MCP.

Le parcours d'une question :
1. le chatbot lance le serveur MCP (mcp_server.py) en sous-processus et lit sa liste d'outils ;
2. il envoie la conversation et les outils au LLM ;
3. si le LLM demande un outil, le chatbot l'exécute via MCP, l'outil appelle l'API FastAPI,
   et le résultat repart au LLM ; on recommence jusqu'à une réponse en texte.
Les outils appelés sont gardés et affichés sous la réponse : l'utilisateur voit d'où viennent
les chiffres.

Réglages (.streamlit/secrets.toml, ou les Secrets de Streamlit Cloud) :
LLM_URL, LLM_KEY, LLM_MODEL, API_URL. Voir .streamlit/secrets.toml.example.
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

SERVEUR_MCP = Path(__file__).with_name("mcp_server.py")
MAX_TOURS = 6  # au plus 6 allers-retours LLM ↔ outils par question
TAILLE_MAX_RESULTAT = 12_000  # caractères d'un résultat d'outil renvoyés au LLM

CONSIGNE = """Tu es l'assistant de la direction des collèges du Département du Loiret.
Tu aides à choisir les collèges publics à diagnostiquer en priorité face aux risques.

Règles :
- Réponds en français, en quelques phrases ou une courte liste.
- N'utilise QUE les chiffres renvoyés par les outils. N'invente rien. Si un outil échoue ou
  ne renvoie rien, dis-le simplement.
- Pour un collège cité par son nom, appelle d'abord chercher_college pour obtenir son uai,
  puis fiche_college.
- Cite toujours le nom du collège et sa commune.
- Rappelle si utile qu'un aléa n'est pas un risque avéré, qu'un ancien site industriel n'est
  pas une pollution prouvée, et que la prévision d'effectifs a une marge d'erreur.
- Familles de risque : sol, inondation, techno (technologique), pollution (sols pollués).
- Les effectifs sont ceux de la rentrée 2025. Pour une année future, horizon = année - 2025
  (2028 → 3) et utilise les champs « prévus » (effectif_prevu, eleves_cumul_prevu) ; précise
  alors que c'est une prévision."""


def outils_au_format_openai(outils) -> list[dict]:
    """Les outils MCP (nom, description, schéma JSON) au format attendu par l'API OpenAI."""
    return [
        {
            "type": "function",
            "function": {
                "name": o.name,
                "description": o.description or "",
                "parameters": o.inputSchema,
            },
        }
        for o in outils
    ]


def texte_resultat(resultat) -> str:
    """Le contenu texte d'un résultat d'outil MCP, tronqué pour ne pas saturer le LLM."""
    texte = "\n".join(c.text for c in resultat.content if getattr(c, "text", None))
    return texte[:TAILLE_MAX_RESULTAT]


def nettoyer(texte: str | None) -> str:
    """Retire le raisonnement <think>…</think> que certains modèles ajoutent."""
    return re.sub(r"<think>.*?</think>", "", texte or "", flags=re.DOTALL).strip()


def parametres_serveur(api_url: str) -> StdioServerParameters:
    """Le serveur MCP lancé avec le Python du projet, et l'adresse de l'API à appeler."""
    return StdioServerParameters(
        command=sys.executable,
        args=[str(SERVEUR_MCP)],
        env={**os.environ, "API_URL": api_url},
    )


async def _repondre(
    conversation: list[dict], llm: OpenAI, modele: str, api_url: str
) -> tuple[str, list[dict]]:
    appels = []
    async with (
        stdio_client(parametres_serveur(api_url)) as (lire, ecrire),
        ClientSession(lire, ecrire) as session,
    ):
        await session.initialize()
        outils = outils_au_format_openai((await session.list_tools()).tools)
        messages = [{"role": "system", "content": CONSIGNE}, *conversation]
        for _ in range(MAX_TOURS):
            reponse = llm.chat.completions.create(
                model=modele, messages=messages, tools=outils, temperature=0
            )
            message = reponse.choices[0].message
            if not message.tool_calls:
                return nettoyer(message.content), appels
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [t.model_dump() for t in message.tool_calls],
                }
            )
            for appel in message.tool_calls:
                arguments = json.loads(appel.function.arguments or "{}")
                resultat = await session.call_tool(appel.function.name, arguments)
                appels.append(
                    {
                        "outil": appel.function.name,
                        "arguments": arguments,
                        "erreur": bool(resultat.isError),
                    }
                )
                messages.append(
                    {"role": "tool", "tool_call_id": appel.id, "content": texte_resultat(resultat)}
                )
    return "Je n'ai pas réussi à conclure : reformulez la question plus simplement.", appels


def repondre(
    conversation: list[dict], url: str, cle: str, modele: str, api_url: str
) -> tuple[str, list[dict]]:
    """Répond à la dernière question de `conversation` ; renvoie le texte et les outils appelés."""
    llm = OpenAI(base_url=url, api_key=cle)
    return asyncio.run(_repondre(conversation, llm, modele, api_url))


async def _lister_outils(api_url: str) -> list[str]:
    async with (
        stdio_client(parametres_serveur(api_url)) as (lire, ecrire),
        ClientSession(lire, ecrire) as session,
    ):
        await session.initialize()
        return [o.name for o in (await session.list_tools()).tools]


def lister_outils(api_url: str) -> list[str]:
    """Les noms des outils du serveur MCP (sert aux tests et au diagnostic)."""
    return asyncio.run(_lister_outils(api_url))


async def _appeler_outil(api_url: str, nom: str, arguments: dict) -> tuple[bool, str]:
    async with (
        stdio_client(parametres_serveur(api_url)) as (lire, ecrire),
        ClientSession(lire, ecrire) as session,
    ):
        await session.initialize()
        resultat = await session.call_tool(nom, arguments)
        return bool(resultat.isError), texte_resultat(resultat)


def appeler_outil(api_url: str, nom: str, arguments: dict) -> tuple[bool, str]:
    """Appelle un outil MCP sans LLM : (erreur ?, texte du résultat). Sert aux tests."""
    return asyncio.run(_appeler_outil(api_url, nom, arguments))
