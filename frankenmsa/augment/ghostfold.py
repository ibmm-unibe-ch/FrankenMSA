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
        output_name = "ghostfold_output"
        Path(GHOSTFOLD_PATH/output_name).mkdir(exist_ok=True)
        log_message(f"In file running GhostFold augmentation for input sequence: {sequence}")
        write_a3m(pd.DataFrame({"header":["GhostFold_input"],"sequence": [sequence]}), f"{GHOSTFOLD_PATH/jobname}.fasta")
        log_message(f"Written input sequence to {GHOSTFOLD_PATH/jobname}.fasta, running GhostFold...")
        cmd_string = f"{GHOSTFOLD_PATH}/ghostfold.sh --project_name {output_name} --fasta_file {GHOSTFOLD_PATH/jobname}.fasta --msa-only"
        
        log_message(f"Running GhostFold command: {cmd_string}")
        proc = subprocess.run(
            cmd_string.split(),
            cwd=GHOSTFOLD_PATH,
            capture_output=True,
            text=True,
        )

        log_message(f"GhostFold stdout:\n{proc.stdout}")
        log_message(f"GhostFold stderr:\n{proc.stderr}")

        if proc.returncode != 0:
            msg = f"GhostFold failed with returncode {proc.returncode}. Check ghostfold.log for output."
            log_message(msg)
            raise subprocess.CalledProcessError(proc.returncode, proc.args, output=proc.stdout, stderr=proc.stderr)

        output_fasta_name = f"{GHOSTFOLD_PATH/output_name}/msa/GhostFold_input/pstMSA.fasta"
        log_message(f"GhostFold command completed, reading output from {output_fasta_name}...")
        output_sequences, output_descriptions = read_fasta(output_fasta_name)
        log_message(f"GhostFold augmentation completed. Generated {len(output_sequences)} sequences.")
        return pd.DataFrame({"header": output_descriptions, "sequence": output_sequences})
    