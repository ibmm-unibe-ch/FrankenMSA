import dash
import tempfile
from pathlib import Path
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from frankenmsa.utils.fileio import (
    build_multimer_csv,
    chain_label,
    combine_unpaired_a3m,
    is_multimer_a3m_text,
    split_dataframe_by_chain,
    split_multimer_a3m_file,
)

dash.register_page(
    __name__,
)


def layout():
    return html.Div(
        dbc.Row(
            [
                dbc.Col(file_upload_layout()),
                dbc.Col(html.Div([file_download_layout()])),
            ]
        ),
        className="gradient-background",
    )


# ================= Helper Functions =================


def file_upload_layout():

    upload_component = dcc.Upload(
        id="upload-data",
        children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
        className="upload-component",
        multiple=False,
        accept=".a3m,.fasta,.fa,.csv",
        max_size=52428800,
        style={"position": "relative", "zIndex": 10, "cursor": "pointer"},
    )

    return html.Div(
        [
            html.H1("Upload an existing MSA"),
            html.P(
                "You can upload an existing MSA file in the following formats: .fasta, .a3m, and .csv"
            ),
            upload_component,
            html.Div(
                id="upload-status",
                style={
                    "margin-top": "20px",
                    "textAlign": "center",
                },
            ),
        ],
        className="shaded-bordered",
    )


@callback(
    Output("upload-status", "children"),
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def upload_file(contents, filename, msa_data):
    if contents is None or not filename:
        return dash.no_update, dash.no_update, dash.no_update

    import base64, io, sys, traceback
    from pathlib import Path
    import pandas as pd
    from io import StringIO

    try:
        content_type, content_string = contents.split(",")
        decoded_bytes = base64.b64decode(content_string)
        decoded_text = io.BytesIO(decoded_bytes).read().decode("utf-8")
        suffix = Path(filename).suffix.lower()
        name = Path(filename).stem

        print(
            f"[UPLOAD] filename={filename} suffix={suffix} size={len(decoded_bytes)}",
            file=sys.stderr,
        )

        msa_data = {} if msa_data is None else msa_data

        # Check for multimer formats
        is_multimer = False
        chain_msas = {}

        if suffix in {".fasta", ".a3m", ".fa"}:
            # Check if it's a multimer A3M
            if is_multimer_a3m_text(decoded_text):
                print(f"[UPLOAD] Detected multimer A3M", file=sys.stderr)
                is_multimer = True

                with tempfile.NamedTemporaryFile(
                    suffix=".a3m", mode="w", encoding="utf-8", delete=False
                ) as tmp:
                    tmp_path = tmp.name
                    tmp.write(decoded_text)

                try:
                    chain_msas = split_multimer_a3m_file(tmp_path, name)
                except Exception as e:
                    print(
                        f"[UPLOAD] Failed to split multimer A3M: {e}", file=sys.stderr
                    )
                    traceback.print_exc()
                    # Fall back to regular parsing
                    is_multimer = False
                    from frankenmsa.utils import read_a3m

                    msa = read_a3m(tmp_path)
                finally:
                    Path(tmp_path).unlink(missing_ok=True)
            else:
                # Regular monomer A3M/FASTA
                from frankenmsa.utils import read_a3m

                with tempfile.NamedTemporaryFile(
                    suffix=".a3m", mode="w", encoding="utf-8", delete=False
                ) as tmp:
                    tmp_path = tmp.name
                    tmp.write(decoded_text)
                try:
                    msa = read_a3m(tmp_path)
                finally:
                    Path(tmp_path).unlink(missing_ok=True)

        elif suffix == ".csv":
            df = pd.read_csv(StringIO(decoded_text), header=0)

            if "sequence" not in df.columns:
                err = dcc.ConfirmDialog(
                    id="upload-error",
                    message="The uploaded CSV file does not contain a 'sequence' column.",
                    displayed=True,
                )
                return err, dash.no_update, dash.no_update

            # Check if it's a multimer CSV (has 'chain' column)
            if "chain" in df.columns:
                print(
                    f"[UPLOAD] Detected multimer CSV with chain column", file=sys.stderr
                )
                is_multimer = True

                try:
                    chain_msas = split_dataframe_by_chain(df, name)
                except Exception as e:
                    print(
                        f"[UPLOAD] Failed to split multimer CSV: {e}", file=sys.stderr
                    )
                    traceback.print_exc()
                    # Fall back to treating as regular CSV (without splitting)
                    is_multimer = False
                    msa = df
            else:
                # Regular monomer CSV
                msa = df

        else:
            err = dcc.ConfirmDialog(
                id="upload-error",
                message=f"Unsupported file format '{suffix}'. Please upload a .fasta, .a3m, or .csv file.",
                displayed=True,
            )
            return err, dash.no_update, dash.no_update

        # Handle multimer: add each chain separately to cache
        if is_multimer and chain_msas:
            # Clean up any existing entries with same base name
            keys_to_remove = [k for k in msa_data.keys() if k.startswith(name)]
            for k in keys_to_remove:
                msa_data.pop(k, None)

            # Add all chains
            total_entries = 0
            chain_names = []
            for chain_name, chain_df in chain_msas.items():
                msa_data[chain_name] = chain_df.to_dict("list")
                total_entries += len(chain_df)
                chain_names.append(chain_name)

            # Select the first chain
            first_chain = list(chain_msas.keys())[0] if chain_msas else name

            success_message = dcc.Markdown(
                f"""
                #### Multimer file uploaded successfully!
                Detected {len(chain_msas)} chains with {total_entries} total entries.
                
                Chains loaded: {', '.join(chain_names)}
                
                You can now use these chains individually and combine them again in the Export layout.
                """
            )
            return success_message, first_chain, msa_data

        # Handle regular monomer
        else:
            msa_length = len(msa)

            # Normalize key and drop duplicates that include extensions
            ext_variants = {
                Path(filename).name,
                f"{name}.a3m",
                f"{name}.fa",
                f"{name}.fasta",
                f"{name}.csv",
            }
            for k in list(msa_data.keys()):
                if k in ext_variants:
                    msa_data.pop(k, None)

            success_message = dcc.Markdown(
                f"""
                #### File uploaded successfully and MSA with {msa_length} entries loaded!
                You can now navigate to the other pages to perform operations on the MSA.
                """
            )
            msa_data[name] = msa.to_dict("list")
            return success_message, name, msa_data

    except Exception as e:
        print("[UPLOAD][ERROR]", repr(e), file=sys.stderr)
        traceback.print_exc()
        err = dcc.ConfirmDialog(
            id="upload-error",
            message=f"Failed to parse file '{filename}': {e.__class__.__name__}: {e}",
            displayed=True,
        )
        return err, dash.no_update, dash.no_update


def file_download_layout():

    download_format_options = [
        {"label": "A3M", "value": ".a3m"},
        {"label": "CSV", "value": ".csv"},
    ]
    download_format = dcc.Dropdown(
        id="download-format",
        options=download_format_options,
        value=".a3m",
        multi=False,
        clearable=False,
        persistence=True,
        persistence_type="memory",
        className="dropdown-component",
        style={"marginTop": "7px"},
    )

    # Single-select dropdown + add button (to support duplicates/homomers)
    msa_selector = dcc.Dropdown(
        id="download-msa-selector",
        options=[],
        multi=False,
        placeholder="Select an MSA",
        className="dropdown-component",
        style={"minWidth": "260px", "flex": 1},
    )

    add_button = html.Button(
        "Add to Export",
        id="add-chain-button",
        n_clicks=0,
        className="button-component",
        style={"marginLeft": "10px", "marginTop": "-30px"},
    )

    # Display selected chains
    chain_list_display = html.Div(
        id="chain-list-display",
        style={"marginTop": "10px", "marginBottom": "10px"},
    )

    # Hidden store for selected chains (list of MSA names in order)
    selected_chains_store = dcc.Store(
        id="selected-chains-store",
        data=[],
    )

    download_filename = dcc.Input(
        id="download-filename",
        type="text",
        placeholder="filename (auto-generated if blank)",
        style={"width": "65%", "marginRight": "12px"},
        className="input-component",
        persistence=True,
        persistence_type="memory",
    )

    download_component = dcc.Download(
        id="download-data",
    )

    status_div = html.Div(id="download-status", style={"marginTop": "10px"})

    available_formats = ", ".join(
        [option["label"] for option in download_format_options]
    )
    body = html.Div(
        [
            html.H1("Export MSA"),
            html.P(
                "Select an MSA and click 'Add to Export' to build your download. "
                "You can add multiple MSAs to create multimers."
            ),
            html.Div(
                [msa_selector, add_button],
                className="horizontal-align",
                style={
                    "marginTop": "10px",
                    "alignItems": "center",
                    "justifyContent": "center",
                },
            ),
            chain_list_display,
            html.Div(
                [
                    download_filename,
                    download_format,
                ],
                className="horizontal-align",
                style={
                    "marginTop": "10px",
                    "alignItems": "center",
                    "justifyContent": "center",
                },
            ),
            html.Button(
                "Download",
                id="download-button",
                n_clicks=0,
                className="button-component",
            ),
            download_component,
            selected_chains_store,
            status_div,
        ],
        className="shaded-bordered",
        style={"maxWidth": "700px", "margin": "0 auto"},
    )
    return body


@callback(
    Output("download-msa-selector", "options"),
    Input("msa-data", "data"),
)
def populate_download_options(msa_data):
    """Populate the MSA selector dropdown with available MSAs."""
    if not msa_data:
        return []
    keys = sorted(msa_data.keys())
    return [{"label": k, "value": k} for k in keys]


@callback(
    Output("selected-chains-store", "data"),
    Output("chain-list-display", "children"),
    Output("download-status", "children", allow_duplicate=True),
    Input("add-chain-button", "n_clicks"),
    Input({"type": "remove-chain", "index": dash.dependencies.ALL}, "n_clicks"),
    State("download-msa-selector", "value"),
    State("selected-chains-store", "data"),
    prevent_initial_call=True,
)
def manage_chain_list(add_clicks, remove_clicks, selected_msa, current_chains):
    """Add or remove chains from the multimer list."""

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]["prop_id"]

    # Handle adding a chain
    if "add-chain-button" in trigger_id:
        if not selected_msa:
            toast = dbc.Toast(
                "Please select an MSA first.",
                header="Warning",
                icon="warning",
                duration=3000,
                is_open=True,
            )
            return dash.no_update, dash.no_update, toast

        current_chains = current_chains or []
        current_chains.append(selected_msa)

    # Handle removing a chain
    elif "remove-chain" in trigger_id:
        import json

        button_id = json.loads(trigger_id.split(".")[0])
        index = button_id["index"]

        current_chains = current_chains or []
        if 0 <= index < len(current_chains):
            current_chains.pop(index)

    # Build display
    if not current_chains:
        display = html.P(
            "No chains added yet.", style={"fontStyle": "italic", "color": "gray"}
        )
    else:
        chain_items = []
        for i, msa_name in enumerate(current_chains):
            chain_label_value = chain_label(i)
            chain_items.append(
                html.Div(
                    [
                        html.Span(
                            f"Chain {chain_label_value}: {msa_name}",
                            style={"marginRight": "10px"},
                        ),
                        html.Button(
                            "×",
                            id={"type": "remove-chain", "index": i},
                            n_clicks=0,
                            style={
                                "background": "#dc3545",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "3px",
                                "cursor": "pointer",
                                "fontSize": "16px",
                                "padding": "2px 8px",
                            },
                        ),
                    ],
                    style={
                        "marginBottom": "5px",
                        "display": "flex",
                        "alignItems": "center",
                    },
                )
            )
        display = html.Div(chain_items)

    return current_chains, display, ""


@callback(
    Output("download-data", "data"),
    Output("download-status", "children", allow_duplicate=True),
    Input("download-button", "n_clicks"),
    State("selected-chains-store", "data"),
    State("msa-data", "data"),
    State("download-format", "value"),
    State("download-filename", "value"),
    prevent_initial_call=True,
)
def download_file(n_clicks, selected_msas, msa_data, format_ext, filename):
    """
    Smart download handler that creates either monomer or multimer downloads
    based on the number of selected MSAs.
    """
    if not n_clicks:
        return None, ""

    import sys

    # Validation
    if not msa_data:
        toast = dbc.Toast(
            "No MSA data available.",
            header="Error",
            icon="danger",
            duration=4000,
            is_open=True,
        )
        return dash.no_update, toast

    if not selected_msas or len(selected_msas) == 0:
        toast = dbc.Toast(
            "Please add at least one chain to download.",
            header="Error",
            icon="danger",
            duration=4000,
            is_open=True,
        )
        return dash.no_update, toast

    try:
        # Single MSA download (monomer)
        if len(selected_msas) == 1:
            return _download_single_msa(
                selected_msas[0], msa_data, format_ext, filename
            )

        # Multiple MSA download (multimer)
        else:
            return _download_multimer(selected_msas, msa_data, format_ext, filename)

    except Exception as e:
        print(f"[DOWNLOAD][ERROR] {repr(e)}", file=sys.stderr)
        import traceback

        traceback.print_exc()

        toast = dbc.Toast(
            f"Download failed: {e.__class__.__name__}: {str(e)}",
            header="Error",
            icon="danger",
            duration=6000,
            is_open=True,
        )
        return dash.no_update, toast


def _download_single_msa(msa_name, msa_data, format_ext, filename):
    """Download a single MSA (monomer)."""
    import os, re, tempfile
    import pandas as pd

    df = pd.DataFrame(msa_data[msa_name])

    # Build safe base name
    base = (filename or msa_name).strip()
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base) or "msa"

    # Decide extension and writer
    if format_ext == ".a3m":
        from frankenmsa.utils import write_a3m as writer
    elif format_ext == ".csv":
        writer = None
    else:
        raise ValueError(f"Invalid file format: {format_ext}")

    tmp_dir = tempfile.gettempdir()
    out_path = os.path.join(tmp_dir, base + format_ext)

    if writer is not None:
        writer(df, out_path)
    else:
        df.to_csv(out_path, index=False)

    toast = dbc.Toast(
        f"Downloading {msa_name} as {base}{format_ext}",
        header="Success",
        icon="success",
        duration=3000,
        is_open=True,
    )
    return dcc.send_file(out_path), toast


def _download_multimer(selected_msas, msa_data, format_ext, filename):
    """Download multiple MSAs as a multimer."""
    import os, re, tempfile, sys
    import pandas as pd
    from pathlib import Path

    # Generate default filename if not provided
    if not filename or not filename.strip():
        # Create filename from MSA names with chain labels
        # e.g., ["msa1", "msa1", "msa2"] -> "msa1_A_msa1_B_msa2_C"
        parts = []
        for i, msa_name in enumerate(selected_msas):
            chain_label_value = chain_label(i)
            parts.append(f"{msa_name}{chain_label_value}")
        base = "_".join(parts)
    else:
        base = filename.strip()

    # Sanitize filename
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base) or "multimer"

    if format_ext == ".csv":
        # CSV multimer: combine with chain column
        combined_df = build_multimer_csv(msa_data, selected_msas)

        tmp_dir = tempfile.gettempdir()
        out_path = os.path.join(tmp_dir, base + ".csv")
        combined_df.to_csv(out_path, index=False)

        chain_list = [chain_label(i) for i in range(len(selected_msas))]
        toast = dbc.Toast(
            f"Downloading multimer CSV with {len(selected_msas)} chains: {', '.join(chain_list)}",
            header="Success",
            icon="success",
            duration=4000,
            is_open=True,
        )
        return dcc.send_file(out_path), toast

    elif format_ext == ".a3m":
        # A3M multimer: use combine_unpaired_a3m
        from frankenmsa.utils import write_a3m

        # Create temp directory for intermediate files
        tmpdir = Path(tempfile.gettempdir()) / "frankenmsa"
        tmpdir.mkdir(parents=True, exist_ok=True)

        # Write each selected MSA to a temp file (preserving order and duplicates)
        in_paths = []
        for idx, msa_name in enumerate(selected_msas):
            df_i = pd.DataFrame(msa_data[msa_name])
            # Use unique temp filenames to handle duplicates
            p = tmpdir / f"chain_{idx}_{msa_name}.a3m"
            write_a3m(df_i, str(p))
            if not p.is_file():
                raise IOError(f"Failed to write temporary file: {p}")
            in_paths.append(str(p))

        # Build output path
        out_path = tmpdir / (base + format_ext)

        print(f"[MULTIMER][DEBUG] tmpdir={tmpdir}", file=sys.stderr)
        print(f"[MULTIMER][DEBUG] in_paths={in_paths}", file=sys.stderr)
        print(f"[MULTIMER][DEBUG] out_path={out_path}", file=sys.stderr)

        # Combine into multimer A3M
        combine_unpaired_a3m(in_paths, str(out_path))

        chain_list = [chain_label(i) for i in range(len(selected_msas))]
        toast = dbc.Toast(
            f"Downloading multimer A3M with {len(selected_msas)} chains: {', '.join(chain_list)}",
            header="Success",
            icon="success",
            duration=4000,
            is_open=True,
        )
        return dcc.send_file(str(out_path)), toast

    else:
        raise ValueError(f"Invalid file format: {format_ext}")


# Register injected A3M (from InverseFold) as if uploaded by user; also trigger on page load
@callback(
    Output("upload-status", "children", allow_duplicate=True),
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Output("inject-a3m", "data", allow_duplicate=True),  # clear after consume
    Input("inject-a3m", "data"),
    Input("url", "pathname"),  # fire when navigating to this page
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def register_injected_a3m(injected, _pathname, msa_data):
    import sys, traceback, tempfile, os
    from pathlib import Path

    # Only proceed when there is injected content
    if not injected or not injected.get("text"):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    try:
        raw_name = injected.get("name") or "mpnn.a3m"
        name = Path(raw_name).stem or "mpnn"

        msa_data = {} if msa_data is None else msa_data

        # Deduplicate possible variants (with extensions) before insert
        ext_variants = {
            raw_name,
            f"{name}.a3m",
            f"{name}.fa",
            f"{name}.fasta",
            f"{name}.csv",
        }
        for k in list(msa_data.keys()):
            if k in ext_variants and k != name:
                msa_data.pop(k, None)

        # If already present, just switch selection and clear the store
        if name in msa_data:
            success_message = dcc.Markdown(
                f"#### A3M '{name}.a3m' already available. Selected it for you."
            )
            return success_message, name, msa_data, None

        # Materialize text into a temp file and parse via existing reader
        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, f"{name}.a3m")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(injected["text"])

        from frankenmsa.utils import read_a3m

        msa = read_a3m(tmp_path)
        msa_length = len(msa)

        # Merge into store and select it
        msa_data[name] = msa.to_dict("list")
        success_message = dcc.Markdown(
            f"#### Registered A3M '{name}.a3m' from ProteinMPNN with {msa_length} entries."
        )

        # Clear inject store after consuming to avoid re-processing
        return success_message, name, msa_data, None

    except Exception as e:
        print("[INJECT][ERROR]", repr(e), file=sys.stderr)
        traceback.print_exc()
        err = dcc.ConfirmDialog(
            id="upload-error",
            message=f"Failed to register injected A3M '{injected.get('name','')}': {e.__class__.__name__}: {e}",
            displayed=True,
        )
        return err, dash.no_update, dash.no_update, dash.no_update
