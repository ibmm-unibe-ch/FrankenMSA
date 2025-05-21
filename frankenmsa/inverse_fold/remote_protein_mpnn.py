"""
Remote ProteinMPNN sequence generator backend
"""

from pathlib import Path
import os
import tempfile
import pandas as pd

from . import backend


class BiolibProteinMPNN(backend.BaseSequenceGenerator):
    """
    Use the Biolib remote ProteinMPNN server to generate sequences from a given protein structure.
    """

    def __init__(self):
        super().__init__()
        try:
            import biolib
        except ImportError:
            raise ImportError(
                "Biolib is not installed. Please install it with 'pip install biolib'."
            )
        self._proteinmpnn = biolib.load("protein_tools/proteinMPNN:0.0.57")

    def generate(
        self,
        pdbfile: str,
        n: int = 128,
        chains: list = None,
        temperature: float = 1.0,
        homomer: bool = True,
    ):
        """
        Generate protein sequences from a PDB file.

        Parameters
        ----------
        pdbfile : str
            Path to the PDB file.
        n : int
            Number of sequences to generate.
        chains : list
            List of chains to design. If None, all chains will be designed.
        temperature : float
            Sampling temperature. Higher values result in more diverse sequences.
        homomer : bool
            If True, treat the protein as a homomer. If False, treat it as a heteromer.
            For now, only homomer is supported.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the generated sequences
        dict
            Other metadata related to the generation process.
        """
        if not homomer:
            raise ValueError("Heteromeric design is not supported yet.")
        if not Path(pdbfile).exists():
            raise FileNotFoundError(f"PDB file {pdbfile} does not exist.")

        outdir = Path(pdbfile).parent / "proteinmpnn_output"
        args = [
            "--pdb_path",
            pdbfile,
            "--homomer",  # since we only
            "--num_seq_per_target",
            str(n),
            "--sampling_temp",
            str(temperature),
            "--out_folder",
            str(outdir),
        ]
        if chains is None:
            from frankenmsa.utils.pdbtools import get_chain_ids

            chains = get_chain_ids(pdbfile)
        args.extend(
            [
                "--pdb_path_chains",
                " ".join(chains),
            ]
        )
        results = self._proteinmpnn.cli(args)
        out = results.to_dict()
        if out["state"] == "failed":
            raise RuntimeError(
                f"ProteinMPNN generation failed. Check the logs online at: {results.get_shareable_link()} "
            )
        results.save_files(str(outdir))
        df = pd.read_csv(outdir / outdir.name / "designed_sequences.csv")
        df.rename(columns={"design": "header"}, inplace=True)
        df.drop(columns=["temperature"], inplace=True)
        os.system(f"rm -rf {outdir}")
        return df, out
