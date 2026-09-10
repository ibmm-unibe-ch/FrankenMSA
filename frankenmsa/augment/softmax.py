from __future__ import annotations

import numpy as np
import pandas as pd
import scipy
import blosum

from ..augment import base
from ..runtime import log_message


def _resolve_blosum_matrix(matrix=None):
    if matrix is None:
        return blosum.BLOSUM(62)
    if isinstance(matrix, str):
        normalized = matrix.strip().upper().replace(" ", "")
        if not normalized.startswith("BLOSUM"):
            raise ValueError(f"Unsupported BLOSUM selector: {matrix!r}")
        try:
            return blosum.BLOSUM(int(normalized.removeprefix("BLOSUM")))
        except ValueError as exc:
            raise ValueError(f"Unsupported BLOSUM selector: {matrix!r}") from exc
    if isinstance(matrix, int):
        return blosum.BLOSUM(matrix)
    return matrix


class Softmax(base.AugmentationFactory):
    """Augmentation method that samples sequence variants from a BLOSUM softmax distribution."""

    def augment(
        self,
        sequence: str,
        temperature: float = 1.0,
        depth: int = 128,
        matrix=None,
    ) -> pd.DataFrame:
        matrix = _resolve_blosum_matrix(matrix)

        sequence = (sequence or "").strip().upper()
        processed = sequence.replace("O", "K").replace("U", "C")
        if not processed:
            return pd.DataFrame({"header": [], "sequence": []})

        blosum_alphabet = [char for char in matrix.keys() if char != "*"]
        char_to_idx = {char: i for i, char in enumerate(blosum_alphabet)}
        idx_to_char = {i: char for i, char in enumerate(blosum_alphabet)}

        blosum_matrix_np = np.zeros(
            (len(blosum_alphabet), len(blosum_alphabet)),
            dtype=np.float32,
        )
        for r_char in blosum_alphabet:
            for c_char in blosum_alphabet:
                blosum_matrix_np[char_to_idx[r_char], char_to_idx[c_char]] = matrix[r_char][c_char]

        # 3. Process sequence and convert to indices, handling 'O' and 'U' replacements
        valid_indices = []
        valid_chars = []
        for start_char in sequence:
            if start_char == "O":
                char = "K"
            elif start_char=="U":
                char = "C"
            else:
                char = start_char
            # Only include characters that are in the BLOSUM alphabet
            if char in char_to_idx:
                valid_indices.append(char_to_idx[char])
                valid_chars.append(start_char)

        if not valid_indices:
            log_message("Softmax augmentation received no valid amino-acid characters.")
            return pd.DataFrame({"header": [], "sequence": []})

        seq_indices_np = np.array(valid_indices, dtype=int)
        scores_for_sequence = blosum_matrix_np[seq_indices_np] * float(temperature)
        probabilities_np = scipy.special.softmax(scores_for_sequence, axis=1)

        generated_sequences = ["".join(valid_chars)]
        for _ in range(max(1, int(depth))):
            sampled_chars = []
            for _, row in enumerate(probabilities_np):
                sampled_index = np.random.choice(len(blosum_alphabet), p=row)
                sampled_chars.append(idx_to_char[sampled_index])
            generated_sequences.append("".join(sampled_chars))

        result_df = pd.DataFrame(
            {
                "header": [f"softmax_{idx}" for idx in range(len(generated_sequences))],
                "sequence": generated_sequences,
            }
        )
        log_message(
            f"Softmax augmentation completed. Generated {len(result_df)} sequences."
        )
        return result_df


__all__ = ["Softmax"]