# MSA Study: regional scrambling and functional site identification in SARS-CoV-2 Spike

The goal here is not simply to observe post-scramble conservation noise, but to
use scrambling as a **control** in combination with AF structure prediction.

The idea: scramble the Receptor Binding Motif (RBM) — the primary ACE2-contact
region — then feed both the WT MSA and the scrambled MSA to AlphaFold. Structure
confidence (pLDDT) and predicted interface RMSD give a quantitative readout of
how much that region's evolutionary signal contributes to predicted fold quality
and interface geometry. No a priori knowledge of the answer is required: if pLDDT
drops and/or the ACE2-contact loop geometry diverges, the MSA signal for that
window was structurally informative. If it doesn't, the region is likely encoded
more locally.

```python
from pathlib import Path

import pandas as pd

from frankenmsa.align import MMSeqs2Colab
from frankenmsa.msa import MSA

# SARS-CoV-2 Spike RBD (UniProt P0DTC2), residues covering RBD+RBM
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

# 2) Produce two scrambled variants of the RBM window.
#    Position 438-506 (0-based) covers the primary ACE2-contact surface.
#    Use different random seeds so you have three distinct AF inputs.
rbm_start, rbm_end = 438, 506

msa_scrambled_1 = msa_ref.copy().shuffle_msa(
    start=rbm_start, end=rbm_end, preserve_gaps=True, random_state=7
)
msa_scrambled_2 = msa_ref.copy().shuffle_msa(
    start=rbm_start, end=rbm_end, preserve_gaps=True, random_state=42
)

# 3) Export MSAs for AlphaFold input
msa_ref.write_a3m("spike_reference.a3m")
msa_scrambled_1.write_a3m("spike_rbm_scrambled_s7.a3m")
msa_scrambled_2.write_a3m("spike_rbm_scrambled_s42.a3m")

# 4) Export the corresponding query sequences as FASTA (sequence is unchanged;
#    only the alignment context behind each position differs).
def query_to_fasta(msa: MSA, name: str, out_path: str) -> None:
    seq = msa.query.df["sequence"].iloc[0].replace("-", "")
    Path(out_path).write_text(f">{name}\n{seq}\n", encoding="utf-8")

query_to_fasta(msa_ref, "Spike_WT_context", "spike_query_ref.fasta")
query_to_fasta(msa_scrambled_1, "Spike_RBM_scrambled_s7", "spike_query_scrambled_s7.fasta")
query_to_fasta(msa_scrambled_2, "Spike_RBM_scrambled_s42", "spike_query_scrambled_s42.fasta")
```

## Downstream AlphaFold comparison

Run AlphaFold (or ColabFold with MSA injection) once with the reference A3M
and once for each scrambled A3M:

1. **pLDDT at RBM positions**: a drop in the scrambled runs indicates that
   coevolutionary signal in the RBM window is contributing to local fold
   confidence at those residues.
2. **Predicted interface geometry** (with ACE2, PDB 6M0J chain B as a template):
   if scrambling disrupts the contact loop geometry, the region carries
   productive MSA signal for interface prediction. If geometry is unchanged,
   the structure is locally rigid regardless of MSA depth at that site.
3. **Two scrambled seeds** act as a control for randomness: consistent effects
   across both scrambles are more likely to reflect MSA signal loss rather than
   a specific residue rearrangement artefact.
