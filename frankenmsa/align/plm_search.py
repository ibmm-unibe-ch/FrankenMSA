"""
Simple PLM-Search client wrapped as an MSAFactory-compatible class.

This module adapts the code from a notebook into a class that follows
the `MSAFactory` interface in `base.py`.
"""
from pathlib import Path
import time
from typing import List, Optional

import requests
import pandas as pd

from . import base
from ..utils import uniprot

PLM_SEARCH_URL = "https://dmiip.sjtu.edu.cn/PLMSearch/submit/"
BOUNDARY = (
    "------geckoformboundary72c107c29309639fa4b1520bc6e35692"
)
HEADERS = {
    "Referer": 'https://github.com/ibmm-unibe-ch/FrankenMSA/',
    "Content-Type": 'multipart/form-data; boundary=----geckoformboundary72c107c29309639fa4b1520bc6e35692',
}

def download_with_resume(sess: requests.Session, url: str) -> bytes:
    #PLM-Search might close connections prematurely, so StackOverflow implemented a simple resume-capable downloader.
    # https://stackoverflow.com/questions/77873658/python-reading-url-chunkedencodingerror
    data = b""
    expected_length = None
    for attempt in range(10):
        if len(data) == expected_length:
            break
        if len(data):
            headers = {"Range": f"bytes={len(data)}-"}
            expected_status = 206
        else:
            headers = {}
            expected_status = 200
        #print(f"{url}: got {len(data)} / {expected_length} bytes...")
        resp = sess.get(url, stream=True, headers=headers)
        resp.raise_for_status()
        if resp.status_code != expected_status:
            raise ValueError(f"Unexpected status code: {resp.status_code}")
        if expected_length is None:  # Only update this on the first request
            content_length = resp.headers.get("Content-Length")
            if not content_length:
                raise ValueError("Content-Length header not found")
            expected_length = int(content_length)

        try:
            for chunk in resp.iter_content(chunk_size=8192):
                data += chunk
        except requests.exceptions.ChunkedEncodingError:
            pass

    if len(data) != expected_length:
        raise ValueError(f"Expected {expected_length} bytes, got {len(data)}")

    return data


class PLMSearch(base.MSAFactory):
    """
    Minimal PLM-Search client exposing an `align` method.

    The `align` method will submit the sequences to the remote PLM-Search
    server, wait for results, download the similarity file and return a
    pandas.DataFrame with responses filtered by `similarity_cutoff`.
    """

    def __init__(self, interval_seconds: int = 5):
        super().__init__()
        self.interval_seconds = interval_seconds

    def align(
        self,
        sequences: List[str],
        descriptions: Optional[List[str]] = None,
        database: str = "uniref50",
        similarity_cutoff: float = 0.3,
    ) -> Optional[pd.DataFrame]:
        """
        Submit sequences and return similarity results as a DataFrame.

        Parameters
        ----------
        sequences: list of str
            Amino-acid sequences to query.
        descriptions: list of str, optional
            Sequence descriptions/IDs to include in the fasta payload.
            If omitted, numeric IDs will be generated.
        database: str
            Target dataset name for the server.
        similarity_cutoff: float
            Minimum similarity threshold to keep rows.

        Returns
        -------
        pd.DataFrame or None
            Filtered DataFrame containing columns `query`, `response`,
            `similarity` and `response_sequence`, or `None` on failure.
        """
        if descriptions is None:
            descriptions = [f"seq{i+1}" for i in range(len(sequences))]

        query_id = self._send_post_request(descriptions, sequences, database)
        if not query_id:
            return None

        filename = self._download_similarities(query_id)
        with open("test.txt", "a") as myfile:
            myfile.write(f"filename: {filename}\n")
        if not filename:
            return None

        df = self._make_results(Path(filename), similarity_cutoff)
        self.msa = df
        return df

    def _send_post_request(self, descriptions: List[str], sequences: List[str], database: str = "uniref50") -> Optional[str]:
        sequence_data = ""
        for description, sequence in zip(descriptions, sequences):
            sequence_data = f"{sequence_data}\r\n>{description}\r\n{sequence}"
        data =f"{BOUNDARY}\r\nContent-Disposition: form-data; name=\"fasta\"\r\n{sequence_data}\r\n{BOUNDARY}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n{BOUNDARY}\r\nContent-Disposition: form-data; name=\"target_dataset\"\r\n\r\n{database}\r\n{BOUNDARY}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nplmsearch\r\n{BOUNDARY}--\r\n"   
        try:
            response = requests.post(PLM_SEARCH_URL, headers=HEADERS, data=data)
            response.raise_for_status()
            # extract query id from response body
            query_id = response.text.split("https://dmiip.sjtu.edu.cn/PLMSearch/refresh/", 1)[1].split('"')[0]
            return query_id
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

    def _download_similarities(self, query_id: str) -> Optional[Path]:
        refresh_url = f"https://dmiip.sjtu.edu.cn/PLMSearch/refresh/{query_id}"
        download_url = f"https://dmiip.sjtu.edu.cn/PLMSearch/{query_id}/similarity.txt"
        output_filename = Path(f"{query_id}_similarity.txt")
        waiting = True
        while waiting:
            try:
                response = requests.get(refresh_url)
                response.raise_for_status()
                if "Done" in response.text:
                    waiting = False
                else:
                    time.sleep(self.interval_seconds)
            except requests.exceptions.RequestException:
                time.sleep(self.interval_seconds)
            except Exception as e:
                print(f"An unexpected error occurred: {e}.")
        with open("test.txt", "a") as myfile:
            myfile.write(f"download {download_url}\n")
        with requests.Session() as sess:
            data = download_with_resume(sess,url=download_url)
            with open(output_filename, "wb") as f:
                f.write(data)
            return output_filename

    def _find_sequence(self, uniprot_id: str) -> str:
        with open("test.txt", "a") as myfile:
            myfile.write(f"uniprot_id {uniprot_id}\n")
        try:
            if uniprot_id.startswith("UPI00"):
                download_url = f"https://rest.uniprot.org/uniparc/{uniprot_id}.fasta"
            else:
                download_url = f"https://www.uniprot.org/uniprot/{uniprot_id}.fasta"
            response = requests.get(download_url)
            response.raise_for_status()
            return "".join(response.text.split("\n")[1:])
        except Exception as e:
            with open("test.txt", "a") as myfile:
                myfile.write(f"error {e}\n")
            return ""

    def _make_results(self, output_filepath: Path, similarity_cutoff: float = 0.3) -> pd.DataFrame:
        df = pd.read_csv(output_filepath, sep="\t", names=["query", "response", "similarity"])
        valid_df = df[df["similarity"] >= similarity_cutoff].copy()
        with open("test.txt", "a") as myfile:
            myfile.write(f"valid_df: {valid_df}")
        uniprot_out =  uniprot.fetch_uniprot_metadata(valid_df["response"].to_list())
        with open("test.txt", "a") as myfile:
            myfile.write(f"uniprot_out: {uniprot_out}")
        uniprot_df = pd.DataFrame([{"id":ide,"sequence":uniprot_out[ide]["sequence"] } for ide in uniprot_out.keys()] )
        with open("test.txt", "a") as myfile:
            myfile.write(f"uniprot_df: {uniprot_df}")
        valid_df = valid_df.merge(uniprot_df, left_on="response", right_on="id", how="left") 
        with open("test.txt", "a") as myfile:
            myfile.write(f"valid_df: {valid_df}")
        valid_df = valid_df[["query", "response", "sequence"]].rename(columns={"response": "header"})
        with open("test.txt", "a") as myfile:
            myfile.write(f"validated_df: {valid_df}")
        return valid_df