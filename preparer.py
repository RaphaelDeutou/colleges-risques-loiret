"""Préparation, à lancer une fois : uv run python preparer.py

Lit les Parquet du cas (data/colleges_risques.parquet, data/colleges.parquet,
data/risques_catnat.parquet), garde les 58 collèges publics (le Département possède les
publics) et écrit trois petits fichiers que l'appli lit seuls :
- data/colleges_priorite.parquet : un collège par ligne, familles de risque, évolution
- data/historique_publics.parquet : effectifs, IPS et brevet sur 10 rentrées
- data/catnat_colleges.parquet : arrêtés CatNat des communes qui ont un collège public
"""

import pandas as pd

from risques import (
    DATA,
    FICHIER_CATNAT,
    FICHIER_HISTORIQUE,
    FICHIER_PRIORITE,
    ajouter_familles,
    evolution_effectifs,
)

COLONNES = [
    "uai", "nom", "commune", "code_insee", "lat", "lon", "secteur_id",
    "effectif_total", "ips",
    "argiles_classe", "nb_cavites_500m", "nb_mouvements_terrain_500m",
    "dans_ppri", "ppri", "distance_repere_crue_km",
    "dans_zone_tmd_500m", "distance_tmd_m", "type_tmd_proche", "distance_seveso_km",
    "distance_centrale_km", "centrale_proche",
    "nb_catnat", "nb_catnat_inondations", "nb_catnat_secheresse",
    "nb_catnat_mouvement_terrain", "annee_dicrim",
]  # fmt: skip


def preparer() -> pd.DataFrame:
    colleges = pd.read_parquet(DATA / "colleges_risques.parquet")
    historique = pd.read_parquet(DATA / "colleges.parquet")

    publics = colleges.loc[colleges["statut"] == "public", COLONNES]
    df = ajouter_familles(publics).merge(
        evolution_effectifs(historique), on="uai", how="left", validate="1:1"
    )
    assert df["uai"].is_unique and len(df) == 58, len(df)
    return df.reset_index(drop=True)


def preparer_historique(uais: pd.Series) -> pd.DataFrame:
    h = pd.read_parquet(DATA / "colleges.parquet")
    cols = ["uai", "rentree", "effectif_total", "ips", "dnb_taux_reussite"]
    return h.loc[h["uai"].isin(uais), cols].reset_index(drop=True)


def preparer_catnat(codes_insee: pd.Series) -> pd.DataFrame:
    c = pd.read_parquet(DATA / "risques_catnat.parquet")
    cols = ["code_insee", "commune", "peril", "date_debut"]
    return c.loc[c["code_insee"].isin(codes_insee), cols].reset_index(drop=True)


if __name__ == "__main__":
    df = preparer()
    df.to_parquet(FICHIER_PRIORITE, index=False)
    preparer_historique(df["uai"]).to_parquet(FICHIER_HISTORIQUE, index=False)
    catnat = preparer_catnat(df["code_insee"])
    catnat.to_parquet(FICHIER_CATNAT, index=False)
    print(f"{len(df)} collèges publics, {len(catnat)} arrêtés CatNat")
    print(df[["sol", "inondation", "techno"]].sum().to_dict())
