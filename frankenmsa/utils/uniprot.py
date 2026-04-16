import pandas as pd
import requests
import sys
import json

def fetch_uniprot_metadata(seqids) -> pd.DataFrame:
  response = requests.get("https://rest.uniprot.org/uniparc/search", headers={"accept": "application/json"}, params={'query': ' OR '.join(seqids),'fields': "sequence", "size": "500"})
  if not response.ok:
    response.raise_for_status()
    sys.exit()
  response_text = response.text
  df = make_dataframe_from_response_text(response_text)
  return df

def make_dataframe_from_response_text(response_text:str):
  response_json = json.loads(response_text)["results"]
  dikts = [{"header":entry["uniParcId"], "sequence":entry["sequence"]["value"]} for entry in response_json]
  return pd.DataFrame(dikts)

__all__ = [
    "fetch_uniprot_metadata",
    "make_dataframe_from_response_text",
]
