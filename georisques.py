"""Récupération Géorisques (API publique de l'État, Licence Ouverte), appelée par preparer.py.

L'appli n'appelle jamais l'API : preparer.py enregistre le résultat dans
data/georisques_colleges.parquet, et ce fichier sert de cache.
Documentation : https://www.georisques.gouv.fr/doc-api

Pour chaque collège, au point du collège :
- les anciens sites industriels et de service (inventaire CASIAS) à moins de 500 m ;
- le rapport de risques à l'adresse : remontée de nappe, argiles (carte nationale),
  canalisations de matières dangereuses.
"""

import json
import time
import urllib.parse
import urllib.request

import pandas as pd

from risques import distance_km

API = "https://georisques.gouv.fr/api/v1/"
RAYON_CASIAS_M = 500


def appeler(chemin: str, **params) -> dict:
    """Un appel GET à l'API, avec trois essais en cas d'erreur réseau."""
    url = API + chemin + "?" + urllib.parse.urlencode(params)
    for essai in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as reponse:
                return json.load(reponse)
        except OSError:
            if essai == 2:
                raise
            time.sleep(2)
    return {}


def sites_casias(lat: float, lon: float) -> pd.DataFrame:
    """Anciens sites industriels à moins de RAYON_CASIAS_M, du plus proche au plus loin."""
    sites, page = [], 1
    while True:
        r = appeler("ssp", latlon=f"{lon},{lat}", rayon=RAYON_CASIAS_M, page=page, page_size=100)
        bloc = r.get("casias", {})
        sites += bloc.get("data", [])
        if page >= bloc.get("total_pages", 1):
            break
        page += 1
    if not sites:
        return pd.DataFrame(columns=["nom", "statut", "distance_km"])
    df = pd.DataFrame(
        {
            "nom": [s["nom_etablissement"] for s in sites],
            "statut": [s["statut"] for s in sites],
            "lon": [s["geom"]["coordinates"][0] for s in sites],
            "lat": [s["geom"]["coordinates"][1] for s in sites],
        }
    )
    df["distance_km"] = distance_km(df["lat"], df["lon"], (lat, lon))
    return df.sort_values("distance_km")


def rapport(lat: float, lon: float) -> dict:
    """Le rapport « risques près de chez moi » de Géorisques, à l'adresse du collège."""
    r = appeler("resultats_rapport_risque", latlon=f"{lon},{lat}")
    naturels = r.get("risquesNaturels", {})
    techno = r.get("risquesTechnologiques", {})
    return {
        "nappe_georisques": naturels.get("remonteeNappe", {}).get("libelleStatutAdresse"),
        "argiles_georisques": naturels.get("retraitGonflementArgile", {}).get(
            "libelleStatutAdresse"
        ),
        "canalisation_tmd": bool(techno.get("canalisationsMatieresDangereuses", {}).get("present")),
    }


def recuperer(colleges: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par collège : sites CASIAS proches et rapport de risques. Une minute environ."""
    lignes = []
    for c in colleges.itertuples():
        sites = sites_casias(c.lat, c.lon)
        proches = sites.head(3)
        lignes.append(
            {
                "uai": c.uai,
                "nb_casias_500m": len(sites),
                "casias_proches": " ; ".join(
                    f"{n} ({d * 1000:.0f} m)"
                    for n, d in zip(proches["nom"], proches["distance_km"], strict=True)
                ),
                **rapport(c.lat, c.lon),
            }
        )
        time.sleep(0.2)  # rester poli avec l'API publique
    return pd.DataFrame(lignes)
