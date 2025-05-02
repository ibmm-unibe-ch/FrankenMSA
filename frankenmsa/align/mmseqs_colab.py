"""
Use the Colab-integration of MMseqs2 to perform MSA.
"""

import os
from loguru import logger
import requests
import time

from . import base
from ..utils import online, fileio
import pandas as pd

REMOTE_URL = "https://api.colabfold.com"


class MMSeqs2Colab(base.MSAFactory):
    """
    Use the Colab-integration of MMseqs2 to perform MSA.

    Parameters
    ----------
    user_agent : str
        User agent to use for the requests. This is required by the ColabFold API.
    """

    def __init__(self, user_agent: str):
        super().__init__()
        self.user_agent = user_agent
        self.pairing = None
        self.filter = None
        self.use_env = None
        self.use_templates = True
        self.job_id = None
        self.status = None
        self.extracted_files = None
        self._download_location = None

    def align(
        self,
        sequences: list,
        env: bool = True,
        filter: bool = True,
        pairing: str = None,
        save_to: str = None,
        retries: int = 3,
        timeout: int = 10,
        cleanup: bool = True,
    ) -> pd.DataFrame:
        """
        Align a list of sequences using the MMseqs2 Colab API.

        Parameters
        ----------
        sequences : list
            List of sequences to align.
        env : bool, optional
            Use the environment-specific model, by default True
        filter : bool, optional
            Filter sequences, by default False
        pairing : str, optional
            Pair sequences, by default "greedy". Can be "greedy" or "complete"
        save_to : str, optional
            Destination directory, by default None (subfolder with job-id in current working directory)
        retries : int, optional
            Number of retries for API calls, by default 3
        timeout : int, optional
            Timeout for API calls (in seconds), by default 10
        cleanup : bool, optional
            Remove the temporary files after fetching the data, by default True

        Returns
        -------
        pd.DataFrame
            DataFrame containing the aligned sequences.
        """
        self.submit(
            sequences=sequences,
            env=env,
            filter=filter,
            pairing=pairing,
            retries=retries,
            timeout=timeout,
        )
        self.wait()
        self.fetch_results(dest=save_to)
        final = self._extract_a3m()
        self.msa = final
        if cleanup:
            os.system(f"rm -rf {self._download_location}")
        return final

    @property
    def files_to_extract(self):
        files = []
        if self.pairing:
            files.append("pair.a3m")
        else:
            files.append("uniref.a3m")
            if self.use_env:
                files.append("bfd.mgnify30.metaeuk30.smag30.a3m")
        return files

    @property
    def headers(self):
        return {
            "User-Agent": self.user_agent,
        }

    @property
    def submission_endpoint(self):
        if self.pairing:
            return "ticket/pair"
        else:
            return "ticket/msa"

    @property
    def mode(self):
        """
        Generate the mode string for the MMseqs2 API.
        """
        mode = None
        if self.filter:
            mode = "env" if self.use_env else "all"
        else:
            mode = "env-nofilter" if self.use_env else "nofilter"

        if not self.pairing:
            return mode

        self.use_templates = False
        if self.pairing == "greedy":
            mode = "pairgreedy"
        elif self.pairing == "complete":
            mode = "paircomplete"

        if self.use_env:
            mode += "-env"

        return mode

    @property
    def has_failed(self):
        return self.status == "ERROR"

    @property
    def is_pending(self):
        return self.status == "PENDING"

    @property
    def is_running(self):
        return self.status == "RUNNING"

    def submit(
        self,
        sequences: list,
        env: bool = True,
        filter: bool = True,
        pairing: str = None,
        retries: int = 3,
        timeout: int = 10,
    ):
        """
        Submit a list of sequences to the MMseqs2 Colab API.

        Parameters
        ----------
        sequences : list
            List of sequences to align.
        env : bool, optional
            Use the environment-specific model, by default True
        filter : bool, optional
            Filter sequences, by default False
        pairing : str, optional
            Pair sequences, by default "greedy". Can be "greedy" or "complete"
        retries : int, optional
            Number of retries for API calls, by default 3
        timeout : int, optional
            Timeout for API calls (in seconds), by default 10
        """
        if isinstance(sequences, str):
            sequences = [sequences]
        query = ""
        sequences = set(i.upper().strip() for i in sequences)
        self._sequence_indices = [101 + idx for idx, i in enumerate(sequences)]
        for idx, i in enumerate(sequences):
            query += f">{101 + idx:03d}\n{i.strip().upper()}\n"

        self.filter = filter
        if pairing and not pairing in ("greedy", "complete"):
            raise ValueError(
                "Invalid pairing mode. Options are 'greedy' and 'complete'."
            )
        self.pairing = pairing
        self.use_env = env

        data = {
            "q": query,
            "mode": self.mode,
        }
        url = f"{REMOTE_URL}/{self.submission_endpoint}"

        for _ in range(retries):
            try:
                response = requests.post(
                    url, data=data, headers=self.headers, timeout=timeout
                )
                response.raise_for_status()
                out = response.json()
                break
            except requests.exceptions.HTTPError as e:
                if response.status_code == 503:
                    time.sleep(3)
                    logger.warning("[MMSeqs2Colab] Server is busy, retrying...")
                    continue
                else:
                    raise e

        self.job_id = out["id"]
        self.status = out["status"]
        self.raw_data = None

    def wait(self, max_wait: int = None, retry_interval: int = 3):
        """
        Wait for the submitted job to finish.

        Parameters
        ----------
        max_wait : int, optional
            Maximum time to wait (in rounds of retries), by default None (infinite)
        retry_interval : int, optional
            Time to wait between retries (in seconds), by default 3
        """
        if max_wait is not None:
            max_retries = max_wait // retry_interval
        else:
            max_retries = None

        retries = 0
        while self.status in ["PENDING", "RUNNING"]:
            time.sleep(retry_interval)
            self.check_status()
            retries += 1
            if max_retries is not None and retries >= max_retries:
                break
        return self.status

    def check_status(self):
        """
        Check the status of the submitted job.
        """
        url = f"{REMOTE_URL}/ticket/{self.job_id}"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        out = response.json()
        self.status = out["status"]
        return self.status

    def fetch_results(self, dest: str = None, retries: int = 3, timeout: int = 3):
        """
        Get the result of the submitted job.

        Parameters
        ----------
        dest : str, optional
            Destination directory, by default None (subfolder with job-id in current working directory)
        retries : int, optional
            Number of retries for API calls, by default 3
        timeout : int, optional
            Timeout for API calls (in seconds), by default 3
        """
        status = self.check_status()
        if status in ("PENDING", "RUNNING"):
            return None
        elif status == "ERROR":
            raise Exception("Job failed. Make sure the input sequences are valid.")

        url = f"{REMOTE_URL}/result/download/{self.job_id}"
        dest = os.path.join(os.getcwd(), self.job_id) if dest is None else dest
        self._download_location = dest

        for _ in range(retries):
            try:
                files = online.download_targz(
                    url,
                    self.files_to_extract,
                    get_kws={"headers": self.headers},
                    dest=dest,
                )
                break
            except FileNotFoundError as e:
                logger.warning("[MMSeqs2Colab] Could not extract files. Retrying...")
                time.sleep(timeout)
                continue

        for i, j in files.items():
            if j is None:
                raise FileNotFoundError(f"Could not extract {i}")
        self.extracted_files = files

        self.uses_templates = self.use_templates
        self.uses_pairing = self.pairing is not None

        self.msa = self._extract_a3m()
        return self.msa

    def _extract_a3m(self):
        a3m_files = (j for i, j in self.extracted_files.items() if i.endswith(".a3m"))
        a3m_data = {
            "targetID": [],
            "alnScore": [],
            "seqIdentity": [],
            "eVal": [],
            "qStart": [],
            "qEnd": [],
            "qLen": [],
            "tStart": [],
            "tEnd": [],
            "tLen": [],
            "sequence": [],
        }
        for a3m_file in a3m_files:
            for header, sequence in fileio.iter_a3m(a3m_file):
                header_data = _split_header(header)
                if header_data["targetID"] in a3m_data["targetID"]:
                    continue
                for k, v in header_data.items():
                    a3m_data[k].append(v)
                a3m_data["sequence"].append(sequence)

        final = pd.DataFrame(a3m_data)
        final["header"] = final["targetID"]
        return final


def _split_header(header):
    header = header.split()
    if len(header) == 1:
        targetID = header[0]
        alnScore = seqIdentity = eVal = qStart = qEnd = qLen = tStart = tEnd = tLen = 0
    else:
        (
            targetID,
            alnScore,
            seqIdentity,
            eVal,
            qStart,
            qEnd,
            qLen,
            tStart,
            tEnd,
            tLen,
        ) = header
    return {
        "targetID": targetID,
        "alnScore": float(alnScore),
        "seqIdentity": float(seqIdentity),
        "eVal": float(eVal),
        "qStart": int(qStart),
        "qEnd": int(qEnd),
        "qLen": int(qLen),
        "tStart": int(tStart),
        "tEnd": int(tEnd),
        "tLen": int(tLen),
    }
