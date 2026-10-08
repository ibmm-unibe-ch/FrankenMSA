import os
import requests

def download_pdb(pdb_id: str, output_dir: str) -> str:
    """
    Download a PDB file from the RCSB PDB database.

    Args:
        pdb_id (str): The PDB ID of the structure to download.
        output_dir (str): The directory where the downloaded PDB file will be saved.

    Returns:
        str: The path to the downloaded PDB file.
    """

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Construct the URL for the PDB file
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"

    # Download the PDB file
    response = requests.get(url)
    if response.status_code == 200:
        pdb_file_path = os.path.join(output_dir, f"{pdb_id}.pdb")
        with open(pdb_file_path, 'wb') as f:
            f.write(response.content)
        return pdb_file_path
    else:
        raise Exception(f"Failed to download PDB file for ID {pdb_id}. HTTP status code: {response.status_code}")

def download_fasta(pdb_id: str, output_dir: str) -> str:
    """
    Download a FASTA file from the RCSB PDB database.

    Args:
        pdb_id (str): The PDB ID of the structure to download.
        output_dir (str): The directory where the downloaded FASTA file will be saved.

    Returns:
        str: The path to the downloaded FASTA file.
    """

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Construct the URL for the FASTA file
    url = f"https://www.rcsb.org/fasta/entry/{pdb_id}"

    # Download the FASTA file
    response = requests.get(url)
    if response.status_code == 200:
        fasta_file_path = os.path.join(output_dir, f"{pdb_id}.fasta")
        with open(fasta_file_path, 'wb') as f:
            f.write(response.content)
        return fasta_file_path
    else:
        raise Exception(f"Failed to download FASTA file for ID {pdb_id}. HTTP status code: {response.status_code}")