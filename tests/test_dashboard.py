"""Tableau de bord : chaque page s'exécute sans erreur, avec et sans filtres, sans le CSV brut."""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app.py")
PAGES = ["demo/views/overview.py", "demo/views/temporal.py", "demo/views/distributions.py",
         "demo/views/comparisons.py", "demo/views/correlations.py", "demo/views/method.py"]


def run(at):
    at.run(timeout=120)
    assert not at.exception, at.exception
    return at


def page(path):
    at = run(AppTest.from_file(APP, default_timeout=120))
    at.switch_page(path)
    return run(at)


@pytest.mark.parametrize("path", PAGES)
def test_pages(path):
    at = page(path)
    assert any("kgrid" in m.value for m in at.markdown)


@pytest.mark.parametrize("path", PAGES[:4])
def test_pages_with_filters(path):
    at = page(path)
    at.multiselect(key="flt_day").set_value(["J2"])
    at.multiselect(key="flt_band").set_value(["0-1", "1-10"])
    run(at)
    assert any("Filtres actifs" in m.value for m in at.markdown)
    assert any("≈" in m.value for m in at.markdown) or path.endswith(("temporal.py", "comparisons.py"))
