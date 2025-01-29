"""
Use the Colab-integration of MMseqs2 to perform MSA.
"""

import os
from loguru import logger
import requests
import time

from . import msa_base

REMOTE_URL = "https://api.colabfold.com"


class MMSeqs2Colab(msa_base.MSABackend):
    def __init__(self, user_agent: str):
        logger.critical("THIS IS NOT YET FULLY IMPLEMENTED")
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

    @property
    def files_to_extract(self):
        files = ["pdb70.m8"]
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
        self.msa = None

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

    def get_result(self, dest: str = None, retries: int = 3, timeout: int = 3):
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
            raise Exception("Job failed.")

        url = f"{REMOTE_URL}/result/download/{self.job_id}"
        dest = os.path.join(os.getcwd(), self.job_id) if dest is None else dest
        self._download_location = dest

        for _ in range(retries):
            try:
                files = msa_base._download_targz(
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


        self.msa = msa_base.MSAResult()
        self.msa.m8_data = self.extracted_files["pdb70.m8"]
        self.uses_templates = self.use_templates
        self.uses_pairing = self.pairing is not None

        if self.use_templates:
            self._query_templates()

        self._extract_a3m() 

        return self.msa

    def _query_templates(self):
        templates = {}
        for line in open(self.msa.m8_data):
            if line.startswith("#"):
                continue
            p = line.rstrip().split()
            if len(p) == 0:
                continue
            M, pdb, qid, e_value = p[0], p[1], p[2], p[10]
            M = int(M)
            if M not in templates:
                templates[M] = []
            templates[M].append(pdb)

        template_files = {}
        for M, pdbs in templates.items():
            subdir = os.path.join(self._download_location, f"templates_{M}")
            os.makedirs(subdir, exist_ok=True)
            query = set(i.split("_")[0] for i in pdbs[:20])
            pdb_query_line = ",".join(set(i for i in pdbs[:20]))
            url = f"{REMOTE_URL}/template/{pdb_query_line}"
            files = msa_base._download_targz(
                url,
                [f"{i}.cif" for i in query] + ["pdb70_a3m.ffindex", "pdb70_a3m.ffdata"],
                get_kws={"headers": self.headers},
                dest=subdir,
            )
            for i, j in files.items():
                if j is None:
                    raise FileNotFoundError(f"Could not extract {i}")
            template_files[M] = files
            if not os.path.exists(f"{subdir}/pdb70_cs219.ffindex"):
                os.symlink(files["pdb70_a3m.ffindex"], f"{subdir}/pdb70_cs219.ffindex")
                open(f"{subdir}/pdb70_cs219.ffdata", "w").close()

        self.msa.template_data = template_files


    def _extract_a3m(self):
        a3m_files = (j for i, j in self.extracted_files.items() if i.endswith(".a3m")) 
        a3m_lines = {}
        for a3m_file in a3m_files:
            update_M, M = True, None
            for line in open(a3m_file,"r"):
                if len(line) > 0:
                    if "\x00" in line:
                        line = line.replace("\x00","")
                        update_M = True
                if line.startswith(">") and update_M:
                    M = int(line[1:].rstrip())
                    update_M = False
                    if M not in a3m_lines: 
                        a3m_lines[M] = []
                a3m_lines[M].append(line)

        a3m_lines = ["".join(a3m_lines[i]) for i in self._sequence_indices]
        self.msa.a3m_data = a3m_lines