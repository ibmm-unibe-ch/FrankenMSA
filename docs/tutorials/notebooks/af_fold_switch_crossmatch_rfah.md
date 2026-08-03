# AF-oriented Study: fold-state cross-matching with RfaH (2OUG vs 2LCL)

This example uses ProteinMPNN-generated sequence sets from two fold states,
then swaps one sequence region across sets to build AlphaFold test candidates.

```python
from pathlib import Path

from frankenmsa.msa import MSA
from frankenmsa.inverse_fold import run_proteinmpnn
from frankenmsa.inverse_fold.protein_mpnn_workflow import download_pdb_by_code

# 0) Download the two RfaH conformational-state structures
pdb_2oug = download_pdb_by_code("2OUG")  # state A
pdb_2lcl = download_pdb_by_code("2LCL")  # state B

# 1) Generate sequence sets with local ProteinMPNN
#    (requires an existing local ProteinMPNN installation)
state_a = run_proteinmpnn(
    pdb_path=pdb_2oug,
    allow_upload=True,
    runtime="local",
    num_seqs=64,
    sampling_temp=0.5,
    design_chains="A",
    fixed_chains="",
    homomer=False,
)

state_b = run_proteinmpnn(
    pdb_path=pdb_2lcl,
    allow_upload=True,
    runtime="local",
    num_seqs=64,
    sampling_temp=0.5,
    design_chains="A",
    fixed_chains="",
    homomer=False,
)

# 2) Load both sequence sets as MSAs
msa_a = MSA.from_a3m(state_a["a3m_path"])
msa_b = MSA.from_a3m(state_b["a3m_path"])

# 3) Swap a region from state A query into state B non-query rows
swap_start, swap_end = 95, 140
fragment = msa_a.query.df["sequence"].iloc[0][swap_start:swap_end]
msa_b_cross = msa_b.copy().replace_at(
    replacement=fragment,
    index=swap_start,
    include_query=False,
)

# 4) Export AF candidates (remove '-' before writing FASTA)
def write_query_fasta(msa_obj: MSA, header: str, out_path: str) -> None:
    seq = msa_obj.query.df["sequence"].iloc[0].replace("-", "")
    Path(out_path).write_text(f">{header}\n{seq}\n", encoding="utf-8")

write_query_fasta(msa_a, "RfaH_stateA_query", "rfah_stateA_query.fasta")
write_query_fasta(msa_b, "RfaH_stateB_query", "rfah_stateB_query.fasta")
write_query_fasta(msa_b_cross, "RfaH_stateB_crossmatched", "rfah_stateB_crossmatched.fasta")

# Optional saved alignments
msa_a.write_a3m("rfah_stateA.a3m")
msa_b.write_a3m("rfah_stateB.a3m")
msa_b_cross.write_a3m("rfah_stateB_crossmatched.a3m")
```

Recommended AlphaFold comparison:

- state-B query vs cross-matched query
- local confidence around swapped segment and neighboring contacts
