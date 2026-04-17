import pandas as pd
import numpy as np
from pathlib import Path
import pytest

PARENT = Path(__file__).parent
FILES = PARENT.parents[1] / "files"

TEST_PDB1 = FILES / "1E4Q.pdb"


def _repo_proteinmpnn_dir() -> Path:
    proteinmpnn_dir = Path(__file__).resolve().parents[3] / "ProteinMPNN"
    if not proteinmpnn_dir.exists():
        pytest.skip("ProteinMPNN directory not found")
    return proteinmpnn_dir


def test_protein_mpnn_generate():
    import os

    torch = pytest.importorskip("torch")

    if torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        device = "cuda:0"
    else:
        device = "cpu"

    from frankenmsa.inverse_fold import LocalProteinMPNN as ProteinMPNN

    proteinmpnn_dir = _repo_proteinmpnn_dir()

    generator = ProteinMPNN.from_directory(proteinmpnn_dir)
    generator.init()
    generator.model = generator.model.to(device)

    assert generator.model is not None
    assert generator._is_loaded
    assert generator.device is not None

    n = 10
    sequences, extra = generator.generate(str(TEST_PDB1), n)
    assert len(sequences) == n
    assert isinstance(sequences, pd.DataFrame)
    assert "sequence" in sequences.columns
    assert "recovery_rate" in sequences.columns
    assert "score" in sequences.columns


def test_protein_mpnn_from_os_environ():
    import os

    proteinmpnn_dir = _repo_proteinmpnn_dir()

    os.environ["FRANKENMSA_PROTEINMPNN_ROOT"] = str(proteinmpnn_dir)

    torch = pytest.importorskip("torch")

    if torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        device = "cuda:0"
    else:
        device = "cpu"

    from frankenmsa.inverse_fold import LocalProteinMPNN as ProteinMPNN

    generator = ProteinMPNN()
    generator.init()
    generator.model = generator.model.to(device)

    assert generator.model is not None
    assert generator._is_loaded
    assert generator.device is not None

    n = 10
    sequences, extra = generator.generate(str(TEST_PDB1), n)
    assert len(sequences) == n
    assert isinstance(sequences, pd.DataFrame)
    assert "sequence" in sequences.columns
    assert "recovery_rate" in sequences.columns
    assert "score" in sequences.columns


def test_functional_api():
    import os

    _ = pytest.importorskip("torch")
    proteinmpnn_dir = _repo_proteinmpnn_dir()

    os.environ["FRANKENMSA_PROTEINMPNN_ROOT"] = str(proteinmpnn_dir)

    import frankenmsa.inverse_fold as ff

    n = 3
    sequences, extra = ff.inverse_fold(str(TEST_PDB1), n)
    assert len(sequences) == n
    assert "sequence" in sequences.columns
    assert "recovery_rate" in sequences.columns
    assert "score" in sequences.columns


def test_biolib_proteinmpnn():
    from frankenmsa.inverse_fold import BiolibProteinMPNN as ProteinMPNN

    generator = ProteinMPNN()
    out, extra = generator.generate(
        str(TEST_PDB1),
        n=3,
        temperature=1.0,
    )
    assert len(out) == 3
    assert isinstance(out, pd.DataFrame)
    assert "sequence" in out.columns
