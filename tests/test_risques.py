import pandas as pd

from preparer import preparer
from risques import (
    ORLEANS,
    ajouter_familles,
    catnat_commune,
    classer,
    compter_familles,
    distance_km,
    indicateurs,
)


def college(**kw):
    base = {
        "argiles_classe": "moyen", "nb_cavites_500m": 0, "nb_mouvements_terrain_500m": 0,
        "dans_ppri": False, "dans_zone_tmd_500m": False, "distance_seveso_km": 10.0,
        "effectif_total": 500,
    }  # fmt: skip
    return {**base, **kw}


def test_regles_des_familles():
    df = ajouter_familles(
        pd.DataFrame(
            [
                college(),
                college(argiles_classe="fort"),
                college(dans_ppri=True),
                college(distance_seveso_km=1.5),
            ]
        )
    )
    assert df[["sol", "inondation", "techno"]].sum(axis=1).tolist() == [0, 1, 1, 1]
    assert df.loc[1, "sol"] and df.loc[2, "inondation"] and df.loc[3, "techno"]


def test_classement_et_indicateurs_suivent_les_familles_cochees():
    df = ajouter_familles(
        pd.DataFrame(
            [
                college(argiles_classe="fort", dans_ppri=True, effectif_total=300),
                college(dans_ppri=True, effectif_total=800),
            ]
        )
    )
    toutes = classer(compter_familles(df, ["sol", "inondation", "techno"]))
    assert toutes["effectif_total"].tolist() == [300, 800]  # 2 risques avant 1 risque
    assert indicateurs(toutes)["eleves_cumul"] == 300
    sans_sol = compter_familles(df, ["inondation"])
    assert indicateurs(sans_sol)["colleges_cumul"] == 0


def test_preparation_garde_les_58_colleges_publics():
    df = preparer()
    assert len(df) == 58 and df["uai"].is_unique
    assert {"sol", "inondation", "techno", "evolution_pct"} <= set(df.columns)


def test_seuil_seveso_reglable():
    df = pd.DataFrame([college(distance_seveso_km=3.0)])
    assert not ajouter_familles(df).loc[0, "techno"]
    assert ajouter_familles(df, seuil_seveso_km=4.0).loc[0, "techno"]


def test_distance_orleans_a_orleans_est_nulle():
    d = distance_km(pd.Series([ORLEANS[0], 47.0]), pd.Series([ORLEANS[1], 1.9093]), ORLEANS)
    assert d.iloc[0] < 0.01
    assert 99 < d.iloc[1] < 101  # 0,9° de latitude ≈ 100 km


def test_catnat_commune_regroupe_les_perils():
    catnat = pd.DataFrame(
        {
            "code_insee": ["45001", "45001", "45001", "45002"],
            "peril": [
                "Inondations et/ou Coulées de Boue",
                "Inondations Remontée Nappe",
                "Sécheresse",
                "Sécheresse",
            ],
            "date_debut": pd.to_datetime(["2016-05-30", "2016-06-01", "2018-07-01", "2018-07-01"]),
        }
    )
    c = catnat_commune(catnat, "45001")
    assert c.set_index(["annee", "peril"])["arretes"].to_dict() == {
        (2016, "Inondation"): 2,
        (2018, "Sécheresse"): 1,
    }
    assert catnat_commune(catnat, "99999").empty
