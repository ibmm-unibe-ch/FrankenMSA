import dash
from dash import html, dcc
from dash import callback, Input, Output, State
import dash_bootstrap_components as dbc
import base64, re
import os
from pathlib import Path
from helpers.constants import COLAB_LINK, ON_COLAB, UPLOAD_DIR

dash.register_page(
    __name__,
)


def layout():
    return html.Div(proteinmpnn_layout(), className="gradient-background")


def proteinmpnn_layout():
    options = dbc.Row(
        [
            dbc.Col(
                [
                    html.P("Sampling Temperature (higher values = more diversity)"),
                    html.Div(
                        dcc.Slider(
                            id="proteinmpnn-sampling-temperature",
                            min=0.1,
                            max=5.0,
                            step=0.1,
                            value=1.0,
                            marks={i / 10: str(i / 10) for i in range(10, 50, 10)},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                        style={"width": "100%", "marginTop": "13px"},
                    ),
                ],
                md=6,
            ),
            dbc.Col(
                [
                    html.P("Number of sequences to generate"),
                    dcc.Input(
                        id="proteinmpnn-sequence-count",
                        type="number",
                        value=128,
                        min=1,
                        max=5000,
                        step=1,
                        style={"width": "100%"},
                    ),
                ],
                md=6,
            ),
        ],
        className="g-2",
        style={
            "align-items": "center",
            "justify-content": "center",
            "marginTop": "6px",
            "marginBottom": "14px",
        },
    )

    # --- Structure input (moved out of Advanced) ---
    structure = html.Div(
        [
            html.Div(
                html.H5(
                    "Provide structure: upload a file or enter a PDB code",
                    style={
                        "textAlign": "center",
                        "fontWeight": 700,
                        "fontSize": "1.05rem",
                        "opacity": 0.9,
                        "margin": "6px 0 8px 0",
                    },
                ),
                style={"width": "100%"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Input(
                                id="proteinmpnn-pdb-code",
                                type="text",
                                value="",
                                placeholder="e.g., 2NNC",
                                className="input-component",
                                style={"width": "100%"},
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dcc.Upload(
                                id="pdb-upload",
                                children=html.Div(
                                    [html.Span("Click or drag & drop a .pdb/.cif file")]
                                ),
                                multiple=False,
                                accept=".pdb,.ent,.cif,.mmcif,.gz,.bz2,.txt",
                                style={
                                    "border": "1px dashed #bbb",
                                    "padding": "6px 10px",
                                    "marginTop": "6px",
                                    "textAlign": "center",
                                    "borderRadius": "8px",
                                    "opacity": 0.9,
                                    "cursor": "pointer",
                                    "minHeight": "40px",
                                    "width": "90%",
                                    "marginLeft": "auto",
                                    "marginRight": "auto",
                                    "backgroundColor": "rgba(255,255,255,0.35)",
                                },
                            ),
                            html.Small(
                                id="pdb-upload-status",
                                style={
                                    "display": "block",
                                    "marginTop": "6px",
                                    "opacity": 0.75,
                                },
                            ),
                            dcc.Store(id="pdb-upload-path", data=""),
                        ],
                        md=6,
                    ),
                ],
                className="g-2",
                style={"alignItems": "center"},
            ),
        ],
        style={"marginTop": "10px", "marginBottom": "8px"},
    )

    advanced = html.Div(
        [
            # Row A: Homomer toggle only (centered)
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        "Homomer (single chain)",
                                        style={
                                            "fontWeight": 500,
                                            "color": "#212529",
                                            "marginRight": "8px",
                                            "display": "inline-flex",
                                            "alignItems": "center",
                                            "lineHeight": "1.2",
                                        },
                                    ),
                                    dbc.Checkbox(
                                        id="proteinmpnn-homomer",
                                        value=True,
                                        className="mb-0",
                                        style={
                                            "display": "inline-block",
                                            "position": "relative",
                                            "top": "6px",
                                            "margin": 0,
                                        },
                                    ),
                                ],
                                style={
                                    "display": "inline-flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "gap": "8px",
                                    "marginBottom": "6px",
                                    "width": "100%",
                                    "textAlign": "center",
                                },
                            ),
                            # [DELETED] Removed the "Currently only homomers..." Small text here.
                        ],
                        md=12,
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "alignItems": "center",
                            "justifyContent": "center",
                        },
                    ),
                ],
                className="g-2",
                style={"alignItems": "center"},
            ),
            # Row B: Design / Fixed chains in two equal columns
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(
                                "Design chains (e.g., A or A,B)",
                                className="mb-1",
                                style={"fontWeight": 500},
                            ),
                            dcc.Input(
                                id="proteinmpnn-design-chains",
                                type="text",
                                value="",
                                placeholder="A or A,B",
                                className="input-component",
                                style={"width": "100%"},
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label(
                                "Fixed chains (optional)",
                                className="mb-1",
                                style={"fontWeight": 500},
                            ),
                            dcc.Input(
                                id="proteinmpnn-fixed-chains",
                                type="text",
                                value="",
                                placeholder="B or B,C",
                                className="input-component",
                                style={"width": "100%"},
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="g-2",
                style={"alignItems": "center", "marginBottom": "6px"},
            ),
        ],
        style={"paddingTop": "1px"},
    )

    advanced_collapse = html.Div(
        [
            html.Hr(style={"margin": "6px 0 12px 0"}),
            html.Div(
                html.Button(
                    "Chain options ▼",
                    id="toggle-advanced",
                    n_clicks=0,
                    style={
                        "background": "none",
                        "border": "none",
                        "fontWeight": 700,
                        "fontSize": "1.2rem",
                    },
                ),
                style={"textAlign": "center", "marginBottom": "10px"},
            ),
            dbc.Collapse(
                advanced,
                id="collapse-advanced",
                is_open=False,
                style={"overflow": "hidden"},
            ),
        ]
    )

    page_container = html.Div(
        [
            html.H1("Inverse Fold with ProteinMPNN"),
            html.Div(style={"height": "32px"}),
            html.P(
                [
                    "You can run inverse folding using ",
                    html.B("ProteinMPNN"),
                    " either on a ",
                    html.B("Google Colab GPU"),
                    " or on your own local machine. Set parameters here and click ",
                    html.B("Run ProteinMPNN"),
                    ". If you prefer running on Colab, open the Colab version via ",
                    html.A(
                        "this Colab link",
                        href=COLAB_LINK,
                        target="_blank",
                    ),
                    ". If you run FrankenMSA locally, ProteinMPNN will use your local environment instead.",
                    " Note: Both Homomers (single chain) and Heteromers (multi-chain complexes) are supported. ",
                ],
                style={"textAlign": "center", "marginBottom": "18px"},
            ),
            options,
            structure,
            advanced_collapse,
            html.Div(
                [
                    html.Button(
                        "Run ProteinMPNN",
                        id="open-proteinmpnn-colab",
                        n_clicks=0,
                        className="button-component",
                        style={"width": "100%", "fontWeight": 700},
                    ),
                    html.Div(
                        [
                            html.P(
                                "Job will run on the backend. Please wait here; when it finishes, a ZIP download link will appear below, and the generated A3M file will also automatically appear in the top-right file selector.",
                                style={"marginBottom": "4px"},
                            ),
                            html.Small(
                                [
                                    "Note: Large ProteinMPNN jobs may exceed the browser timeout. ",
                                    "If the loading spinner stops but no download link appears, please switch to a ",
                                    html.Span(
                                        "GPU runtime",
                                        style={"color": "#0b7285", "fontWeight": 600},
                                    ),
                                ],
                                style={
                                    "display": "block",
                                    "marginTop": "6px",
                                    "fontSize": "0.85rem",
                                    "opacity": 0.8,
                                },
                            ),
                        ],
                        style={
                            "marginTop": "10px",
                            "fontSize": "0.95rem",
                            "opacity": 0.9,
                        },
                    ),
                    # Visible status area (shows progress/errors/results)
                    dcc.Loading(
                        id="proteinmpnn-loading",
                        type="circle",
                        children=html.Div(
                            id="proteinmpnn-status",
                            style={
                                "marginTop": "14px",
                                "textAlign": "center",
                                "whiteSpace": "pre-wrap",
                            },
                        ),
                    ),
                    # Keep the hidden dummy div (not used anymore, but harmless)
                    html.Div(id="colab-launch-dummy", style={"display": "none"}),
                ],
                style={
                    "width": "56%",
                    "maxWidth": "620px",
                    "marginTop": "12px",
                    "margin": "20px auto",
                    "textAlign": "center",
                },
            ),
        ],
        style={"width": "80%", "maxWidth": "1000px"},
    )

    return html.Div(
        [page_container],
        style={"display": "flex", "justifyContent": "center", "width": "100%"},
    )


@callback(
    Output("collapse-advanced", "is_open"),
    Output("toggle-advanced", "children"),
    Input("toggle-advanced", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_advanced(n):
    if n and n % 2 == 1:
        return True, "Chain options ▲"
    return False, "Chain options ▼"


from dash.dependencies import (
    Input as _Input,
    Output as _Output,
    State as _State,
)  # ensure alias not required, but keep for clarity


# --- Removed old clientside_callback that opens Google Colab in a new tab ---


# --- Colab integration: directly run ProteinMPNN inside Colab environment ---
from dash import no_update
import os
from frankenmsa.inverse_fold import run_proteinmpnn


@callback(
    Output("pdb-upload-status", "children"),
    Output("pdb-upload-path", "data"),
    Input("pdb-upload", "contents"),
    State("pdb-upload", "filename"),
    prevent_initial_call=True,
)
def _save_uploaded_pdb(contents, filename):  # can be deleted?
    if not contents or not filename:
        return html.Small(""), ""
    try:
        # sanitize filename to a safe subset
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", filename)
        # ensure directory exists at runtime
        Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        out_path = os.path.join(UPLOAD_DIR, safe)

        # decode base64 payload and write file
        header, b64data = contents.split(",", 1)
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(b64data))

        exists = os.path.isfile(out_path)
        print(f"[UPLOAD] saved -> {out_path}, exists={exists}")  # diagnostic log
        if not exists:
            return html.Small("❌ Upload failed: file not found after save"), ""

        return html.Small(f"📄 Uploaded: {safe}"), out_path
    except Exception as e:
        print("[UPLOAD][ERROR]", e)
        return html.Small(f"❌ Upload failed: {e}"), ""


# Helper function: parse A3M to dict
def _parse_a3m_to_dict(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    headers, sequences = [], []
    current_header = None
    for l in lines:
        if l.startswith(">"):
            current_header = l[1:]
        elif current_header is not None:
            headers.append(current_header)
            sequences.append(l)
            current_header = None
    return {"header": headers, "sequence": sequences}


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("main-msa", "data", allow_duplicate=True),
    Output("inject-a3m", "data", allow_duplicate=True),
    Output("proteinmpnn-status", "children", allow_duplicate=True),
    Input("open-proteinmpnn-colab", "n_clicks"),
    State("proteinmpnn-sampling-temperature", "value"),
    State("proteinmpnn-sequence-count", "value"),
    State("proteinmpnn-design-chains", "value"),
    State("proteinmpnn-fixed-chains", "value"),
    State("proteinmpnn-homomer", "value"),
    State("proteinmpnn-pdb-code", "value"),
    State("pdb-upload-path", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_proteinmpnn_in_colab(
    n, temp, num, design, fixed, homomer_val, pdb, pdb_upload_path, msa_data_state
):
    if not n:
        return no_update, no_update, no_update, no_update

    uploaded_path = (pdb_upload_path or "").strip()
    code_clean = (pdb or "").strip().upper()
    use_uploaded = bool(uploaded_path) and os.path.isfile(uploaded_path)

    if not use_uploaded and not code_clean:
        return (
            no_update,
            no_update,
            no_update,
            html.Div("❌ Please provide a PDB code or upload a PDB/MMCIF file above."),
        )

    _path = uploaded_path
    is_homomer = bool(homomer_val)

    try:
        res = run_proteinmpnn(
            sampling_temp=(temp or 1.0),
            num_seqs=(num or 128),
            pdb_code=("" if use_uploaded else code_clean),
            pdb_path=_path,
            design_chains=(design or "").strip(),
            fixed_chains=(fixed or "").strip(),
            homomer=is_homomer,
            model_name="v_48_020",
            use_soluble_model=False,
            ca_only=False,
            clean_workspace=True,
            allow_upload=False,
            auto_download=False,
            runtime="colab" if ON_COLAB else "local",
        )
    except Exception as e:
        return no_update, no_update, no_update, html.Div(f"❌ Run failed: {e}")

    new_msa_data = no_update
    new_main_msa = no_update
    inject_payload = None

    try:
        # Only register split-chain MSAs in the GUI; keep the combined A3M
        # for the ZIP download but do not expose it as a separate MSA.
        current = msa_data_state if isinstance(msa_data_state, dict) else {}
        current = dict(current)

        split_map = res.get("split_chains", {})
        chain_names = []

        # Count how many chains ProteinMPNN detected
        num_chains = len(split_map)

        # Case 1: MULTIMER (2 or more chains) → only add split chains
        if num_chains > 1:
            for name, text in split_map.items():
                parsed_split = _parse_a3m_to_dict(text)
                current[name] = parsed_split
                chain_names.append(name)

            if chain_names and new_main_msa is no_update:
                new_main_msa = chain_names[0]

        # Case 2: MONOMER (0 or 1 chain) → keep combined chain instead
        else:
            # Combined A3M text/name from ProteinMPNN result
            combined_text = res.get("a3m_text")
            combined_name = res.get("a3m_name", "proteinmpnn_combined")

            if combined_text:
                parsed_combined = _parse_a3m_to_dict(combined_text)
                current[combined_name] = parsed_combined
                chain_names = [combined_name]

                if new_main_msa is no_update:
                    new_main_msa = combined_name

        new_msa_data = current

    except Exception as e:
        print(f"Error processing ProteinMPNN results: {e}")
        pass

    zip_name = os.path.basename(res["zip"])
    link = html.A(
        "⬇️ Download results (ZIP)",
        href=f"/colab/download/{zip_name}",
        target="_blank",
    )
    status_children = [html.Div("✅ ProteinMPNN finished."), link]
    if not ON_COLAB:
        status_children.append(
            html.Small(
                f"Stored at {res['zip']}",
                style={"display": "block", "marginTop": "6px", "opacity": 0.7},
            )
        )

    return (
        new_msa_data,
        new_main_msa,
        inject_payload,
        html.Div(status_children),
    )


# --- end Colab integration ---
