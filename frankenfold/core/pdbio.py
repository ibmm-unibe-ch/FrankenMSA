"""
PDB I/O functions
"""

from . import utils


class PDB:
    """
    The PDB data container
    """

    def __init__(self):
        self.data = None
        self.file = None
        self.pdbid = None

    @property
    def chains(self) -> list:
        """
        Get the chain IDs in the PDB data

        Returns
        -------
        list
            The list of chain IDs
        """
        chains = []
        for line in self.data.split("\n"):
            if line.startswith("ATOM"):
                chain = line[21]
                if chain not in chains:
                    chains.append(chain)
        return chains

    def write(self, file_path: str):
        """
        Write the PDB data to a file

        Parameters
        ----------
        file_path : str
            The file path to write the PDB data to
        """
        with open(file_path, "w") as f:
            f.write(self.data)
        self.file = file_path

    def to_tmpfile(self):
        """
        Write the PDB data to a temporary file

        Returns
        -------
        str
            The temporary file path
        """
        self.file = utils.tmpfile(self.data, suffix=".pdb")

    @classmethod
    def from_file(cls, filepath: str):
        """
        Read a PDB file

        Parameters
        ----------
        filepath : str
            The file path to read the PDB data from

        Returns
        -------
        PDB
            The PDB object
        """
        with open(filepath, "r") as f:
            pdb_data = f.read()
        new = cls()
        new.data = pdb_data
        new.file = filepath
        return new

    @classmethod
    def from_rcsb(cls, pdbid: str):
        """
        Query the RCSB PDB database for a PDB file

        Parameters
        ----------
        pdbid : str
            The PDB ID to query

        Returns
        -------
        PDB
            The PDB object
        """
        import requests

        url = f"https://files.rcsb.org/download/{pdbid}.pdb"
        pdb_data = requests.get(url).text
        new = cls()
        new.data = pdb_data
        new.pdbid = pdbid
        return new
