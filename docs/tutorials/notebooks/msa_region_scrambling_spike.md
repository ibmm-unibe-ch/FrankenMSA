# MSA Study: regional scrambling in SARS-CoV-2 Spike RBM

This example tests region sensitivity by scrambling one biologically meaningful
window while keeping sequence lengths and global composition stable.

```python
import pandas as pd

from frankenmsa.align import MMSeqs2Colab
from frankenmsa.msa import MSA

# SARS-CoV-2 Spike (UniProt P0DTC2) query sequence (S ectodomain-length workflows are possible;
# this minimal example accepts any query you choose to start from).
spike_query = (
    "MFVFLVLLPLVSSQCVNLTTRTQLPPAYTNSFTRGVYYPDKVFRSSVLHSTQDLFLPFFSNVTWFHAIHVSGTNGT"
    "KRFDNPVLPFNDGVYFASTEKSNIIRGWIFGTTLDSKTQSLLIVNNATNVVIKVCEFQFCNDPFLGVYYHKNNKSW"
    "MESEFRVYSSANNCTFEYVSQPFLMDLEGKQGNFKNLREFVFKNIDGYFKIYSKHTPINLVRDLPQGFSALEPLVD"
    "LPIGINITRFQTLLALHRSYLTPGDSSSGWTAGAAAYYVGYLQPRTFLLKYNENGTITDAVDCALDPLSETKCTLK"
)

# 1) Build and clean MSA
mmseqs = MMSeqs2Colab(user_agent="frankenmsa-tutorials")
raw_df = mmseqs.align([spike_query], env=True, filter=True, pairing=None)
msa_ref = MSA(raw_df).drop_duplicates().filter_gaps(0.5)

# 2) Scramble RBM-like window (example boundaries; adjust to your sequence span)
rbm_start, rbm_end = 438, 506  # 0-based, end-exclusive in FrankenMSA shuffle_msa
msa_scrambled = msa_ref.copy().shuffle_msa(
    start=rbm_start,
    end=rbm_end,
    preserve_gaps=True,
    random_state=7,
)

# 3) Compare summary metrics
ref_conservation = msa_ref.conservation_scores()
scrambled_conservation = msa_scrambled.conservation_scores()

region = pd.DataFrame(
    {
        "position": range(len(ref_conservation)),
        "ref_conservation": ref_conservation.values,
        "scrambled_conservation": scrambled_conservation.values,
        "delta": (scrambled_conservation - ref_conservation).values,
    }
)

print(region.iloc[max(0, rbm_start - 10) : rbm_end + 10])

msa_ref.write_a3m("spike_reference.a3m")
msa_scrambled.write_a3m("spike_rbm_scrambled.a3m")
```

Recommended follow-up:

- run `query_identity_scores()` and inspect distribution shifts in the
  scrambled window
- compare clustering before/after scrambling
