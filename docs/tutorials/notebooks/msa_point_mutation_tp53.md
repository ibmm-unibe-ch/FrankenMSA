# MSA Study: TP53 hotspot mutation context (R248Q)

This example is an MSA-first workflow: build a TP53 alignment with MMseqs2,
apply a hotspot mutation at one position, and compare conservation/identity
signals before and after perturbation.

```python
import pandas as pd

from frankenmsa.align import MMSeqs2Colab
from frankenmsa.msa import MSA

# Human TP53 (UniProt P04637), DNA-binding domain segment around codon 248
tp53_query = (
    "SQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPPVAPAPAAPTPAAPAP"
    "SWPLSSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIY"
    "KQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYM"
    "CNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELPPGSTKRALPTST"
)

# 1) Build MSA from MMseqs2 (network call)
mmseqs = MMSeqs2Colab(user_agent="frankenmsa-tutorials")
raw_df = mmseqs.align([tp53_query], env=True, filter=True, pairing=None)
msa_wt = MSA(raw_df).drop_duplicates().filter_gaps(0.4)

# 2) Generate a mutant cohort by setting residue 248 to Q.
#    Use 0-based indexing in FrankenMSA.
mut_index = 247
msa_mut = msa_wt.copy().replace_at("Q", index=mut_index, include_query=True).fix_at([mut_index])

# 3) Compare alignment-level summaries
wt_cons = msa_wt.conservation_scores()
mut_cons = msa_mut.conservation_scores()
delta_cons = mut_cons - wt_cons

wt_identity = msa_wt.query_identity_scores()
mut_identity = msa_mut.query_identity_scores()

summary = pd.DataFrame(
    {
        "position": range(len(wt_cons)),
        "wt_conservation": wt_cons.values,
        "mut_conservation": mut_cons.values,
        "delta_conservation": delta_cons.values,
        "wt_query_identity": wt_identity.values,
        "mut_query_identity": mut_identity.values,
    }
)

print(summary.iloc[max(0, mut_index - 5) : mut_index + 6])

# Optional: write both alignments for inspection
msa_wt.write_a3m("tp53_wt.a3m")
msa_mut.write_a3m("tp53_r248q_fixed.a3m")
```

Recommended follow-up:

- compare clustering assignments (`cluster_kmeans`) between WT and mutant
- inspect conservation drops around known DNA-contact residues
