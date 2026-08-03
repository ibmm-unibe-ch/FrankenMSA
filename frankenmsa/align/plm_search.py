"""
PLM-Search client for finding similar protein sequences.

This module provides a class that wraps the PLM-Search API following
the `MSAFactory` interface defined in `base.py`.

References:
    https://dmiip.sjtu.edu.cn/PLMSearch
"""

from pathlib import Path
import time
from typing import List, Optional

import requests
import pandas as pd

from . import base
from ..runtime import log_message
from ..utils.uniprot import fetch_uniprot_metadata

# PLM-Search API endpoints and configuration
PLM_SEARCH_BASE_URL = "https://dmiip.sjtu.edu.cn/PLMSearch"
PLM_SEARCH_SUBMIT_URL = f"{PLM_SEARCH_BASE_URL}/submit/"
PLM_SEARCH_REFRESH_URL_TEMPLATE = f"{PLM_SEARCH_BASE_URL}/refresh/{{query_id}}"
PLM_SEARCH_DOWNLOAD_URL_TEMPLATE = f"{PLM_SEARCH_BASE_URL}/{{query_id}}/similarity.txt"

# Multipart form data boundary
MULTIPART_BOUNDARY = "------geckoformboundary4aeca06a4428bd98875a0a9648782b8"

# HTTP headers for API requests
REQUEST_HEADERS = {
    #    "Referer": "https://github.com/ibmm-unibe-ch/FrankenMSA/",
    #    "Content-Type": f"multipart/form-data; boundary={MULTIPART_BOUNDARY}",
    "Host": "dmiip.sjtu.edu.cn",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": f"multipart/form-data; boundary={MULTIPART_BOUNDARY}",
    "Origin": "https://dmiip.sjtu.edu.cn",
    "Connection": "keep-alive",
    "Referer": "https://dmiip.sjtu.edu.cn/PLMSearch",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
}

# API constants
DEFAULT_POLL_INTERVAL_SECONDS = 5
MAX_RETRIES = 10
CHUNK_SIZE = 8192
BATCH_SIZE_UNIPROT = 100


def download_with_resume(
    session: requests.Session, url: str, max_retries: int = MAX_RETRIES
) -> bytes:
    """
    Download file content with automatic resume on connection errors.

    PLM-Search may close connections prematurely. This function implements
    a simple resume-capable downloader that retries and resumes from the
    last successfully downloaded byte.

    References:
        https://stackoverflow.com/questions/77873658/python-reading-url-chunkedencodingerror

    Parameters
    ----------
    session : requests.Session
        Active requests session for HTTP communication.
    url : str
        URL to download from.
    max_retries : int, optional
        Maximum number of retry attempts (default: 10).

    Returns
    -------
    bytes
        Complete file content.

    Raises
    ------
    ValueError
        If download cannot be completed after max retries or if response
        status code is unexpected.
    """
    data = b""
    expected_length = None

    for attempt in range(max_retries):
        # Check if download is complete
        if len(data) == expected_length:
            break

        # Prepare headers for resuming or starting fresh
        if len(data):
            headers = {"Range": f"bytes={len(data)}-"}
            expected_status = 206
        else:
            headers = {}
            expected_status = 200

        # Perform request
        try:
            resp = session.get(url, stream=True, headers=headers)
            resp.raise_for_status()

            if resp.status_code != expected_status:
                raise ValueError(
                    f"Unexpected HTTP status: {resp.status_code} "
                    f"(expected {expected_status})"
                )

            # Extract expected total length on first request
            if expected_length is None:
                content_length = resp.headers.get("Content-Length")
                if not content_length:
                    raise ValueError("Content-Length header missing in response")
                expected_length = int(content_length)

            # Download chunk by chunk
            try:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    data += chunk
            except requests.exceptions.ChunkedEncodingError as e:
                # Continue to retry loop
                pass

        except requests.exceptions.RequestException as e:
            time.sleep(1)  # Brief delay before retry

    # Final validation
    if len(data) != expected_length:
        raise ValueError(
            f"Download incomplete: expected {expected_length} bytes, "
            f"got {len(data)} bytes after {max_retries} attempts"
        )

    return data


class PLMSearch(base.MSAFactory):
    """
    PLM-Search client for finding similar protein sequences.

    This class provides an interface to the PLM-Search remote service
    (https://dmiip.sjtu.edu.cn/PLMSearch), which uses protein language models
    to find similar sequences in various protein databases.

    The `align` method follows the `MSAFactory` interface defined in `base.py`.

    Attributes
    ----------
    interval_seconds : int
        Wait interval (in seconds) between status polling requests.
    """

    def __init__(self, interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS):
        """
        Initialize PLM-Search client.

        Parameters
        ----------
        interval_seconds : int, optional
            Interval in seconds to wait between status checks (default: 5).
        """
        super().__init__()
        self.interval_seconds = interval_seconds

    def align(
        self,
        sequences: List[str],
        descriptions: Optional[List[str]] = None,
        database: str = "uniref50",
        similarity_cutoff: float = 0.9,
        max_sequences: int = 200,
        **kwargs,
    ) -> Optional[pd.DataFrame]:
        """
        Submit sequences to PLM-Search and retrieve similar sequences.

        Submits amino-acid sequences to the remote PLM-Search server,
        polls for completion, downloads results, and filters by similarity.
        UniProt metadata is fetched for matching sequences.

        Parameters
        ----------
        sequences : list of str
            Amino-acid sequences to query (e.g., ["MKTAYIAKQ", "AKVISR"]).
        descriptions : list of str, optional
            Sequence identifiers/names to include in submission.
            If None, numeric identifiers (seq1, seq2, ...) are generated.
        database : str, optional
            Target database for search (default: "uniref50").
            Options: "uniref50", "PDB", "Swiss-Prot".
            similarity_cutoff : float, optional
            Minimum similarity score to include in results (default: 0.3).
            Must be in range [0.0, 1.0].
        max_sequences : int, optional
            Maximum number of matching sequences to return per query
            (default: 200). The limit is applied per input sequence,
            not globally across all queries.
        **kwargs
            Optional runtime overrides. Supported key:
            - request_headers (dict): extra/override headers for the submit call.

        Returns
        -------
        pd.DataFrame or None
            DataFrame with columns ["header", "sequence", "query", ...] from
            UniProt metadata, or None if submission fails.
            One row per matching sequence. Returns empty DataFrame if no
            matches exceed similarity_cutoff.

        Raises
        ------
        ValueError
            If similarity_cutoff is outside valid range.
        """
        # Validate inputs
        if not (0.0 <= similarity_cutoff <= 1.0):
            raise ValueError(
                f"similarity_cutoff must be in [0.0, 1.0], got {similarity_cutoff}"
            )
        log_message(f"Starting PLM-Search alignment with {len(sequences)} input sequences against database '{database}'.")
        if descriptions is None:
            descriptions = [f"seq{i + 1}" for i in range(len(sequences))]

        if len(descriptions) != len(sequences):
            raise ValueError(
                f"Number of descriptions ({len(descriptions)}) must match "
                f"number of sequences ({len(sequences)})"
            )

        # 1. Submit query to API
        log_message(
            f"in file Submitting {len(sequences)} sequences to PLM-Search API with database '{database}' and similarity cutoff {similarity_cutoff}."
        )
        query_id = self._send_post_request(
            descriptions,
            sequences,
            database,
            request_headers=kwargs.get("request_headers"),
        )
        if not query_id:
            return None

        # 2. Download results file
        log_message(
            f"PLM-Search submission successful, received query ID: {query_id}. Polling for results..."
        )
        output_file = self._download_similarities(query_id)
        if not output_file:
            return None

        # 3. Parse results and fetch metadata
        log_message(
            f"Results downloaded to {output_file}. Parsing results and fetching UniProt metadata..."
        )
        try:
            df = self._parse_and_enrich_results(
                output_file, similarity_cutoff, max_sequences
            )
            self.msa = df
            log_message(
                f"PLM-Search alignment completed. Retrieved {len(df)} similar sequences after filtering by similarity cutoff."
            )
            return df
        except Exception as e:
            return None

    def _build_multipart_payload(
        self, descriptions: List[str], sequences: List[str], database: str
    ) -> str:
        """
        Build multipart form data payload for API submission.

        Parameters
        ----------
        descriptions : list of str
            Sequence identifiers.
        sequences : list of str
            Sequence data.
        database : str
            Target database name.

        Returns
        -------
        str
            Formatted multipart form data.
        """
        # Build FASTA section
        fasta_lines = []
        for desc, seq in zip(descriptions, sequences):
            fasta_lines.append(f">{desc}")
            fasta_lines.append(seq)
        fasta_content = "\r\n".join(fasta_lines)

        # Build complete payload
        parts = [
            f"--{MULTIPART_BOUNDARY}",
            'Content-Disposition: form-data; name="fasta"',
            "",
            fasta_content,
            f"--{MULTIPART_BOUNDARY}",
            'Content-Disposition: form-data; name="file"; filename=""',
            "Content-Type: application/octet-stream",
            "",
            "",
            f"--{MULTIPART_BOUNDARY}",
            'Content-Disposition: form-data; name="target_dataset"',
            "",
            database,
            f"--{MULTIPART_BOUNDARY}",
            'Content-Disposition: form-data; name="model"',
            "",
            "plmsearch",
            f"--{MULTIPART_BOUNDARY}--",
            "",
        ]

        return "\r\n".join(parts)

    def _send_post_request(
        self,
        descriptions: List[str],
        sequences: List[str],
        database: str,
        request_headers: Optional[dict] = None,
    ) -> Optional[str]:
        """
        Submit sequences to PLM-Search API.

        Parameters
        ----------
        descriptions : list of str
            Sequence identifiers.
        sequences : list of str
            Sequence data.
        database : str
            Target database name.

        Returns
        -------
        str or None
            Query ID if successful, None otherwise.
        """
        try:
            payload = self._build_multipart_payload(descriptions, sequences, database)
            headers = (
                REQUEST_HEADERS
                if request_headers is None
                else {**REQUEST_HEADERS, **request_headers}
            )

            response = requests.post(
                PLM_SEARCH_SUBMIT_URL, headers=headers, data=payload
            )
            response.raise_for_status()

            # Extract query ID from response
            # Response contains: ...https://dmiip.sjtu.edu.cn/PLMSearch/refresh/{QUERY_ID}"...
            try:
                query_id = response.text.split(f"{PLM_SEARCH_BASE_URL}/refresh/", 1)[
                    1
                ].split('"')[0]
                if not query_id:
                    raise ValueError("Empty query ID extracted")
                return query_id
            except (IndexError, ValueError) as e:
                return None

        except requests.exceptions.RequestException as e:
            log_message(f"An error occurred in PLMSearch: {e}")

    def _download_similarities(self, query_id: str) -> Optional[Path]:
        """
        Poll for completion and download similarity results.

        Periodically checks the query status via the refresh endpoint
        until completion, then downloads the similarity.txt file.

        Parameters
        ----------
        query_id : str
            Query identifier from API submission.

        Returns
        -------
        Path or None
            Path to downloaded similarity.txt file, or None if failed.
        """
        refresh_url = PLM_SEARCH_REFRESH_URL_TEMPLATE.format(query_id=query_id)
        download_url = PLM_SEARCH_DOWNLOAD_URL_TEMPLATE.format(query_id=query_id)
        output_file = Path(f"{query_id}_similarity.txt")
        # Poll until done
        max_wait_time = 3600  # 1 hour timeout
        elapsed = 0
        while elapsed < max_wait_time:
            try:
                response = requests.get(refresh_url, timeout=10)
                response.raise_for_status()

                if "Done" in response.text:
                    break

                time.sleep(self.interval_seconds)
                elapsed += self.interval_seconds

            except requests.exceptions.RequestException as e:
                time.sleep(self.interval_seconds)
                elapsed += self.interval_seconds

        if elapsed >= max_wait_time:
            return None

        # Download file with resume capability
        try:
            with requests.Session() as session:
                data = download_with_resume(session, download_url)
                with open(output_file, "wb") as f:
                    f.write(data)
                return output_file

        except Exception as e:
            return None

    def _parse_and_enrich_results(
        self, filepath: Path, similarity_cutoff: float, max_sequences: int
    ) -> pd.DataFrame:
        """
        Parse similarity file and enrich with UniProt metadata.

        Parameters
        ----------
        filepath : Path
            Path to similarity.txt file from API.
        similarity_cutoff : float
            Minimum similarity to include.

        Returns
        -------
        pd.DataFrame
            Enriched results with UniProt metadata.
        """
        # Parse similarity file
        df = pd.read_csv(filepath, sep="\t", names=["query", "response", "similarity"])

        # Keep only rows that meet similarity cutoff
        valid_df = df[df["similarity"] >= similarity_cutoff].copy()

        if valid_df.empty:
            return pd.DataFrame()

        # Enrich with UniProt metadata in batches, limiting results per query
        dfs = []
        for query in valid_df["query"].unique():
            group = (
                valid_df[valid_df["query"] == query]
                .sort_values(by="similarity", ascending=False)
                .head(max_sequences)
            )
            seqids = group["response"].tolist()

            for i in range(0, len(seqids), BATCH_SIZE_UNIPROT):
                batch = seqids[i : i + BATCH_SIZE_UNIPROT]
                metadata_df = fetch_uniprot_metadata(batch)
                metadata_df["query"] = query
                dfs.append(metadata_df)

        if not dfs:
            return pd.DataFrame()

        result = pd.concat(dfs, ignore_index=True)
        return result
