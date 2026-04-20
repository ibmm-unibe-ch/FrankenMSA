import pandas as pd
import pytest

from frankenmsa.augment.workflows import attach_ghostfold_result
from frankenmsa.augment.workflows import build_ghostfold_result_key
from frankenmsa.augment.workflows import normalize_ghostfold_input
from frankenmsa.augment.workflows import run_ghostfold_augmentation


def test_normalize_ghostfold_input_uppercases_and_skips_header():
    result = normalize_ghostfold_input(">query\n acde \n fg\n")

    assert result == "ACDEFG"


def test_normalize_ghostfold_input_rejects_multiple_records():
    with pytest.raises(ValueError, match="one FASTA record"):
        normalize_ghostfold_input(">q1\nAAAA\n>q2\nBBBB\n")


def test_normalize_ghostfold_input_rejects_multimers():
    with pytest.raises(ValueError, match="monomer"):
        normalize_ghostfold_input("AAAA:BBBB")


def test_build_ghostfold_result_key_counts_existing_results():
    msa_data = {"ghostfold_aug_1": {}, "ghostfold_aug_2": {}, "other": {}}

    assert build_ghostfold_result_key(msa_data) == "ghostfold_aug_3"


def test_attach_ghostfold_result_initializes_store():
    result_df = pd.DataFrame({"header": ["query"], "sequence": ["ACDE"]})

    msa_data, main_key, created_keys = attach_ghostfold_result(None, result_df)

    assert main_key == "ghostfold_aug_1"
    assert created_keys == ["ghostfold_aug_1"]
    assert msa_data["ghostfold_aug_1"]["sequence"] == ["ACDE"]


def test_run_ghostfold_augmentation_uses_backend_and_attaches(monkeypatch):
    result_df = pd.DataFrame({"header": ["query", "hit1"], "sequence": ["ACDE", "AFDE"]})

    monkeypatch.setattr(
        "frankenmsa.augment.workflows.GhostFold.augment",
        lambda self, sequence: result_df,
    )

    msa_data, main_key, created_keys, output_df = run_ghostfold_augmentation(
        ">query\nacde\n",
        {},
    )

    assert main_key == "ghostfold_aug_1"
    assert created_keys == ["ghostfold_aug_1"]
    assert msa_data[main_key]["header"] == ["query", "hit1"]
    assert output_df.equals(result_df)