# MSA Study: TP53 hotspot mutation context (R248Q)

This notebook uses TP53 as a mutation-context study, not just a toy
conservation exercise. The key idea is to compare **WT-seeded** and
**R248Q-seeded** homolog neighborhoods and inspect how residue preferences shift
at functionally important positions.

R248 is a canonical TP53 DNA-contact hotspot in cancer cohorts.

```python
from collections import Counter
import pandas as pd

from frankenmsa.align import MMSeqs2Colab
from frankenmsa.msa import MSA

# Human TP53 (UniProt P04637)
tp53_query = (
    "SQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPPVAPAPAAPTPAAPAP"
    "SWPLSSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIY"
    "KQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYM"
    "CNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELPPGSTKRALPTST"
)

# 0-based mutation index for residue 248
mut_index = 247
tp53_r248q = tp53_query[:mut_index] + "Q" + tp53_query[mut_index + 1 :]

mmseqs = MMSeqs2Colab(user_agent="frankenmsa-tutorials")

# 1) Build WT-seeded and mutant-seeded MSAs independently
wt_raw = mmseqs.align([tp53_query], env=True, filter=True, pairing=None)
mut_raw = mmseqs.align([tp53_r248q], env=True, filter=True, pairing=None)

msa_wt = MSA(wt_raw).drop_duplicates().filter_gaps(0.4)
msa_mut = MSA(mut_raw).drop_duplicates().filter_gaps(0.4)

# 2) Compare residue preference shifts at key TP53 positions
def residue_frequencies(msa: MSA, pos_0based: int, top_n: int = 8) -> pd.Series:
    residues = []
    for s in msa.df["sequence"]:
        if pos_0based < len(s):
            aa = s[pos_0based]
            if aa != "-":
                residues.append(aa)
    counts = Counter(residues)
    total = sum(counts.values()) or 1
    freq = {aa: c / total for aa, c in counts.items()}
    return pd.Series(freq).sort_values(ascending=False).head(top_n)

# canonical DNA-contact/hotspot positions in TP53 core domain
positions = {
    "R175 hotspot": 174,
    "R248 hotspot": 247,
    "R273 hotspot": 272,
}

for label, pos in positions.items():
    wt_freq = residue_frequencies(msa_wt, pos)
    mut_freq = residue_frequencies(msa_mut, pos)
    table = pd.concat(
        [wt_freq.rename("WT-seeded"), mut_freq.rename("R248Q-seeded")], axis=1
    ).fillna(0.0)
    print(f"\n=== {label} (1-based {pos+1}) ===")
    print(table.head(10))

# 3) Save artifacts for downstream workflows
msa_wt.write_a3m("tp53_wt_seeded.a3m")
msa_mut.write_a3m("tp53_r248q_seeded.a3m")
```

## Why this is useful

The output gives a practical shortlist of context residues that co-vary
differently between WT- and mutant-seeded neighborhoods. That can drive
follow-up design/structure work, for example:

- choose compensatory candidates near the DNA-binding surface (e.g., positions
  around 175/248/273) for combinatorial mutation sets,
- run AlphaFold/other structure pipelines on selected combinations,
- dock to DNA or compare interface confidence/ranking between WT-like and
  mutant-like sequence contexts.
