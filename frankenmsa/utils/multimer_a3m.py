from pathlib import Path
from typing import List, Tuple

print("[DEBUG] multimer_a3m loaded from:", __file__)


def parse_a3m(path: str) -> List[Tuple[str, str]]:
    records = []
    header = None
    seq_chunks = []
    with open(path, "r") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    records.append((header, "".join(seq_chunks)))
                header = line.strip()  # keep full header line, trimmed
                seq_chunks = []
            else:
                seq_chunks.append(line)
        if header is not None:
            records.append((header, "".join(seq_chunks)))
    if not records:
        raise ValueError(f"Empty or invalid A3M: {path}")
    return records


def combine_unpaired_a3m(
    input_paths: List[str],
    output_path: str,
    add_anchor: bool = True,
) -> None:
    import tempfile
    from pathlib import Path

    if not output_path or output_path.strip() in ("/", ".", "./"):
        out = Path(tempfile.gettempdir()) / "frankenmsa_multimer.a3m"
    else:
        out = Path(output_path)

        if out.is_dir() or str(out).endswith(("/", "\\")):
            out = out / "multimer.a3m"

        if not out.parent.exists() or str(out.parent) == "":
            out = Path(tempfile.gettempdir()) / out.name

    out.parent.mkdir(parents=True, exist_ok=True)

    chains = [parse_a3m(p) for p in input_paths]

    # Normalize: (a) equalize record count across chains, (b) pad per-chain sequences to same length
    if not all(len(c) > 0 for c in chains):
        raise ValueError("One or more A3M files are empty or invalid.")

    # Truncate to the minimum number of records so chains are aligned row-wise
    min_rows = min(len(c) for c in chains)
    if any(len(c) != min_rows for c in chains):
        print(f"[WARN] Truncating chains to {min_rows} records to equalize row count.")
        chains = [c[:min_rows] for c in chains]

    def _pad(seq: str, target: int) -> str:
        return seq + ("-" * (target - len(seq))) if len(seq) < target else seq

    # Pad sequences within each chain so all sequences in that chain have identical length
    norm_chains = []
    per_chain_lengths = []
    for c in chains:
        max_len = max(len(s) for _, s in c)
        per_chain_lengths.append(max_len)
        norm_chains.append([(h, _pad(s, max_len)) for (h, s) in c])

    chains = norm_chains

    # Final lengths for multimer header
    lengths = per_chain_lengths
    card = ["1"] * len(chains)
    header_line = f"#" + ",".join(str(L) for L in lengths) + "\t" + ",".join(card)

    lines = [header_line]

    if add_anchor:
        # Write a single anchor sequence >101 with all chains concatenated (no gaps)
        lines.append(">101")
        anchor_seq = "".join(chains[i][0][1] for i in range(len(chains)))
        lines.append(anchor_seq)

    for chain_idx, chain in enumerate(chains):
        pad_left = sum(lengths[:chain_idx])
        pad_right = sum(lengths[chain_idx + 1 :])
        for h, seq in chain:
            seq = seq.replace(" ", "")
            # sanitize tabs in headers (ColabFold is picky)
            h_clean = h.replace("\t", " ").strip()
            lines.append(h_clean)
            lines.append("-" * pad_left + seq + "-" * pad_right)

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
