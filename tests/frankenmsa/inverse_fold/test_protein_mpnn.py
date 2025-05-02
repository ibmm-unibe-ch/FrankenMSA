import pandas as pd
import numpy as np
from pathlib import Path

PARENT = Path(__file__).parent
FILES = PARENT.parents[1] / "files"

TEST_PDB1 = FILES / "1E4Q.pdb"


def test_protein_mpnn_generate():
    import os
    import torch

    if torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        device = "cuda:0"
    else:
        device = "cpu"

    from frankenmsa.inverse_fold import ProteinMPNN

    proteinmpnn_dir = PARENT.parents[3] / "ProteinMPNN"
    assert proteinmpnn_dir.exists(), "ProteinMPNN directory not found"

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

    proteinmpnn_dir = PARENT.parents[3] / "ProteinMPNN"
    assert proteinmpnn_dir.exists(), "ProteinMPNN directory not found"

    os.environ["ProteinMPNN_DIR"] = str(proteinmpnn_dir)

    import torch

    if torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        device = "cuda:0"
    else:
        device = "cpu"

    from frankenmsa.inverse_fold import ProteinMPNN

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

    proteinmpnn_dir = PARENT.parents[3] / "ProteinMPNN"
    assert proteinmpnn_dir.exists(), "ProteinMPNN directory not found"

    os.environ["ProteinMPNN_DIR"] = str(proteinmpnn_dir)

    import frankenmsa.inverse_fold as ff

    n = 3
    sequences, extra = ff.inverse_fold(str(TEST_PDB1), n)
    assert len(sequences) == n
    assert "sequence" in sequences.columns
    assert "recovery_rate" in sequences.columns
    assert "score" in sequences.columns
