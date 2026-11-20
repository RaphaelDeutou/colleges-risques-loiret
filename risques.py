"""Calculs du projet, sans affichage : les familles de risque et les indicateurs.

Quatre familles, chacune une règle simple qu'on peut expliquer à un élu :
- sol : argiles au niveau le plus haut de la carte choisie (GéoLoiret « fort » ou Géorisques
  « important »), ou cavité, ou mouvement de terrain à moins de 500 m
- inondation : dans un périmètre de PPRI (ce n'est pas la zone inondable), ou remontée de nappe
  « risque existant » selon Géorisques
- technologique : zone de sûreté TMD de 500 m, ou site Seveso à moins de 2 km (réglable)
- sols pollués : au moins 5 anciens sites industriels (CASIAS) à moins de 500 m (réglable) ;
  5 est le seuil du quart des collèges les plus entourés
Les rayons et seuils sont des choix du projet, pas des seuils officiels.
"""

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
FICHIER_PRIORITE = DATA / "colleges_priorite.parquet"
FICHIER_HISTORIQUE = DATA / "historique_publics.parquet"
FICHIER_CATNAT = DATA / "catnat_colleges.parquet"
FICHIER_GEORISQUES = DATA / "georisques_colleges.parquet"
FICHIER_PREVISIONS = DATA / "previsions.parquet"
FICHIER_ERREURS = DATA / "prevision_erreurs.parquet"

SEUIL_SEVESO_KM = 2.0
SEUIL_CASIAS = 5  # anciens sites industriels à moins de 500 m ; 3e quartile des 58 collèges
ANNEE_REF, ANNEE_FIN = 2020, 2025  # évolution des effectifs sur 5 rentrées

# Deux cartes des argiles, et la classe retenue comme « argiles fortes » dans chacune.
CARTES_ARGILES = {
    "geoloiret": ("argiles_classe", "fort"),
    "georisques": ("argiles_georisques", "Risque Existant - important"),
}
NAPPE_EXISTANTE = "Risque Existant"

FAMILLES = {
    "sol": "Sol (argiles fortes, cavités, mouvements)",
    "inondation": "Inondation (PPRI, remontée de nappe)",
    "techno": "Technologique (TMD, Seveso)",
    "pollution": "Sols pollués (anciens sites industriels)",
}
FAMILLES_COURT = {
    "sol": "Sol",
    "inondation": "Inondation",
    "techno": "Technologique",
    "pollution": "Sols pollués",
}
DIAGNOSTICS = {
    "sol": "étude géotechnique",
    "inondation": "diagnostic de vulnérabilité inondation",
    "techno": "revue du plan de mise en sûreté (confinement)",
    "pollution": "diagnostic de la qualité des sols et de l'air intérieur",
}
PERILS = {  # libellés GASPAR -> trois périls lisibles
    "Sécheresse": "Sécheresse",
    "Inondations et/ou Coulées de Boue": "Inondation",
    "Inondations Remontée Nappe": "Inondation",
    "Mouvement de Terrain": "Mouvement de terrain",
    "Effondrement et/ou Affaisement": "Mouvement de terrain",
}


def ajouter_familles(
    df: pd.DataFrame,
    seuil_seveso_km: float = SEUIL_SEVESO_KM,
    carte_argiles: str = "geoloiret",
    seuil_casias: int = SEUIL_CASIAS,
) -> pd.DataFrame:
    """Ajoute une colonne booléenne par famille de risque."""
    colonne, classe_forte = CARTES_ARGILES[carte_argiles]
    return df.assign(
        sol=df[colonne].eq(classe_forte).fillna(False)
        | df["nb_cavites_500m"].gt(0)
        | df["nb_mouvements_terrain_500m"].gt(0),
        inondation=df["dans_ppri"].astype(bool)
        | df["nappe_georisques"].eq(NAPPE_EXISTANTE).fillna(False),
        techno=df["dans_zone_tmd_500m"].astype(bool) | df["distance_seveso_km"].lt(seuil_seveso_km),
        pollution=df["nb_casias_500m"].ge(seuil_casias),
    )


def evolution_effectifs(historique: pd.DataFrame) -> pd.DataFrame:
    """Effectif en ANNEE_REF et variation en % jusqu'à ANNEE_FIN, un collège par ligne."""
    pivot = historique.pivot_table(
        index="uai", columns="rentree", values="effectif_total", aggfunc="sum"
    )
    debut, fin = pivot[ANNEE_REF], pivot[ANNEE_FIN]
    return pd.DataFrame(
        {
            "effectif_ref": debut.astype("Int64"),
            "evolution_pct": ((fin - debut) / debut * 100).round(1),
        }
    ).reset_index()


def compter_familles(df: pd.DataFrame, familles: list[str]) -> pd.DataFrame:
    """Nombre de familles retenues auxquelles chaque collège est exposé, et leurs libellés."""
    retenues = [f for f in FAMILLES if f in familles]
    nb = df[retenues].sum(axis=1).astype(int) if retenues else pd.Series(0, index=df.index)

    def libelle(ligne: pd.Series) -> str:
        return " + ".join(FAMILLES_COURT[f].lower() for f in retenues if ligne[f]) or "aucune"

    def diagnostic(ligne: pd.Series) -> str:
        return " ; ".join(DIAGNOSTICS[f] for f in retenues if ligne[f]) or "aucun"

    return df.assign(
        nb_familles=nb,
        familles_exposees=df.apply(libelle, axis=1),
        diagnostics=df.apply(diagnostic, axis=1),
    )


def ajouter_prevision(df: pd.DataFrame, previsions: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Ajoute l'effectif prévu à l'horizon choisi (colonnes effectif_prevu, annee_prevue)."""
    p = previsions.loc[previsions["horizon"] == horizon, ["uai", "effectif_prevu", "annee"]]
    return df.merge(p.rename(columns={"annee": "annee_prevue"}), on="uai", how="left")


def filtrer_communes(df: pd.DataFrame, communes: list[str]) -> pd.DataFrame:
    """Garde les collèges des communes choisies ; aucune commune choisie = toutes."""
    return df[df["commune"].isin(communes)] if communes else df


def classer(df: pd.DataFrame, eleves: str = "effectif_total") -> pd.DataFrame:
    """Le plus de familles d'abord, puis le plus d'élèves ; ajoute le rang.

    `eleves` : « effectif_total » (rentrée 2025) ou « effectif_prevu » (prévision du modèle).
    """
    trie = df.sort_values(["nb_familles", eleves], ascending=[False, False])
    return trie.assign(rang=range(1, len(trie) + 1))


def indicateurs(df: pd.DataFrame) -> dict[str, int]:
    """Les chiffres du haut de page, sur la vue filtrée."""
    cumul = df[df["nb_familles"] >= 2]
    return {
        "colleges": len(df),
        "colleges_cumul": len(cumul),
        "eleves_cumul": int(cumul["effectif_total"].sum()),
        "colleges_expose": int((df["nb_familles"] >= 1).sum()),
        "eleves_expose": int(df.loc[df["nb_familles"] >= 1, "effectif_total"].sum()),
        "eleves_cumul_prevu": (
            int(cumul["effectif_prevu"].sum()) if "effectif_prevu" in df else None
        ),
    }


ORLEANS = (47.9029, 1.9093)


def km(x: float) -> str:
    """Une distance en km à la française : « 1,4 km », ou « moins de 50 m »."""
    return "moins de 50 m" if x < 0.05 else f"{x:.1f} km".replace(".", ",")


def distance_km(lat: pd.Series, lon: pd.Series, origine: tuple[float, float]) -> pd.Series:
    """Distance à vol d'oiseau (formule de haversine), en km."""
    lat0, lon0 = np.radians(origine[0]), np.radians(origine[1])
    la, lo = np.radians(lat), np.radians(lon)
    a = np.sin((la - lat0) / 2) ** 2 + np.cos(lat0) * np.cos(la) * np.sin((lo - lon0) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def statut_court(statut: object) -> str:
    """« Risque Existant - important » -> « existant, important » ; vide -> « non renseigné »."""
    if not isinstance(statut, str) or not statut:
        return "non renseigné"
    return statut.removeprefix("Risque ").replace(" - ", ", ").lower()


def facteurs(
    ligne: pd.Series,
    seuil_seveso_km: float = SEUIL_SEVESO_KM,
    seuil_casias: int = SEUIL_CASIAS,
) -> dict[str, str]:
    """Pour la fiche : ce qui explique chaque famille, en une phrase avec les chiffres sources."""
    sol = (
        f"Argiles : aléa {ligne['argiles_classe']} selon GéoLoiret, "
        f"{statut_court(ligne['argiles_georisques'])} selon Géorisques · "
        f"{ligne['nb_cavites_500m']} cavité(s) et {ligne['nb_mouvements_terrain_500m']} "
        "mouvement(s) de terrain à moins de 500 m"
    )
    if ligne["dans_ppri"]:
        inondation = f"Dans le périmètre du {ligne['ppri']}"
    else:
        inondation = "Hors périmètre de PPRI"
    inondation += (
        f" · remontée de nappe : {statut_court(ligne['nappe_georisques'])}"
        f" · repère de crue le plus proche à {km(ligne['distance_repere_crue_km'])}"
    )
    n = int(ligne["nb_casias_500m"])
    pollution = (
        f"{n} ancien(s) site(s) industriel(s) à moins de 500 m (seuil retenu : {seuil_casias})"
    )
    if n:
        pollution += f" · les plus proches : {ligne['casias_proches']}"
    zone = "dans la zone de 500 m" if ligne["dans_zone_tmd_500m"] else "hors zone de 500 m"
    techno = (
        f"Axe TMD ({str(ligne['type_tmd_proche']).lower()}) à {ligne['distance_tmd_m']} m, "
        f"{zone} · site Seveso à {km(ligne['distance_seveso_km'])} "
        f"(seuil retenu : {km(seuil_seveso_km)})"
    )
    return {"sol": sol, "inondation": inondation, "techno": techno, "pollution": pollution}


def historique_college(historique: pd.DataFrame, uai: str) -> pd.DataFrame:
    """Les rentrées connues d'un collège, dans l'ordre."""
    h = historique[historique["uai"] == uai].sort_values("rentree")
    return h.dropna(subset=["effectif_total"])


def catnat_commune(catnat: pd.DataFrame, code_insee: str) -> pd.DataFrame:
    """Arrêtés CatNat d'une commune, comptés par année et par péril simplifié."""
    c = catnat[catnat["code_insee"] == code_insee]
    if c.empty:
        return pd.DataFrame(columns=["annee", "peril", "arretes"])
    return (
        c.assign(annee=c["date_debut"].dt.year, peril=c["peril"].map(PERILS).fillna("Autre"))
        .groupby(["annee", "peril"], as_index=False)
        .size()
        .rename(columns={"size": "arretes"})
    )


def charger_priorite() -> pd.DataFrame:
    """Le Parquet préparé par preparer.py : un collège public par ligne."""
    return pd.read_parquet(FICHIER_PRIORITE)


def charger_historique() -> pd.DataFrame:
    return pd.read_parquet(FICHIER_HISTORIQUE)


def charger_catnat() -> pd.DataFrame:
    return pd.read_parquet(FICHIER_CATNAT)


def charger_previsions() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Les prévisions d'effectifs (un collège × un horizon) et le tableau des erreurs."""
    return pd.read_parquet(FICHIER_PREVISIONS), pd.read_parquet(FICHIER_ERREURS)
