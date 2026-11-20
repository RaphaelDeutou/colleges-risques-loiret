"""L'appli s'ouvre sans erreur, et la fiche de chacun des 58 collèges aussi.

Un collège sans DICRIM (année manquante) faisait planter sa fiche : ce test les ouvre tous.
"""

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from risques import FICHIER_PRIORITE

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_la_page_s_ouvre_sans_erreur():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception


def test_toutes_les_fiches_s_ouvrent():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    for uai in pd.read_parquet(FICHIER_PRIORITE)["uai"]:
        at.selectbox(key="college").set_value(uai).run()
        assert not at.exception, uai
