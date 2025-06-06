"""
Base classes for multiple sequence alignment (MSA) algorithms.
"""

from typing import List
import pandas as pd
import numpy as np
import pickle
from pathlib import Path


class MSA:
    """
    Store Multiple-Sequence Alignment data.

    Attributes
    ----------
    raw : MSARawData
        Raw MSA data that was generated by a backend.
    metadata : M8Metadata
        Alignment Metadata.
    alignment : A3MAlignment
        Alignment of sequences.
    templates : TemplateData
        Template data.
    """

    def __init__(self):
        self.raw = None
        self.metadata = None
        self.alignment = None
        self.templates = None

    def export(self, prefix: str):
        """
        Export the MSA data to a directory.

        Parameters
        ----------
        prefix : str
            Prefix for the file names.
        """
        if self.raw is not None:
            with open(f"{prefix}.raw.pkl", "wb") as f:
                pickle.dump(self.raw, f)
        if self.metadata is not None:
            self.metadata.write(f"{prefix}.m8")
        if self.alignment is not None:
            self.alignment.write(f"{prefix}.a3m")
        if self.templates is not None:
            self.templates.write(f"{prefix}.templates")

    @classmethod
    def from_files(cls, prefix: str):
        """
        Import the MSA data from a directory.

        Parameters
        ----------
        prefix : str
            Prefix for the file names.
        """
        new = cls()
        new.raw = raw
        prefix = Path(prefix)
        raw_pickle = prefix.with_suffix(".raw.pkl")
        if raw_pickle.exists():
            with open(raw_pickle, "rb") as f:
                raw = pickle.load(f)
        else:
            raw = None

        m8 = prefix.with_suffix(".m8")
        if m8.exists():
            new.metadata = M8Metadata.from_file(m8)

        a3m = prefix.with_suffix(".a3m")
        if a3m.exists():
            new.alignment = A3MAlignment.from_file(a3m)

        templates = prefix.with_suffix(".templates")
        if templates.exists():
            new.templates = TemplateData.from_file(templates)
        return new

    @classmethod
    def from_sequences(
        cls, sequences: List[str], extra: dict = None, headers_key: str = None
    ):
        """
        Create an MSA object from a list of sequences.

        Parameters
        ----------
        sequences : List[str]
            List of sequences
        extra : dict, optional
            Extra metadata. This should be a dictionary where values are array-like and have the same length as the sequences list.
        headers_key : str, optional
            Key in the extra metadata dictionary that contains the headers for the sequences (if any), by default None.

        Returns
        -------
        MSA
            MSA object.
        """
        msa = cls()
        msa.alignment = A3MAlignment.from_sequences(sequences, extra, headers_key)
        return msa

    def save(self, filename: str):
        """
        Save the MSA data to a pickle file.

        Parameters
        ----------
        filename : str
            File name.
        """
        with open(filename, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filename: str):
        """
        Load MSA data from a pickle file.

        Parameters
        ----------
        filename : str
            File name.

        Returns
        -------
        MSA
            MSA object.
        """
        with open(filename, "rb") as f:
            return pickle.load(f)

    def __len__(self):
        if self.alignment is not None:
            return len(self.alignment)
        elif self.metadata is not None:
            return len(self.metadata)


class M8Metadata:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        for attr in df.columns:

            @property
            def getter(self, attr=attr):
                return self.df[attr].to_numpy()

    def __setitem__(self, key, value):
        self.df[key] = value

    def __getitem__(self, key):
        return self.df[key]

    def __len__(self):
        return len(self.df)

    def write(self, filename: str):
        """
        Write the M8 data to an M8 file.

        Parameters
        ----------
        filename : str
            File name.
        """
        self.df.to_csv(filename, sep="\t", header=False, index=False)

    @classmethod
    def from_file(cls, filename: str):
        df = pd.read_csv(
            filename,
            sep="\t",
            header=None,
            index_col=False,
            names=[
                "query",
                "target",
                "identity",
                "alignment_length",
                "mismatches",
                "gap_opens",
                "q_start",
                "q_end",
                "t_start",
                "t_end",
                "evalue",
                "bit_score",
            ],
        )
        return cls(df)


class A3MAlignment:
    def __init__(self, df: pd.DataFrame):
        if not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a pandas DataFrame.")
        if not all([i in df.columns for i in ["header", "sequence"]]):
            raise ValueError("df must have columns 'header' and 'sequence'.")
        self.df = df
        self.df["query"] = self.df["header"][0]
        self.extra_df = None

    @property
    def extra(self) -> np.ndarray:
        """
        Extra metadata that is included in the sequence headers
        The first entry in the array is the header, the rest are the metadata.
        """
        data = self.df["header"].apply(lambda x: x.split("\t"))
        max_length = data.apply(len).max()
        return data.apply(lambda x: x + [""] * (max_length - len(x))).to_numpy()

    @property
    def headers(self) -> np.ndarray:
        return self.df["header"].to_numpy()

    @property
    def sequences(self) -> np.ndarray:
        return self.df["sequence"].to_numpy()

    @sequences.setter
    def sequences(self, value: np.ndarray):
        self.df["sequence"] = value

    @property
    def has_insertions(self) -> np.ndarray:
        """
        Check if sequences have insertions.

        Returns
        -------
        np.ndarray
            Boolean array indicating if the sequences have insertions.
        """
        return (
            self.df["sequence"].apply(lambda x: any(i.islower() for i in x)).to_numpy()
        )

    @classmethod
    def from_file(cls, filename: str):
        """
        Create an A3MAlignment object from an A3M file.

        Parameters
        ----------
        filename : str
            File name.

        Returns
        -------
        A3MAlignment
            A3MAlignment object.
        """
        headers = []
        sequences = []
        with open(filename, "r") as f:
            for line in f:
                if line.startswith(">"):
                    headers.append(line[1:].strip())
                else:
                    sequences.append(line.strip())
        df = pd.DataFrame({"header": headers, "sequence": sequences})
        return cls(df)

    @classmethod
    def from_string(cls, string: str):
        """
        Create an A3MAlignment object from a A3M / multiple sequence alignment string in Fasta format.

        Parameters
        ----------
        string : str
            A3M / multiple sequence alignment string in Fasta format.

        Returns
        -------
        A3MAlignment
            A3MAlignment object.
        """
        headers = []
        sequences = []
        for line in string.split("\n"):
            if line.startswith(">"):
                headers.append(line[1:].strip())
            else:
                sequences.append(line.strip())
        df = pd.DataFrame({"header": headers, "sequence": sequences[:-1]})
        return cls(df)

    @classmethod
    def from_sequences(
        cls, sequences: List[str], extra: dict = None, headers_key: str = None
    ):
        """
        Create an A3MAlignment object from a list of sequences.

        Parameters
        ----------
        sequences : List[str]
            List of sequences.
        extra : dict, optional
            Extra metadata. This should be a dictionary where values are array-like and have the same length as the sequences list.
        headers_key : str, optional
            Key in the extra metadata dictionary that contains the headers for the sequences (if any), by default None.

        Returns
        -------
        A3MAlignment
            A3MAlignment object.
        """
        if extra is not None:
            if headers_key is not None:
                _headers = extra[headers_key]
            else:
                _headers = [str(i) for i in range(len(sequences))]
            headers = []
            for i in range(len(sequences)):
                header = [_headers[i]]
                for key, value in extra.items():
                    if key != headers_key:
                        header.append(str(value[i]))
                headers.append("\t".join(header))
            df = pd.DataFrame({"header": headers, "sequence": sequences})
            for key, value in extra.items():
                if key != headers_key:
                    df[key] = value
            new = cls(df)
            new.extra_df = pd.DataFrame(extra)
            return new
        else:
            df = pd.DataFrame({"header": range(len(sequences)), "sequence": sequences})
            return cls(df)

    def make_extra_df(self, columns: list) -> pd.DataFrame:
        """
        Create a DataFrame from the extra metadata in the headers.

        Parameters
        ----------
        columns : list
            Column names for the DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame with the extra metadata.
        """
        extra = self.extra
        extra_df = pd.DataFrame(extra.tolist(), columns=columns)
        self.extra_df = extra_df
        return extra_df

    def update_headers_from_extra(self):
        """
        Update the headers from the extra metadata DataFrame.
        """
        if self.extra_df is None:
            raise ValueError("Extra metadata DataFrame not found.")
        self.df["header"] = self.extra_df.apply(lambda x: "\t".join(x), axis=1)

    def drop_insertions(self):
        """
        Drop sequences with insertions.
        """
        ref_length = len(self.df["sequence"].iloc[0])
        self.df = self.df[self.df["sequence"].apply(lambda x: len(x) == ref_length)]
        return self

    def mask_insertions(self):
        """
        Convert all sequences to uppercase (i.e. mask insertions).
        """
        self.df["sequence"] = self.df["sequence"].apply(lambda x: x.upper())
        return self

    def crop(self, n: int, axis: int = 0):
        """
        Crop the sequences or alignment to a certain length.

        Parameters
        ----------
        n : int
            Length to crop the sequences to.
        axis : int, optional
            Axis to crop along, by default 0 = crop sequences. If 1, crop the alignment.
        """
        if axis == 0:
            self.df["sequence"] = self.df["sequence"].apply(lambda x: x[:n])
        elif axis == 1:
            self.df = self.df.iloc[:n]
        else:
            raise ValueError(f"Invalid axis: {axis=}")
        return self

    def slice(self, start: int, end: int, axis: int = 0):
        """
        Slice the sequences or alignment.

        Parameters
        ----------
        start : int
            Start index.
        end : int
            End index.
        axis : int, optional
            Axis to slice along, by default 0 = slice sequences. If 1, slice the alignment.
        """
        if axis == 0:
            self.df["sequence"] = self.df["sequence"].apply(lambda x: x[start:end])
        elif axis == 1:
            self.df = self.df.iloc[:, start:end]
        else:
            raise ValueError(f"Invalid axis: {axis=}")
        return self

    def to_depth(self, n: int, extend: str = "repeat", crop: bool = False):
        """
        Extend or crop the alignment until the desired depth is reached.

        Parameters
        ----------
        n : int
            Desired depth.
        extend : str, optional
            What to do if the MSA is smaller than the desired depth. Options are 'repeat' (introduce duplicate entries) or 'patch' (just add "----" sequences).
        crop : bool, optional
            If True, crop the alignment if they are longer than the desired depth, by default False.
        """
        if len(self.df) < n:

            if extend == "repeat":
                incoming = self.df.copy()[: n - len(self.df)]
                incoming["header"] = [f"gap_{i}" for i in range(len(incoming))]
                self.df = pd.concat([self.df, incoming], ignore_index=True)

            elif extend == "patch":
                n_extend = n - len(self.df)
                seq_length = len(self.df["sequence"].iloc[0])
                seq = "-" * seq_length
                incoming = {
                    "header": [f"gap_{i}" for i in range(n_extend)],
                    "sequence": [seq] * n_extend,
                    "query": [self.df["query"].iloc[0]] * n_extend,
                }
                self.df = pd.concat(
                    [self.df, pd.DataFrame(incoming)], ignore_index=True
                )

            else:
                raise ValueError(f"Invalid option for 'extend': {extend=}")

        elif len(self.df) > n and crop:
            self.df = self.df.iloc[:n]

        return self

    def filter(
        self,
        diff: int,
        max_pairwise_identity: int = 100,
        min_query_coverage: int = 50,
        min_query_identity: int = 0,
        min_query_score: float = -20,
        target_diversity: int = 0,
        *args,
        **kwargs,
    ):
        """
        Filter the alignment using HH-suite's hhfilter.

        Parameters
        ----------
        diff : int
            Sequence diversity factor. Minimum sequences to retain. (option -diff).
        max_pairwise_identity : int, optional
            Maximum pairwise identity, by default 100 (option -id).
        min_query_coverage : int, optional
            Minimum query coverage, by default 50 (option -cov).
        min_query_identity : int, optional
            Minimum query identity, by default 0 (option -qid).
        min_query_score : float, optional
            Minimum query score, by default -20 (option -qsc).
        target_diversity : int, optional
            Target diversity, by default 0 = disabled (option -neff).
        output_file : str, optional
            Path to the output MSA file, by default the input filename is appended by 'filtered'.
        *args
            Additional arguments that will be passed to the hhfilter command (dashes are added automatically).
        **kwargs
            Additional keyword arguments that will be passed to the hhfilter command (dashes are added automatically).
        """
        from .hhsuite import hhfilter, has_hhsuite

        if not has_hhsuite():
            raise ImportError("HH-suite is not installed.")

        from uuid import uuid4

        filename = f"temp_{uuid4()}.a3m"
        self.write(filename)
        filtered = hhfilter(
            filename,
            diff,
            max_pairwise_identity,
            min_query_coverage,
            min_query_identity,
            min_query_score,
            target_diversity,
            *args,
            **kwargs,
        )
        self.df = A3MAlignment.from_file(filtered).df
        Path(filename).unlink()
        Path(filtered).unlink()
        return self

    def write(self, filename: str):
        """
        Write the alignment data to an A3M file.

        Parameters
        ----------
        filename : str
            File name.
        """
        with open(filename, "w") as f:
            for i in range(len(self.df)):
                row = self.df.iloc[i]
                f.write(f">{row['header']}\n")
                f.write(f"{row['sequence']}\n")

    def concat(self, other: "A3MAlignment"):
        """
        Merge this alignment data with another alignment data object.

        Parameters
        ----------
        other : A3MAlignment
            object to merge with.
        """
        self.df = pd.concat([self.df, other.df], ignore_index=True)
        return self

    def __setitem__(self, key, value):
        self.df[key] = value

    def __getitem__(self, key):
        return self.df[key]

    def __len__(self):
        return len(self.df)


class TemplateData:
    def __init__(self):
        self.template_ids = []
        self.structure_files = []
        self.index_files = []

    def add(self, template_id: str, structure_files: str, index_files: str):
        self.template_ids.append(template_id)
        self.structure_files.append(structure_files)
        self.index_files.append(index_files)

    def __getitem__(self, key):
        return self.template_ids[key], self.structure_files[key], self.index_files[key]

    def write(self, filename: str):
        """
        Write the template data to a json file.

        Parameters
        ----------
        filename : str
            File name.
        """
        import json

        with open(filename, "w") as f:
            json.dump(
                {
                    "template_ids": self.template_ids,
                    "structure_files": self.structure_files,
                    "index_files": self.index_files,
                },
                f,
            )

    @classmethod
    def from_file(cls, filename: str):
        """
        Load template data from a json file.

        Parameters
        ----------
        filename : str
            File name.

        Returns
        -------
        TemplateData
            Template data object.
        """
        import json

        with open(filename, "r") as f:
            data = json.load(f)
        new = cls()
        new.template_ids = data["template_ids"]
        new.structure_files = data["structure_files"]
        new.index_files = data["index_files"]
        return new

    def __len__(self):
        return len(self.template_ids)


class MSARawData:
    """
    Store raw MSA data that is fetched from an MSA backend.

    Parameters
    ----------
    backend : str
        MSA backend factory name that was used to fetch the data.

    Attributes
    ----------
    m8_raw_data : str
        Data relating to m8 data files.
    a3m_raw_data : str
        Data relating to a3m data files.
    template_data : str
        Data relating to template data files.
    uses_templates : bool
        Whether the MSA uses templates.
    uses_pairing : bool
        Whether the MSA uses pairing.
    """

    def __init__(self, backend: str):
        self.backend = backend.lower()
        self.m8_raw_data = None
        self.a3m_raw_data = None
        self.template_raw_data = None
        self.uses_templates = False
        self.uses_pairing = False


class MSABackendFactory:
    def __init__(self):
        self.msa = None
        self.raw_data = None

    def align(self, sequences: List[str], *args, **kwargs) -> MSA:
        """
        Align a list of sequences.

        Parameters
        ----------
        sequences: List of sequences to align.

        Returns
        -------
        MSA
            MSA object.
        """
        raise NotImplementedError()

    def __call__(self, *args, **kwds):
        return self.align(*args, **kwds)


def _download_targz(
    url: str, files_of_interest: list, dest: str = None, get_kws: dict = None
):
    """
    Download and extract a .tar.gz file.

    Parameters
    ----------
    url: str
        URL to the .tar.gz file.
    files_of_interest: list
        List of files to extract. These must be the exact file names.
    dest: str, optional
        Destination directory, by default None
    get_kws: dict, optional
        Additional keyword arguments for the GET request, by default None

    Returns
    -------
    dict
        Dictionary containing the extracted file names and paths of interest. Keys are the file names.
        Values are the file paths. Files that could not be extracted are set to None.
    """
    import os
    import tarfile
    import requests

    get_kws = {} if get_kws is None else get_kws

    path = os.getcwd() if dest is None else dest
    os.makedirs(path, exist_ok=True)
    response = requests.get(url, **get_kws)
    response.raise_for_status()
    with open("temp.tar.gz", "wb") as f:
        f.write(response.content)

    final = {i: None for i in files_of_interest}
    with tarfile.open("temp.tar.gz", "r:gz") as tar:
        for member in tar.getmembers():
            if member.name in files_of_interest:
                tar.extract(member, path=path)
                final[member.name] = os.path.join(path, member.name)

    os.remove("temp.tar.gz")
    return final


def _retry_request(
    url, mode: "post", retries: int = 3, interval: int = 10, kws: dict = None
):
    """
    Retry a request.

    Parameters
    ----------
    url : str
        URL to request.
    mode : str
        Request mode (GET or POST).
    retries : int, optional
        Number of retries, by default 3
    interval : int, optional
        Interval between retries (in seconds), by default 10
    kws : dict, optional
        Additional keyword arguments for the request, by default None

    Returns
    -------
    requests.Response
        Response object.
    """
    import requests
    import time

    for _ in range(retries):
        if mode == "post":
            response = requests.post(url, **kws)
        elif mode == "get":
            response = requests.get(url, **kws)
        else:
            raise ValueError("Invalid mode. Must be 'post' or 'get'.")
        if response.ok:
            return response
        time.sleep(interval)
    return response
