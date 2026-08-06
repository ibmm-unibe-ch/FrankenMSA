import json
from pathlib import Path

from frankenmsa.inverse_fold.protein_mpnn_workflow import merge_outputs_to_fasta
from frankenmsa.inverse_fold.protein_mpnn_workflow import split_chain_list
from frankenmsa.inverse_fold.protein_mpnn_workflow import split_fasta_by_chain_separator
from frankenmsa.inverse_fold.protein_mpnn_workflow import write_chain_jsonl
from frankenmsa.inverse_fold.protein_mpnn_workflow import zip_outputs


def test_split_chain_list_normalizes_csv_values():
    assert split_chain_list("a, b;C,invalid,AA") == ["A", "B", "C"]


def test_write_chain_jsonl_writes_expected_payload(tmp_path):
    pdb_path = tmp_path / "input.pdb"
    pdb_path.write_text("ATOM\n")

    jsonl_path = write_chain_jsonl(tmp_path, pdb_path, ["A"], ["B"])

    payload = json.loads(Path(jsonl_path).read_text().strip())
    assert payload == {
        "name": "input",
        "design_chain_list": ["A"],
        "fixed_chain_list": ["B"],
    }


def test_merge_outputs_to_fasta_relabels_fragments(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (tmp_path / "a.fa").write_text(">first\nAAAA\n")
    (nested / "b.fasta").write_text(">second\nBBBB\n")

    merged_path, count = merge_outputs_to_fasta(tmp_path, "demo")

    assert count == 2
    assert Path(merged_path).read_text() == ">sample_1\nAAAA\n>sample_2\nBBBB\n"


def test_merge_outputs_to_fasta_ignores_existing_output_file(tmp_path):
    (tmp_path / "existing.fa").write_text(">old\nCCCC\n")
    (tmp_path / "demo_proteinmpnn.fasta").write_text(">already_here\nDDDD\n")

    merged_path, count = merge_outputs_to_fasta(tmp_path, "demo")

    assert count == 1
    assert Path(merged_path).read_text() == ">sample_1\nCCCC\n"


def test_merge_outputs_to_fasta_uses_only_matching_stem(tmp_path):
    (tmp_path / "2LCL.fa").write_text(">design_1\nAAAA\n")
    (tmp_path / "2OUG.fa").write_text(">design_1\nCCCC\n")

    merged_path, count = merge_outputs_to_fasta(tmp_path, "2LCL")

    assert count == 1
    assert Path(merged_path).read_text() == ">sample_1\nAAAA\n"


def test_split_fasta_by_chain_separator_builds_per_chain_a3m(tmp_path):
    fasta_path = tmp_path / "combined.fasta"
    fasta_path.write_text(">sample_1\nAAAA/BBBB\n>sample_2\nCCCC/DDDD\n")

    split = split_fasta_by_chain_separator(
        full_fasta_path=fasta_path,
        out_dir=tmp_path,
        base_name="demo",
        chain_labels=["X", "Y"],
    )

    assert sorted(split) == ["demo_chainX", "demo_chainY"]
    assert split["demo_chainX"] == ">sample_1\nAAAA\n>sample_2\nCCCC\n"
    assert split["demo_chainY"] == ">sample_1\nBBBB\n>sample_2\nDDDD\n"


def test_zip_outputs_only_includes_relevant_artifacts(tmp_path):
    (tmp_path / "keep.fasta").write_text(">x\nAAAA\n")
    (tmp_path / "keep.a3m").write_text(">x\nAAAA\n")
    (tmp_path / "skip.txt").write_text("ignore me")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "keep.pdb").write_text("ATOM\n")

    zip_path = zip_outputs(tmp_path, "demo")

    assert Path(zip_path).exists()
    assert "keep.fasta" in zipfile.namelist(zip_path)
    assert "keep.a3m" in zipfile.namelist(zip_path)
    assert "nested/keep.pdb" in zipfile.namelist(zip_path)
    assert "skip.txt" not in zipfile.namelist(zip_path)
