# AF-oriented Study: GFP insertion into CHRM3 loop region

This example creates a GFP-inserted sequence cohort from an MSA and exports
FASTA sequences for downstream AlphaFold comparison.

```python
from pathlib import Path

import pandas as pd

from frankenmsa.align import MMSeqs2Colab
from frankenmsa.msa import MSA

# Human CHRM3 (UniProt P20309) query sequence
chrm3_query = (
    "MNTSVPPAVSPNATSSPSESKQLQATANMGNSSYQGAPAPAPRTTASLQTPAAGSPESVYQQLVQHLSVANRNL"
    "LQTPGTPGSSRSPQPPGGVYVTMVVGNLAAADLILACGLWVSLAIISQPVQYNLVYLVIGRLRRWRRRR"
)

# EGFP amino-acid sequence (canonical lab variant)
egfp = (
    "MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTFSYGVQCFSRYPDHMKQHD"
    "FFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLVNRIELKGIDFKEDGNILGHKLEYNYNSHNVYIMADKQKNGIKVN"
    "FKIRHNIEDGSVQLADHYQQNTPIGDGPVLLPDNHYLSTQSALSKDPNEKRDHMVLLEFVTAAGITHGMDELYK"
)

# 1) Build starting MSA
mmseqs = MMSeqs2Colab(user_agent="frankenmsa-tutorials")
raw_df = mmseqs.align([chrm3_query], env=True, filter=True, pairing=None)
msa = MSA(raw_df).drop_duplicates().filter_gaps(0.5)

# 2) Insert linker+GFP+linker at an example ICL3-like insertion site.
#    This index is tutorial-specific; use a structure-aligned loop position in real projects.
insert_index = 180
linker = "GGGGS"
insert_payload = linker + egfp + linker

msa_inserted = msa.copy().insert_at(insert_payload, index=insert_index, include_query=True)

# 3) Export WT and inserted query sequences as FASTA for AlphaFold
def query_to_fasta(msa_obj: MSA, header: str, out_path: str) -> None:
    seq = msa_obj.query.df["sequence"].iloc[0].replace("-", "")
    Path(out_path).write_text(f">{header}\n{seq}\n", encoding="utf-8")

query_to_fasta(msa, "CHRM3_wt_query", "chrm3_wt.fasta")
query_to_fasta(msa_inserted, "CHRM3_GFP_insert_query", "chrm3_gfp_insert.fasta")

# Optional: keep alignment artifacts for inspection
msa.write_a3m("chrm3_reference.a3m")
msa_inserted.write_a3m("chrm3_gfp_insert.a3m")
```

Recommended AlphaFold comparison:

- WT vs GFP-inserted pLDDT and domain packing
- local confidence around insertion boundaries (linker junctions)
