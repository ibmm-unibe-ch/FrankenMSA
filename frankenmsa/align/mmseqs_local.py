import requests
import time
import pandas as pd
import tarfile
from io import BytesIO

from frankenmsa.runtime import log_message

# =============================================================================
#  Local Backend Logic
# =============================================================================

class LocalMMSeqs2Colab:
    """
    Lightweight ColabFold API client for multimer pairing MSA generation.

    Unlike the full MMSeqs2Colab class this is intentionally minimal: it speaks
    directly to the ColabFold pair endpoint and returns a (df, header_line,
    lengths) tuple consumed by the multimer alignment workflow in the app.
    """

    def __init__(self):
        self.base_url = "https://api.colabfold.com"

    def align(self, sequence_str, pairing_mode):
        lengths = []
        header_line = None
        
        if ":" in sequence_str:
            parts = sequence_str.split(":")
            lengths = [len(p.strip()) for p in parts if p.strip()]
            cardinalities = ["1"] * len(lengths)
            header_line = f"#{','.join(map(str, lengths))}\t{','.join(cardinalities)}"
        else:
            lengths = [len(sequence_str.strip())]
            header_line = None

        query = f">101\n{sequence_str}\n"
        
        if pairing_mode == "greedy":
            api_mode = "pairgreedy"
        elif pairing_mode == "complete":
            api_mode = "paircomplete"
        else:
            api_mode = "pairgreedy"

        log_message(f"Submitting multimer pair request to ColabFold API (mode={api_mode}).")

        post_url = f"{self.base_url}/ticket/pair"
        data = {"q": query, "mode": api_mode}

        resp = requests.post(post_url, data=data)
        resp.raise_for_status()
        job_id = resp.json()['id']
        log_message(f"ColabFold job submitted (id={job_id}).")

        status = "PENDING"
        while status in ["PENDING", "RUNNING"]:
            time.sleep(3)
            status_resp = requests.get(f"{self.base_url}/ticket/{job_id}")
            status_resp.raise_for_status()
            status = status_resp.json()['status']
            log_message(f"ColabFold job status: {status}")
        
        if status == "ERROR":
            raise RuntimeError("ColabFold API returned ERROR status.")

        download_url = f"{self.base_url}/result/download/{job_id}"
        log_message(f"Downloading ColabFold results from {download_url}.")
        
        res = requests.get(download_url)
        res.raise_for_status()

        final_df = pd.DataFrame()
        
        with tarfile.open(fileobj=BytesIO(res.content), mode="r:gz") as tar:
            found = False
            for member in tar.getmembers():
                if "pair.a3m" in member.name:
                    found = True
                    f = tar.extractfile(member)
                    content = f.read().decode("utf-8")
                    
                    headers = []
                    seqs = []
                    
                    current_header = None
                    current_seq = []
                    
                    for line in content.splitlines():
                        line = line.strip()
                        if not line: continue
                        if line.startswith("#"): continue
                        
                        if line.startswith(">"):
                            if current_header:
                                headers.append(current_header)
                                seqs.append("".join(current_seq))
                            current_header = line.lstrip(">")
                            current_seq = []
                        else:
                            current_seq.append(line)
                    
                    if current_header:
                        headers.append(current_header)
                        seqs.append("".join(current_seq))
                        
                    if len(lengths) > 1 and len(headers) > 0:
                        new_ids = [str(101 + i) for i in range(len(lengths))]
                        headers[0] = "\t".join(new_ids)

                    final_df = pd.DataFrame({"header": headers, "sequence": seqs})
                    break
            
            if not found:
                raise RuntimeError("ColabFold API finished but pair.a3m was not found in the result.")

        return final_df, header_line, lengths
