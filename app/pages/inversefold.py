import dash
from dash import html, dcc
from dash import callback, Input, Output, State, clientside_callback
import dash_bootstrap_components as dbc
from urllib.parse import urlencode
import time
import base64, re
import os
from pathlib import Path

# Local upload directory inside Colab backend
UPLOAD_DIR = "/content/ProteinMPNN/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    structure = html.Div([
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
        dbc.Row([
            dbc.Col([
                dcc.Input(
                    id="proteinmpnn-pdb-code",
                    type="text",
                    value="",
                    placeholder="e.g., 2NNC",
                    className="input-component",
                    style={"width": "100%"},
                ),
            ], md=6),
            dbc.Col([
                dcc.Upload(
                    id="pdb-upload",
                    children=html.Div([
                        html.Span("Click or drag & drop a .pdb/.cif file")
                    ]),
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
                html.Small(id="pdb-upload-status", style={"display": "block", "marginTop": "6px", "opacity": 0.75}),
                dcc.Store(id="pdb-upload-path", data=""),
            ], md=6),
        ], className="g-2", style={"alignItems": "center"}),
    ], style={"marginTop": "10px", "marginBottom": "8px"})

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
                            html.Small(
                                "Currently only homomers (single chain) are supported.",
                                className="text-muted",
                                style={
                                    "display": "block",
                                    "textAlign": "center",
                                    "marginTop": "4px",
                                },
                            ),
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
                            dbc.Label("Design chains (e.g., A or A,B)", className="mb-1", style={"fontWeight": 500}),
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
                            dbc.Label("Fixed chains (optional)", className="mb-1", style={"fontWeight": 500}),
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
        style={"paddingTop": "1px"}
    )

    advanced_collapse = html.Div([
        html.Hr(style={"margin": "6px 0 12px 0"}),
        html.Div(
            html.Button("Advanced (optional) ▼", id="toggle-advanced", n_clicks=0,
                        style={"background":"none","border":"none","fontWeight":700,"fontSize":"1.2rem"}),
            style={"textAlign":"center","marginBottom":"10px"}
        ),
        dbc.Collapse(
            advanced, 
            id="collapse-advanced", 
            is_open=False,
            style={"overflow": "hidden"}
        )
    ])

    page_container = html.Div(
        [
            html.H1("Inverse Fold with ProteinMPNN"),
            html.Div(style={"height": "32px"}),
            html.Div(
                dcc.Markdown(
                    "Run inverse folding using **ProteinMPNN** on a **Google Colab GPU**.\n"
                    "Set parameters here and click **Run ProteinMPNN** to start the job. A download link will appear when finished.\n"
                    "Note: currently FrankenMSA only supports homomers (single chain)."
                ),
                style={"marginBottom": "18px"}
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
                        "Job will run on the Colab backend. Please wait here; a ZIP download link will appear below when it finishes.",
                        style={"marginTop": "10px", "fontSize": "0.95rem", "opacity": 0.9}
                    ),
                    # Visible status area (shows progress/errors/results)
                    dcc.Loading(
                        id="proteinmpnn-loading",
                        type="circle",
                        children=html.Div(
                            id="proteinmpnn-status",
                            style={"marginTop": "14px", "textAlign": "left", "whiteSpace": "pre-wrap"}
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

    return html.Div([page_container], style={"display": "flex", "justifyContent": "center", "width": "100%"})


@callback(
    Output("collapse-advanced", "is_open"),
    Output("toggle-advanced", "children"),
    Input("toggle-advanced", "n_clicks"),
    prevent_initial_call=True
)

def toggle_advanced(n):
    if n and n % 2 == 1:
        return True, "Advanced (optional) ▲"
    return False, "Advanced (optional) ▼"


from dash.dependencies import Input as _Input, Output as _Output, State as _State  # ensure alias not required, but keep for clarity


# --- Removed old clientside_callback that opens Google Colab in a new tab ---


# --- Colab integration: directly run ProteinMPNN inside Colab environment ---
from dash import no_update
import urllib.parse, os

try:
    import colab_bridge  # Provided by Colab notebook (Cell 1)
except Exception:
    colab_bridge = None

@callback(
    Output("pdb-upload-status", "children"),
    Output("pdb-upload-path", "data"),
    Input("pdb-upload", "contents"),
    State("pdb-upload", "filename"),
    prevent_initial_call=True,
)
def _save_uploaded_pdb(contents, filename):
    if not contents or not filename:
        return html.Small(""), ""
    try:
        # sanitize filename to a safe subset
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", filename)
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


@callback(
    Output("proteinmpnn-status", "children", allow_duplicate=True),
    Input("open-proteinmpnn-colab", "n_clicks"),
    State("proteinmpnn-sampling-temperature", "value"),
    State("proteinmpnn-sequence-count", "value"),
    State("proteinmpnn-design-chains", "value"),
    State("proteinmpnn-fixed-chains", "value"),
    State("proteinmpnn-pdb-code", "value"),
    State("pdb-upload-path", "data"),
    prevent_initial_call=True,
)
def run_proteinmpnn_in_colab(n, temp, num, design, fixed, pdb, pdb_upload_path):
    if not n:
        return no_update
    if colab_bridge is None:
        return html.Div("❌ Colab bridge not available. Please start the Colab launcher notebook (Cell 1 & Cell 2) and refresh this page.")

    # Prefer uploaded file; consider it valid only if the path exists on backend
    uploaded_path = (pdb_upload_path or "").strip()
    code_clean = (pdb or "").strip().upper()
    use_uploaded = bool(uploaded_path) and os.path.isfile(uploaded_path)

    # Debug: print what we actually see before deciding
    print(f"[RUN-check] store_path='{uploaded_path}' exists={os.path.isfile(uploaded_path) if uploaded_path else None} code='{code_clean}'")

    if not use_uploaded and not code_clean:
        return html.Div("❌ Please provide a PDB code or upload a PDB/MMCIF file above.")

    qs = "?" + urllib.parse.urlencode({
        "temp": temp or 1.0,
        "num": num or 128,
        "design": (design or "").replace(" ", "").upper(),
        "fixed": (fixed or "").replace(" ", "").upper(),
        "pdb": (pdb or "").upper(),
        "homomer": 1,
    })

    # If user chose upload, we already validated existence above
    _path = uploaded_path

    try:
        params = colab_bridge.parse_params(qs)
        # Diagnostic: confirm what we are about to send to the runner
        print(
            "[RUN]",
            "code=", ("" if use_uploaded else code_clean),
            "pdb_path=", _path,
            "allow_upload=", False,
        )
        res = colab_bridge.run_proteinmpnn(
            sampling_temp=params.get("sampling_temp", 1.0),
            num_seqs=params.get("num_seqs", 128),
            pdb_code=("" if use_uploaded else code_clean),
            pdb_path=_path,
            design_csv=params.get("design_csv", ""),
            fixed_csv=params.get("fixed_csv", ""),
            homomer=params.get("homomer", True),
            model_name=params.get("model_name", "v_48_020"),
            use_soluble_model=params.get("use_soluble_model", False),
            ca_only=params.get("ca_only", False),
            clean_workspace=True,
            allow_upload=False,  # IMPORTANT: disable Colab files.upload(); use pdb_path instead when present
            auto_download=False,
        )
    except Exception as e:
        return html.Div(f"❌ Run failed: {e}")

    zip_name = os.path.basename(res["zip"])
    link = html.A("⬇️ Download results (ZIP)", href=f"/colab/download/{zip_name}", target="_blank")
    summary = html.Pre(str({
        "pdb": res["pdb_path"],
        "num_sequences": res["num_sequences"],
        "cuda_available": res["cuda_available"],
        "fasta": os.path.basename(res["fasta"]),
        "a3m": os.path.basename(res["a3m"]),
        "zip": os.path.basename(res["zip"]),
    }))
    input_info = html.Div(
        f"📁 Input file used: {res.get('pdb_path', '(none)')}",
        style={"marginTop": "4px", "opacity": 0.85}
    )
    return html.Div([
        html.Div("✅ ProteinMPNN finished."),
        input_info,
        link,
        summary
    ])
# --- end Colab integration ---