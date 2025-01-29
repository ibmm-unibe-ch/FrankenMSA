"""
Base class for multiple sequence alignment (MSA) algorithms.
"""

from typing import List

class MSAResult:
    def __init__(self):
        self.m8_data = None
        self.a3m_data = None
        self.template_data = None
        self.uses_templates = False
        self.uses_pairing = False

class MSABackend:
    def __init__(self):
        self.msa = None

    def align(self, sequences: List[str], *args, **kwargs) -> List[str]:
        """
        Align a list of sequences.

        Parameters
        ----------
        sequences: List of sequences to align.
        """
        raise NotImplementedError()

    def write_m8(self, filename: str, clear: bool = True):
        """
        Write the MSA in m8 format to a file.

        Parameters
        ----------
        filename: str
            Output file name.
        """
        if self.msa is None:
            raise ValueError("MSA is empty.")
        if not filename.endswith(".m8"):
            raise ValueError("Output file must have .m8 extension.")
        with open(filename, "w") as f:
            f.write(self.msa)
        if clear:
            del self.msa
            self.msa = None

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
