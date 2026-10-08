import importlib
from pathlib import Path

import dash
import pytest


@pytest.fixture
def edit_page(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "app"))
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)
    monkeypatch.setattr(dash, "callback", lambda *args, **kwargs: lambda func: func)
    return importlib.import_module("pages.edit")


def test_overview_shows_consensus_and_first_sequence_separately(edit_page):
    msa_data = {
        "example": {
            "header": ["query", "hit1", "hit2"],
            "sequence": ["AC-D", "ATGD", "ATGD"],
        }
    }

    overview, consensus, query = edit_page.update_msa_overview("example", msa_data)

    assert consensus == "ATGD"
    assert query == "AC-D"
    assert overview == [
        {"column": "Number of sequences", "value": 3},
        {"column": "Max. sequence length", "value": 4},
        {"column": "Min. sequence length", "value": 4},
        {"column": "Avg. sequence length", "value": 4.0},
        {"column": "Number of gaps", "value": 1},
    ]


def test_overview_empty_msa_has_appropriate_sequence_messages(edit_page):
    result = edit_page.update_msa_overview(
        "empty", {"empty": {"header": [], "sequence": []}}
    )

    assert result == (
        dash.no_update,
        "No consensus sequence available.",
        "No query sequence available.",
    )


@pytest.mark.parametrize(
    ("main_msa", "msa_data"),
    [(None, {"example": {}}), ("example", None), ("example", {})],
)
def test_overview_missing_selection_preserves_all_outputs(
    edit_page, main_msa, msa_data
):
    assert edit_page.update_msa_overview(main_msa, msa_data) == (
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )


def test_overview_layout_labels_both_sequences(edit_page):
    def walk(component):
        yield component
        children = getattr(component, "children", None)
        if children is not None:
            for child in children if isinstance(children, list) else [children]:
                yield from walk(child)

    components = list(walk(edit_page.msa_overview_layout()))
    headings = [
        component.children
        for component in components
        if isinstance(component, dash.html.H5)
    ]
    assert "Consensus Sequence" in headings
    assert "Query Sequence" in headings
    paragraphs = {
        component.id: component.children
        for component in components
        if isinstance(component, dash.html.P) and hasattr(component, "id")
    }
    assert paragraphs["msa-consensus-seq"] == "No consensus sequence available."
    assert paragraphs["msa-query-seq"] == "No query sequence available."
