"""L'API FastAPI du projet : les collèges, leurs risques et leurs prévisions, en JSON.

Les calculs sont ceux de risques.py, les mêmes que l'appli : l'API, l'appli et le chatbot
donnent les mêmes chiffres. Le serveur MCP (mcp_server.py) appelle cette API.

Lancer en local : uv run uvicorn api:app --host 127.0.0.1 --port 8000 --reload
Documentation interactive : http://127.0.0.1:8000/docs
Sur Render : voir render.yaml (uvicorn api:app --host 0.0.0.0 --port $PORT).
"""

import json
import unicodedata
from typing import Annotated, Literal

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query

from risques import (
    DIAGNOSTICS,
    FAMILLES,
    FAMILLES_COURT,
    SEUIL_CASIAS,
    SEUIL_SEVESO_KM,
    ajouter_familles,
    ajouter_prevision,
    catnat_commune,
    charger_catnat,
    charger_historique,
    charger_previsions,
    charger_priorite,
    classer,
    compter_familles,
    facteurs,
    filtrer_communes,
    historique_college,
    indicateurs,
)

Famille = Literal["sol", "inondation", "techno", "pollution"]
CarteArgiles = Literal["geoloiret", "georisques"]

app = FastAPI(
    title="Collèges et risques · Loiret",
    version="1.0",
    description="Les 58 collèges publics du Loiret, leurs familles de risque, le diagnostic à "
    "demander et la prévision de leurs effectifs. Sources : GéoLoiret, Géorisques, Éducation "
    "nationale (Licence Ouverte 2.0).",
)

COLLEGES = charger_priorite()
HISTORIQUE = charger_historique()
CATNAT = charger_catnat()
PREVISIONS, ERREURS = charger_previsions()
COMMUNES = sorted(COLLEGES["commune"].unique())


def json_propre(donnees: pd.DataFrame) -> list[dict[str, object]]:
    """Convertit les valeurs pandas (dont les valeurs manquantes) en JSON standard."""
    return json.loads(donnees.to_json(orient="records", force_ascii=False))


def sans_accents(texte: str) -> str:
    """« Orléans » -> « orleans », pour une recherche qui ignore accents et majuscules."""
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c)).lower().strip()


def reglages(
    familles: Annotated[
        list[Famille] | None, Query(description="Familles comptées (toutes par défaut).")
    ] = None,
    seuil_seveso_km: Annotated[float, Query(ge=0.5, le=5.0)] = SEUIL_SEVESO_KM,
    carte_argiles: CarteArgiles = "geoloiret",
    seuil_casias: Annotated[int, Query(ge=1, le=50)] = SEUIL_CASIAS,
    horizon: Annotated[int, Query(ge=1, le=5, description="Prévision à 1-5 ans.")] = 3,
    eleves: Literal["effectif_total", "effectif_prevu"] = "effectif_total",
) -> dict:
    """Les réglages de l'appli, communs à toutes les routes ; validés par FastAPI (422 sinon)."""
    choisies = familles or list(FAMILLES)
    vue = compter_familles(
        ajouter_familles(COLLEGES, seuil_seveso_km, carte_argiles, seuil_casias), choisies
    )
    vue = classer(ajouter_prevision(vue, PREVISIONS, horizon), eleves)
    return {
        "vue": vue,
        "familles": choisies,
        "seuil_seveso_km": seuil_seveso_km,
        "seuil_casias": seuil_casias,
        "horizon": horizon,
    }


Reglages = Annotated[dict, Depends(reglages)]


def commune_connue(commune: str | None) -> list[str]:
    """Une commune du projet, ou une erreur 404 qui liste des communes proches."""
    if not commune:
        return []
    cible = sans_accents(commune)
    trouvees = [c for c in COMMUNES if sans_accents(c) == cible]
    if not trouvees:
        proches = [c for c in COMMUNES if cible[:4] in sans_accents(c)][:5]
        raise HTTPException(404, f"Commune sans collège public : {commune}. Proches : {proches}")
    return trouvees


@app.get("/sante")
def sante() -> dict[str, object]:
    """Vérifie que l'API répond (Render réveille le service au premier appel)."""
    return {"statut": "ok", "colleges": len(COLLEGES), "communes": len(COMMUNES)}


@app.get("/communes")
def communes() -> list[str]:
    """Les communes qui ont au moins un collège public."""
    return COMMUNES


@app.get("/indicateurs")
def lire_indicateurs(r: Reglages, commune: str | None = None) -> dict[str, object]:
    """Les chiffres du haut de page : collèges et élèves exposés, sur la vue filtrée."""
    vue = filtrer_communes(r["vue"], commune_connue(commune))
    return {
        **indicateurs(vue),
        "annee_prevue": 2025 + r["horizon"],
        "familles": r["familles"],
        "commune": commune,
    }


@app.get("/colleges")
def lire_colleges(
    r: Reglages,
    commune: str | None = None,
    min_risques: Annotated[int, Query(ge=0, le=4)] = 0,
    limit: Annotated[int, Query(ge=1, le=58)] = 15,
) -> list[dict[str, object]]:
    """Le classement : le plus de familles de risque d'abord, puis le plus d'élèves."""
    vue = filtrer_communes(r["vue"], commune_connue(commune))
    vue = vue[vue["nb_familles"] >= min_risques].head(limit)
    colonnes = ["rang", "uai", "nom", "commune", "effectif_total", "effectif_prevu",
                "annee_prevue", "nb_familles", "familles_exposees", "diagnostics"]  # fmt: skip
    return json_propre(vue[colonnes])


@app.get("/colleges/recherche")
def rechercher(q: Annotated[str, Query(min_length=2)]) -> list[dict[str, object]]:
    """Trouve un collège par son nom ou sa commune, sans tenir compte des accents."""
    cible = sans_accents(q)
    trouves = COLLEGES[
        COLLEGES["nom"].map(sans_accents).str.contains(cible, regex=False)
        | COLLEGES["commune"].map(sans_accents).str.contains(cible, regex=False)
    ]
    return json_propre(trouves[["uai", "nom", "commune"]])


@app.get("/colleges/{uai}")
def fiche(uai: str, r: Reglages) -> dict[str, object]:
    """La fiche d'un collège : risques expliqués, diagnostics, effectifs, prévision, CatNat."""
    vue = r["vue"].set_index("uai")
    if uai not in vue.index:
        raise HTTPException(404, f"Collège inconnu : {uai}. Cherchez-le avec /colleges/recherche.")
    c = vue.loc[uai]
    explications = facteurs(c, r["seuil_seveso_km"], r["seuil_casias"])
    h = historique_college(HISTORIQUE, uai)
    cat = catnat_commune(CATNAT, c["code_insee"])
    err = ERREURS.set_index("horizon").loc[r["horizon"]]
    actives = [f for f in r["familles"] if c[f]]
    return {
        "uai": uai,
        "nom": c["nom"],
        "commune": c["commune"],
        "rang": int(c["rang"]),
        "sur": len(vue),
        "effectif_2025": int(c["effectif_total"]),
        "ips": float(c["ips"]),
        "nb_familles": int(c["nb_familles"]),
        "familles": {FAMILLES_COURT[f]: bool(c[f]) for f in r["familles"]},
        "pourquoi": {FAMILLES_COURT[f]: explications[f] for f in r["familles"]},
        "diagnostics_a_demander": [DIAGNOSTICS[f] for f in actives],
        "dicrim": None if pd.isna(c["annee_dicrim"]) else int(c["annee_dicrim"]),
        "effectifs": json_propre(h[["rentree", "effectif_total"]]),
        "prevision": {
            "annee": int(c["annee_prevue"]),
            "effectif_prevu": int(c["effectif_prevu"]),
            "erreur_moyenne_modele": round(float(err["mae_modele"]), 1),
            "erreur_moyenne_naive": round(float(err["mae_naif"]), 1),
        },
        "catnat_commune": {
            "total": int(cat["arretes"].sum()),
            "par_peril": cat.groupby("peril")["arretes"].sum().astype(int).to_dict(),
            "depuis": None if cat.empty else int(cat["annee"].min()),
        },
    }


@app.get("/communes/{commune}/catnat")
def catnat(commune: str) -> list[dict[str, object]]:
    """Les arrêtés de catastrophe naturelle d'une commune, par année et par péril."""
    nom = commune_connue(commune)[0]
    code = COLLEGES.loc[COLLEGES["commune"] == nom, "code_insee"].iloc[0]
    return json_propre(catnat_commune(CATNAT, code))
