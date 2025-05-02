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

    generator = ProteinMPNN()
    generator.init()
    generator.model = generator.model.to(device)

    assert generator.model is not None
    assert generator._is_loaded
    assert generator.device is not None

    n = 10
    sequences, extra = generator.generate(TEST_PDB1, n)
    assert len(sequences) == n
    assert all(isinstance(seq, str) for seq in sequences)
    assert len(extra["score"]) == n
    assert len(extra.keys()) == 5


def test_functional_api():

    import frankenmsa.inverse_fold as ff

    n = 3
    sequences, extra = ff.inverse_fold(TEST_PDB1, n)
    assert len(sequences) == n
    assert all(isinstance(seq, str) for seq in sequences)
    assert len(extra["score"]) == n
    assert len(extra.keys()) == 5
