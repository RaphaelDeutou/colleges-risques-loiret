"""Le serveur MCP du projet : des outils qu'un LLM peut appeler, au-dessus de l'API FastAPI.

Le LLM choisit un outil d'après son nom, sa docstring et ses arguments : ils sont rédigés
pour lui. Chaque outil appelle une route de api.py ; aucun chiffre n'est inventé ici.

Lancer : c'est le client qui le lance (le chatbot de l'appli, en stdio). Lancé à la main, il
n'affiche rien et attend un client : c'est normal.
Tester : npx @modelcontextprotocol/inspector uv run python mcp_server.py
L'adresse de l'API vient de la variable d'environnement API_URL (http://127.0.0.1:8000 par
défaut ; l'URL Render une fois déployé).
"""

import os
from typing import Annotated, Any, Literal

import requests
from mcp.server.fastmcp import FastMCP
from pydantic import Field

API = os.environ.get("API_URL", "http://127.0.0.1:8000").rstrip("/")
mcp = FastMCP("colleges-risques-loiret", log_level="WARNING")

Famille = Literal["sol", "inondation", "techno", "pollution"]
Horizon = Annotated[
    int,
    Field(
        ge=1,
        le=5,
        description="Nombre d'années après la rentrée 2025 : 2026 → 1, 2027 → 2, 2028 → 3, "
        "2029 → 4, 2030 → 5.",
    ),
]


def appeler_api(chemin: str, **params: Any) -> Any:
    """GET sur l'API ; une erreur lisible pour le LLM si l'API refuse ou ne répond pas."""
    params = {k: v for k, v in params.items() if v is not None}
    try:
        # 60 s : sur Render, le premier appel réveille le service, qui met environ une minute.
        reponse = requests.get(f"{API}{chemin}", params=params, timeout=60)
    except requests.RequestException as erreur:
        raise RuntimeError(f"L'API ne répond pas ({API}) : {erreur}") from erreur
    if reponse.status_code >= 400:
        detail = reponse.json().get("detail", reponse.text) if reponse.content else ""
        raise RuntimeError(f"L'API a refusé la demande ({reponse.status_code}) : {detail}")
    return reponse.json()


@mcp.tool()
def indicateurs_risques(
    commune: str | None = None,
    familles: list[Famille] | None = None,
    horizon: Horizon = 3,
) -> dict[str, Any]:
    """Chiffres clés des collèges publics du Loiret exposés aux risques.

    Renvoie : colleges (nombre de collèges), colleges_cumul (collèges qui cumulent au moins
    2 familles de risque), eleves_cumul (leurs élèves à la rentrée 2025),
    eleves_cumul_prevu (leurs élèves PRÉVUS en annee_prevue = 2025 + horizon),
    colleges_expose et eleves_expose (au moins 1 risque, en 2025).
    Pour une question sur une année future, choisissez horizon = année - 2025 et répondez avec
    eleves_cumul_prevu. Sans commune : tout le département.
    Familles : sol, inondation, techno (technologique), pollution (sols pollués).
    """
    return appeler_api("/indicateurs", commune=commune, familles=familles, horizon=horizon)


@mcp.tool()
def classement_colleges(
    commune: str | None = None,
    min_risques: Annotated[int, Field(ge=0, le=4)] = 1,
    limit: Annotated[int, Field(ge=1, le=58)] = 10,
    familles: list[Famille] | None = None,
    horizon: Horizon = 3,
) -> list[dict[str, Any]]:
    """Classement des collèges publics à diagnostiquer en priorité.

    Trié par nombre de familles de risque (sol, inondation, technologique, sols pollués),
    puis par nombre d'élèves. Chaque ligne donne le rang, l'identifiant uai, le nom, la
    commune, les élèves en 2025 et prévus, les familles et les diagnostics à demander.
    Utilisez-le pour « quels collèges en priorité », « les plus exposés », « à Orléans ».
    """
    return appeler_api(
        "/colleges",
        commune=commune,
        min_risques=min_risques,
        limit=limit,
        familles=familles,
        horizon=horizon,
    )


@mcp.tool()
def chercher_college(texte: Annotated[str, Field(min_length=2)]) -> list[dict[str, Any]]:
    """Trouve l'identifiant uai d'un collège à partir de son nom ou de sa commune.

    À appeler avant fiche_college quand l'utilisateur donne un nom (« Montjoie »,
    « le collège de Jargeau ») : renvoie uai, nom et commune des collèges qui correspondent.
    """
    return appeler_api("/colleges/recherche", q=texte)


@mcp.tool()
def fiche_college(uai: str, horizon: Horizon = 3) -> dict[str, Any]:
    """Fiche détaillée d'un collège, à partir de son identifiant uai (voir chercher_college).

    Renvoie : rang, élèves, familles de risque (vrai/faux), l'explication chiffrée de chaque
    famille (« pourquoi »), les diagnostics à demander, l'historique des effectifs, la
    prévision à l'horizon choisi avec l'erreur moyenne du modèle, les arrêtés CatNat de la
    commune et l'année du DICRIM (null s'il n'y en a pas).
    """
    return appeler_api(f"/colleges/{uai}", horizon=horizon)


@mcp.tool()
def arretes_catnat(commune: str) -> list[dict[str, Any]]:
    """Arrêtés de catastrophe naturelle (CatNat) d'une commune, par année et par péril.

    Péril : sécheresse, inondation, mouvement de terrain. C'est le risque déjà vécu par la
    commune ; un arrêté suppose que le maire en ait fait la demande.
    """
    return appeler_api(f"/communes/{commune}/catnat")


if __name__ == "__main__":
    mcp.run(transport="stdio")
