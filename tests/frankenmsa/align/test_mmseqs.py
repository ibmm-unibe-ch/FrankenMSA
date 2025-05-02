import pandas as pd
import numpy as np
from pathlib import Path

PARENT = Path(__file__).parent
FILES = PARENT.parents[1] / "files"

TEST_SEQ1 = (FILES / "test1.seq").read_text().strip()
TEST_SEQ2 = (FILES / "test2.seq").read_text().strip()


def test_mmseqs_colab():
    from frankenmsa.align import MMSeqs2Colab

    mmseqs = MMSeqs2Colab(user_agent="FrankenMSA/test")

    msa = mmseqs.align([TEST_SEQ1])
    assert isinstance(msa, pd.DataFrame)
    assert len(msa) > 1
    assert "sequence" in msa.columns
    assert "header" in msa.columns
