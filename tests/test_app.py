"""Checagem mínima do dashboard: cada página roda sem erro, e os números-chave da Tela 1 aparecem.

Uso:  python -m pytest tests/
"""
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))  # as páginas importam app/dados.py


@pytest.mark.parametrize("pagina", ["tela1.py", "tela2.py", "sobre.py"])
def test_pagina_roda(pagina):
    at = AppTest.from_file(str(APP / pagina), default_timeout=60).run()
    assert not at.exception, at.exception


def test_tela1_nivel_e_original():
    at = AppTest.from_file(str(APP / "tela1.py"), default_timeout=60).run()
    assert at.metric[0].value == "136.378"        # 5,3 m, dados corrigidos
    at.toggle(key="original").set_value(True).run()
    assert at.metric[0].value == "138.414"        # 5,3 m, dados originais do INCT
    at.select_slider(key="nivel_t1").set_value(10.0).run()
    assert at.metric[0].value == "274.993"        # 10 m, original
    assert at.metric[2].value == "54 de 94"


def test_nivel_pela_url():
    at = AppTest.from_file(str(APP / "tela1.py"), default_timeout=60)
    at.query_params["nivel"] = "6,5"              # link compartilhado: ?nivel=6,5
    at.run()
    assert at.metric[0].value == "177.762"
