"""La chaîne chatbot → serveur MCP → API FastAPI, sans clé Groq.

Un faux LLM joue le rôle de Groq : au premier appel il demande l'outil chercher_college,
au second il répond en citant le résultat. L'API tourne dans un thread, sur un port libre.
"""

import asyncio
import json
import socket
import threading
import time
from types import SimpleNamespace

import pytest
import uvicorn
from fastapi.testclient import TestClient

import api
import chatbot


@pytest.fixture(scope="module")
def api_url():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    serveur = uvicorn.Server(
        uvicorn.Config(api.app, host="127.0.0.1", port=port, log_level="error")
    )
    threading.Thread(target=serveur.run, daemon=True).start()
    while not serveur.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    serveur.should_exit = True


def message(texte=None, appels=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
        content=texte, tool_calls=appels))])  # fmt: skip


class FauxLLM:
    """Imite client.chat.completions.create : un appel d'outil, puis une réponse."""

    def __init__(self):
        self.recus = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, model, messages, tools, temperature):
        self.recus.append(messages)
        if len(self.recus) == 1:
            appel = SimpleNamespace(
                id="appel-1",
                function=SimpleNamespace(name="chercher_college", arguments='{"texte": "jargeau"}'),
                model_dump=lambda: {"id": "appel-1", "type": "function", "function": {
                    "name": "chercher_college", "arguments": '{"texte": "jargeau"}'}},
            )  # fmt: skip
            return message(appels=[appel])
        resultat = json.loads(messages[-1]["content"])[0]  # une liste de collèges trouvés
        return message(texte=f"<think>…</think>Le collège de Jargeau est {resultat['nom']}.")


def test_les_cinq_outils_sont_exposes(api_url):
    assert chatbot.lister_outils(api_url) == [
        "indicateurs_risques", "classement_colleges", "chercher_college", "fiche_college",
        "arretes_catnat",
    ]  # fmt: skip


def test_la_boucle_outil_puis_reponse(api_url):
    llm = FauxLLM()
    texte, appels = asyncio.run(
        chatbot._repondre([{"role": "user", "content": "Jargeau ?"}], llm, "faux", api_url)
    )
    assert texte == "Le collège de Jargeau est Clos Ferbois."  # <think> retiré
    assert appels == [
        {"outil": "chercher_college", "arguments": {"texte": "jargeau"}, "erreur": False}
    ]
    assert llm.recus[1][-1]["role"] == "tool"  # le résultat de l'outil est renvoyé au LLM


def test_une_commune_inconnue_donne_une_erreur_lisible(api_url):
    erreur, texte = chatbot.appeler_outil(api_url, "arretes_catnat", {"commune": "Paris"})
    assert erreur and "Commune sans collège public" in texte


def test_l_api_valide_ses_parametres():
    client = TestClient(api.app)
    assert client.get("/colleges", params={"horizon": 9}).status_code == 422
    assert client.get("/colleges/INCONNU").status_code == 404
    premier = client.get("/colleges", params={"limit": 1}).json()[0]
    assert premier["rang"] == 1 and premier["nb_familles"] >= 1


def test_un_quota_groq_depasse_donne_un_message_clair():
    import httpx
    from openai import RateLimitError

    reponse = httpx.Response(429, request=httpx.Request("POST", "https://api.groq.com"))
    enveloppe = ExceptionGroup("TaskGroup", [RateLimitError("429", response=reponse, body=None)])
    assert isinstance(chatbot.cause(enveloppe), RateLimitError)
    assert "quota" in chatbot.message_erreur(enveloppe)


def test_l_historique_envoye_au_llm_reste_court():
    conversation = [{"role": "user", "content": f"q{i}"} for i in range(10)]
    conversation[5] = {"role": "assistant", "content": "x" * 5000}
    court = chatbot.historique_court(conversation)
    assert court[-1]["content"] == "q9"  # la question est toujours envoyée
    assert len(court) == chatbot.ECHANGES_GARDES + 1
    assert all(len(m["content"]) <= chatbot.TAILLE_MAX_ANCIENNE_REPONSE for m in court[:-1])


def test_un_parametre_null_prend_la_valeur_par_defaut(api_url):
    erreur, texte = chatbot.appeler_outil(
        api_url, "classement_colleges", {"horizon": None, "limit": None, "min_risques": None}
    )
    assert not erreur and len(json.loads(texte)) == 5  # 5 collèges par défaut, JSON compact
