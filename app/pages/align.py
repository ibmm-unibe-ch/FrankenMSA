import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
import requests
import time
import pandas as pd
import tarfile
from io import BytesIO
import string

dash.register_page(
    __name__,
)

# =============================================================================
#  Local Backend Logic
# =============================================================================
class LocalMMSeqs2Colab:
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

        print(f"[DEBUG] Submitting to API. Mode: {api_mode}")

        post_url = f"{self.base_url}/ticket/pair"
        data = {"q": query, "mode": api_mode}

        resp = requests.post(post_url, data=data)
        resp.raise_for_status()
        job_id = resp.json()['id']
        print(f"[DEBUG] Job ID: {job_id}")

        status = "PENDING"
        while status in ["PENDING", "RUNNING"]:
            time.sleep(3)
            status_resp = requests.get(f"{self.base_url}/ticket/{job_id}")
            status_resp.raise_for_status()
            status = status_resp.json()['status']
            print(f"[DEBUG] Status: {status}")
        
        if status == "ERROR":
            raise Exception("ColabFold API returned ERROR status.")

        download_url = f"{self.base_url}/result/download/{job_id}"
        print(f"[DEBUG] Downloading from: {download_url}")
        
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
                 raise Exception("API finished but pair.a3m was not found in the result.")

        return final_df, header_line, lengths


# =============================================================================
#  UI Layout
# =============================================================================

def layout():
    return html.Div([mmseqs_colab_layout()], className="gradient-background")

def mmseqs_colab_layout():
    
    return html.Div(
        [
            # 1. Title
            html.H1("MMseqs2 ColabFold", style={"marginBottom": "10px"}),
            
            # 2. Citation Link
            html.Div([
                html.Span("Align one or more sequences using "),
                html.A("MMseqs2", href="https://www.nature.com/articles/s41467-018-04964-5", target="_blank"),
                html.Span("."),
            ], style={"marginBottom": "20px", "fontSize": "1.1rem"}),

            # 3. Instructions Section
            html.Div([
                html.Div([
                    dcc.Markdown(
                        """
                        * **Monomer:** Enter sequence. Select `Pairing: None`.
                        * **Multimer:** Join chains with `:` (e.g. `AAAA:BBBB`). Select `Pairing: Greedy` or `All`.
                        """,
                        style={"color": "#444", "lineHeight": "1.6"}
                    )
                ], style={"display": "inline-block", "textAlign": "left", "marginBottom": "5px"}),

                html.Details([
                    html.Summary("ℹ️ Click to learn about Pairing Modes (Greedy vs All)", style={"cursor": "pointer", "color": "#56CCF2", "fontSize": "0.9rem", "fontWeight": "500", "marginTop": "5px"}),
                    html.Div([
                        dcc.Markdown(
                            """
                            **Greedy (Strict):** Attempts to find the single best matching pair per species. *Warning: Often returns empty results on public servers.*
                            
                            **All (Recommended):** Finds all possible matching sequences per species. *Success rate is much higher.*
                            """,
                            style={"fontSize": "0.9rem", "color": "#555", "marginTop": "10px", "textAlign": "left", "maxWidth": "600px", "marginLeft": "auto", "marginRight": "auto", "lineHeight": "1.5"}
                        )
                    ])
                ])

            ], style={"textAlign": "center", "marginBottom": "20px"}),

            # 4. Input Area
            dcc.Textarea(
                id="mmseqs-input",
                placeholder="Enter sequences here...\n\nExample Multimer: AAAAA:BBBBB\nExample Monomer: AAAAA",
                style={
                    "width": "100%",
                    "padding": "15px",
                    "height": "120px",
                    "width": "80%",
                    "borderRadius": "8px",
                    "border": "1px solid #ccc",
                    "fontSize": "14px",
                    "fontFamily": "monospace"
                },
                className="input-component",
                persistence=True,
                persistence_type="memory",
            ),

            # 5. Options Row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P("Pairing mode", style={"fontWeight": "bold", "marginBottom": "10px"}),
                            dcc.RadioItems(
                                id="mmseqs-pairing-mode",
                                options=[
                                    {"label": "None (Monomer)", "value": "none"},
                                    {"label": "Greedy", "value": "greedy"},
                                    {"label": "All", "value": "complete"},
                                ],
                                value="none",
                                persistence=True,
                                persistence_type="memory",
                                inline=True,
                                inputStyle={"marginRight": "5px", "marginLeft": "10px"},
                                labelStyle={"marginRight": "15px"}
                            ),
                            html.Small(
                                [
                                    html.Span("💡 Tip: ", style={"color": "#56CCF2"}), 
                                    html.Strong("All", style={"color": "#444"}), 
                                    html.Span(" is recommended.", style={"color": "#666"}),
                                ],
                                style={"display": "block", "marginTop": "8px", "fontSize": "0.85rem"}
                            ),
                        ],
                        width=6, 
                        style={"textAlign": "center", "paddingRight": "20px"}
                    ),

                    dbc.Col(
                        [
                            html.P("Use Filtering", style={"fontWeight": "bold", "marginBottom": "10px"}),
                            dcc.RadioItems(
                                id="mmseqs-filter-mode",
                                options=[
                                    {"label": "Yes", "value": True},
                                    {"label": "No", "value": False},
                                ],
                                value=True,
                                persistence=True,
                                persistence_type="memory",
                                inline=True,
                                inputStyle={"marginRight": "5px", "marginLeft": "10px"},
                                labelStyle={"marginRight": "15px"}
                            ),
                            html.Small(
                                "Remove low-complexity regions.",
                                className="text-muted",
                                style={"display": "block", "marginTop": "8px", "fontSize": "0.85rem"}
                            ),
                        ],
                        width=6,
                        style={"textAlign": "center", "borderLeft": "1px solid #ddd", "paddingLeft": "20px"}
                    ),
                ],
                className="g-0", 
                style={
                    "marginTop": "30px", 
                    "marginBottom": "30px", 
                    "width": "80%",
                    "marginLeft": "auto",
                    "marginRight": "auto",
                    "alignItems": "start" 
                }
            ),

            # 6. Run Button
            html.Button(
                "Run MMseqs2",
                id="mmseqs-run-button",
                n_clicks=0,
                className="button-component",
                style={"width": "80%", "fontSize": "16px", "fontWeight": "bold", "padding": "12px"},
            ),

            # --- [NEW] Explanatory Text below button ---
            html.Div(
                html.Small(
                    "Output files (Main MSA + split chains) will be available in the file selector after computation.",
                    style={"color": "#888", "fontSize": "0.85rem"}
                ),
                style={"marginTop": "10px", "marginBottom": "5px"}
            ),
            
            # 7. Output / Status
            dcc.Loading(
                html.Div(id="mmseqs-output", className="output-component", style={"marginTop": "10px", "width": "80%", "marginLeft": "auto", "marginRight": "auto"}),
                type="dot",
                color="#333"
            ),
        ],
        style={"textAlign": "center", "paddingBottom": "50px"}
    )


# =============================================================================
#  Callback
# =============================================================================

@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Output("mmseqs-output", "children"),
    Input("mmseqs-run-button", "n_clicks"),
    State("mmseqs-input", "value"),
    State("mmseqs-pairing-mode", "value"),
    State("mmseqs-filter-mode", "value"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_mmseqs(n_clicks, input_data, pairing_mode, filter_mode, msa_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    if not input_data:
        return dash.no_update, dash.no_update, dbc.Alert("Please provide input data.", color="danger")

    # 1. Parse Input
    sequence_parts = []
    for line in input_data.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith(">"):
            continue
        sequence_parts.append(line)
    
    full_sequence = "".join(sequence_parts)
    full_sequence = "".join(full_sequence.split()).upper()

    if not full_sequence:
        return dash.no_update, dash.no_update, dbc.Alert("No valid sequences found.", color="danger")

    # 2. Validation
    is_multimer = ":" in full_sequence
    
    if is_multimer and pairing_mode == "none":
        return dash.no_update, dash.no_update, dbc.Alert(
            "Error: You have ':' in sequence but selected 'None'. Please select 'Greedy' or 'All'.", 
            color="danger"
        )
    if not is_multimer and pairing_mode != "none":
         return dash.no_update, dash.no_update, dbc.Alert(
            "Error: Single sequence provided but 'Greedy/All' selected. Please select 'None'.", 
            color="danger"
        )

    # 3. Execute API Call
    try:
        multimer_header_str = None
        chain_lengths = []
        
        if is_multimer:
            runner = LocalMMSeqs2Colab()
            msa_df, header_str, chain_lengths = runner.align(full_sequence, pairing_mode)
            multimer_header_str = header_str
            
            chains_count = full_sequence.count(":") + 1
            base_name = f"mmseqs_multimer_{chains_count}chains"
        
        else:
            from frankenmsa.align import MMSeqs2Colab
            runner = MMSeqs2Colab("frankenmsa-gui")
            msa_df = runner.align([full_sequence], True, filter_mode, None)
            base_name = "mmseqs"

        if not isinstance(msa_data, dict):
            msa_data = {}
            
        n_existing = sum(1 for i in msa_data.keys() if i.startswith(base_name) and "chain" not in i)
        new_main_key = f"{base_name}_{n_existing + 1}"
        
        # (A) Store Main MSA
        data_dict = msa_df.to_dict("list")
        if multimer_header_str:
            data_dict["_multimer_header"] = [multimer_header_str] * len(msa_df)
        
        msa_data[new_main_key] = data_dict
        
        # (B) Split Chains Logic
        split_msg = ""
        if is_multimer and chain_lengths:
            start = 0
            split_keys = []
            alphabet = string.ascii_uppercase
            
            for i, length in enumerate(chain_lengths):
                end = start + length
                chain_seqs = [s[start:end] for s in msa_df["sequence"]]
                
                # Rename Header for split file: >101 102 -> >101
                new_headers = list(msa_df["header"])
                if len(new_headers) > 0:
                    new_headers[0] = str(101 + i)
                
                chain_df = pd.DataFrame({
                    "header": new_headers, 
                    "sequence": chain_seqs
                })
                
                chain_suffix = alphabet[i] if i < 26 else str(i+1)
                split_key = f"{new_main_key}_chain{chain_suffix}"
                
                msa_data[split_key] = chain_df.to_dict("list")
                split_keys.append(split_key)
                start = end
            
            split_msg = f" Also generated split files: {', '.join(split_keys)}."

        msg = f"Success! Generated {new_main_key}.{split_msg}"
        return new_main_key, msa_data, dbc.Alert(msg, color="success")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return dash.no_update, dash.no_update, dbc.Alert(f"API Error: {str(e)}", color="danger")