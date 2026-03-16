from ..augment import base
import pandas as pd
from pathlib import Path
import subprocess
from ..utils.fileio import read_fasta, write_a3m


GHOSTFOLD_PATH = "."  # TODO: set this to the actual path of the ghostfold installation

class GhostFoldAugmentation(base.AugmentationFactory):
    """
    Augmentation method that uses GhostFold to generate new sequences.
    """
    def augment(self, sequence):
        """
        Augment sequences using GhostFold.

        Parameters
        ----------
        sequence : str
            Input sequence to augment.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the augmented sequences.
        """
        jobname = "ghostfold_job"
        output_name = "ghostfold_output"
        Path(f"{output_name}").mkdir(exist_ok=True)
        write_a3m(pd.DataFrame({"header":["GhostFold_input"],"sequence": [sequence]}), f"{jobname}.fasta")
        cmd_string = f"{GHOSTFOLD_PATH}/ghostfold.sh --project_name {output_name} --fasta_file {jobname}.fasta --msa-only"
        subprocess.run(cmd_string.split(),check=True, cwd=GHOSTFOLD_PATH)
        output_fasta_name = f"{output_name}/msa/{jobname}/pstMSA.fasta"
        output_sequences = read_fasta(output_fasta_name)
        return output_sequences
    