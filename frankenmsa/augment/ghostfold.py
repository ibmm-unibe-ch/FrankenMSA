from ..augment import base
import pandas as pd
from pathlib import Path
import subprocess
from ..utils.fileio import read_fasta, write_a3m


def log_message(message:str):
    with open("/content/app/log.txt", "a") as log_file:
        log_file.write(f"{message}\n")

GHOSTFOLD_PATH = Path("/content/ghostfold")  # TODO: set this to the actual path of the ghostfold installation

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
        output_name = GHOSTFOLD_PATH / "ghostfold_output"
        Path(f"{output_name}").mkdir(exist_ok=True)
        log_message(f"In file running GhostFold augmentation for input sequence: {sequence}")
        write_a3m(pd.DataFrame({"header":["GhostFold_input"],"sequence": [sequence]}), f"{GHOSTFOLD_PATH/jobname}.fasta")
        log_message(f"Written input sequence to {GHOSTFOLD_PATH/jobname}.fasta, running GhostFold...")
        cmd_string = f"{GHOSTFOLD_PATH}/ghostfold.sh --project_name {output_name} --fasta_file {GHOSTFOLD_PATH/jobname}.fasta --msa-only"
        
        log_message(f"Running GhostFold command: {cmd_string}")
        subprocess.run(cmd_string.split(),check=True, cwd=GHOSTFOLD_PATH)
        output_fasta_name = f"{GHOSTFOLD_PATH/output_name}/msa/{jobname}/pstMSA.fasta"
        log_message(f"GhostFold command completed, reading output from {output_fasta_name}...")
        output_sequences = read_fasta(output_fasta_name)
        log_message(f"GhostFold augmentation completed. Generated {len(output_sequences)} sequences.")
        return output_sequences
    