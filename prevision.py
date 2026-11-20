"""Couche ML : prévoir l'effectif de chaque collège dans 1 à 5 ans.

Pourquoi : des travaux votés aujourd'hui sont livrés dans 2 ou 3 ans. Ce qui compte pour la
décision, c'est le nombre d'élèves qui seront dans le collège exposé.

Le modèle (un par horizon h) :
- un exemple = un collège à la rentrée t ; la cible = la variation relative de son effectif
  entre t et t + h (on prédit +4 %, pas 700 élèves : les petits et grands collèges se comparent) ;
- les variables, toutes connues à la rentrée t :
  parts de 6e, 5e et 4e dans l'effectif (une grosse promotion de 6e restera 3 ans encore),
  IPS, taille du collège ;
- une régression Ridge (linéaire, régularisée) : peu d'exemples, il faut un modèle simple.

L'évaluation (backtest) : on cache la dernière rentrée connue (2025), on entraîne sur les
exemples dont la cible est antérieure, on prédit 2025 et on mesure l'erreur absolue moyenne
(MAE, en élèves). On la compare à la méthode naïve « l'effectif ne bouge pas ».
Le modèle de prévision final est ensuite réentraîné sur toutes les années.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HORIZONS = range(1, 6)  # de 1 à 5 ans
VARIABLES = ["part_6e", "part_5e", "part_4e", "ips", "log_effectif"]


def variables(historique: pd.DataFrame) -> pd.DataFrame:
    """Les variables du modèle, une ligne par collège et par rentrée connue."""
    h = historique.dropna(subset=["effectif_total", "effectif_6e", "ips"]).copy()
    total = h["effectif_total"].astype(float)
    for niveau in ("6e", "5e", "4e"):
        h[f"part_{niveau}"] = h[f"effectif_{niveau}"] / total
    h["log_effectif"] = np.log(total)
    return h[["uai", "rentree", "effectif_total", *VARIABLES]]


def exemples(var: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Couples (rentrée t, rentrée t + horizon) d'un même collège, avec la variation."""
    futur = var[["uai", "rentree", "effectif_total"]].rename(
        columns={"effectif_total": "effectif_futur"}
    )
    futur["rentree"] -= horizon
    ex = var.merge(futur, on=["uai", "rentree"])
    ex["variation"] = ex["effectif_futur"] / ex["effectif_total"] - 1
    ex["annee_cible"] = ex["rentree"] + horizon
    return ex


def modele() -> object:
    return make_pipeline(StandardScaler(), Ridge(alpha=10.0))


def evaluer(var: pd.DataFrame, horizon: int) -> dict:
    """Backtest : entraîne sur les cibles avant la dernière année, teste sur la dernière."""
    ex = exemples(var, horizon)
    derniere = ex["annee_cible"].max()
    train, test = ex[ex["annee_cible"] < derniere], ex[ex["annee_cible"] == derniere]
    if train.empty or test.empty:
        return {"horizon": horizon, "mae_modele": np.nan, "mae_naif": np.nan,
                "n_train": len(train), "n_test": len(test)}  # fmt: skip
    m = modele().fit(train[VARIABLES], train["variation"])
    prevu = test["effectif_total"] * (1 + m.predict(test[VARIABLES]))
    return {
        "horizon": horizon,
        "mae_modele": float((prevu - test["effectif_futur"]).abs().mean()),
        "mae_naif": float((test["effectif_total"] - test["effectif_futur"]).abs().mean()),
        "n_train": len(train),
        "n_test": len(test),
        "annees_train": f"{int(train['annee_cible'].min())}-{int(train['annee_cible'].max())}",
    }


def prevoir(var: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Prévision depuis la dernière rentrée, avec un modèle entraîné sur toutes les années."""
    ex = exemples(var, horizon)
    m = modele().fit(ex[VARIABLES], ex["variation"])
    derniere = var[var["rentree"] == var["rentree"].max()]
    prevu = derniere["effectif_total"] * (1 + m.predict(derniere[VARIABLES]))
    return pd.DataFrame(
        {
            "uai": derniere["uai"].to_numpy(),
            "horizon": horizon,
            "annee": int(derniere["rentree"].max()) + horizon,
            "effectif_prevu": prevu.round().astype(int).to_numpy(),
        }
    )


def calculer(historique: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Toutes les prévisions (un collège × un horizon) et le tableau des erreurs."""
    var = variables(historique)
    previsions = pd.concat([prevoir(var, h) for h in HORIZONS], ignore_index=True)
    erreurs = pd.DataFrame([evaluer(var, h) for h in HORIZONS])
    return previsions, erreurs
