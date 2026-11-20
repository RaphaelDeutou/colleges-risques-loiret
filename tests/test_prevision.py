import pandas as pd

import prevision


def historique_fictif():
    """Deux collèges sur 7 rentrées : l'un grandit de 10 élèves par an, l'autre est stable."""
    lignes = []
    for uai, depart, pente in (("A", 400, 10), ("B", 600, 0)):
        for i, annee in enumerate(range(2019, 2026)):
            total = depart + pente * i
            lignes.append(
                {"uai": uai, "rentree": annee, "effectif_total": total, "ips": 100.0,
                 "effectif_6e": total // 4, "effectif_5e": total // 4, "effectif_4e": total // 4}
            )  # fmt: skip
    return pd.DataFrame(lignes)


def test_exemples_aligne_la_rentree_et_la_cible():
    ex = prevision.exemples(prevision.variables(historique_fictif()), horizon=3)
    a2019 = ex[(ex["uai"] == "A") & (ex["rentree"] == 2019)].iloc[0]
    assert a2019["annee_cible"] == 2022
    assert a2019["effectif_futur"] == 430  # 400 + 3 × 10
    assert ex["annee_cible"].max() == 2025  # pas d'exemple au-delà des données connues


def test_un_modele_par_horizon_et_des_previsions_depuis_2025():
    previsions, erreurs = prevision.calculer(historique_fictif())
    assert sorted(erreurs["horizon"]) == [1, 2, 3, 4, 5]
    assert (previsions.groupby("horizon")["annee"].first() == [2026, 2027, 2028, 2029, 2030]).all()
    assert len(previsions) == 2 * 5  # deux collèges × cinq horizons
    assert erreurs["mae_naif"].notna().all() and erreurs["mae_modele"].notna().all()
