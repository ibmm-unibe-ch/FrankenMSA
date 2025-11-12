import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State

dash.register_page(
    __name__,
)


def layout():
    return html.Div(
        dbc.Row(
            [
                dbc.Col(file_upload_layout()),
                dbc.Col(html.Div([file_download_layout(), multimer_builder_layout()])),
            ]
        ),
        className="gradient-background",
    )


def file_upload_layout():

    upload_component = dcc.Upload(
        id="upload-data",
        children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
        className="upload-component",
        multiple=False,
        accept=".a3m,.fasta,.fa,.csv",
        max_size=52428800,
        style={"position": "relative", "zIndex": 10, "cursor": "pointer"}
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
    Output("main-msa", "data"),
    Output("msa-data", "data"),
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

    try:
        content_type, content_string = contents.split(",")
        decoded_bytes = base64.b64decode(content_string)
        decoded_text = io.BytesIO(decoded_bytes).read().decode("utf-8")
        suffix = Path(filename).suffix.lower()

        print(f"[UPLOAD] filename={filename} suffix={suffix} size={len(decoded_bytes)}", file=sys.stderr)

        if suffix in {".fasta", ".a3m", ".fa"}:
            from frankenmsa.utils import read_a3m
            tmp_path = "temp_file.a3m"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(decoded_text)
            msa = read_a3m(tmp_path)
        elif suffix == ".csv":
            import pandas as pd
            from io import StringIO
            msa = pd.read_csv(StringIO(decoded_text), header=0)
            if "sequence" not in msa.columns:
                err = dcc.ConfirmDialog(
                    id="upload-error",
                    message="The uploaded CSV file does not contain a 'sequence' column.",
                    displayed=True,
                )
                return err, dash.no_update, dash.no_update
        else:
            err = dcc.ConfirmDialog(
                id="upload-error",
                message=f"Unsupported file format '{suffix}'. Please upload a .fasta, .a3m, or .csv file.",
                displayed=True,
            )
            return err, dash.no_update, dash.no_update

        msa_length = len(msa)
        name = Path(filename).stem

        # Normalize key and drop duplicates that include extensions
        ext_variants = {
            Path(filename).name,
            f"{name}.a3m",
            f"{name}.fa",
            f"{name}.fasta",
            f"{name}.csv",
        }
        msa_data = {} if msa_data is None else msa_data
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

    return dash.no_update, dash.no_update, dash.no_update


def file_download_layout():

    download_format_options = [
        {"label": "A3M", "value": ".a3m"},
        {"label": "FASTA", "value": ".fasta"},
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
    )
    download_filename = dcc.Input(
        id="download-filename",
        type="text",
        placeholder="filename (defaults to MSA name)",
        style={"width": "50%"},
        className="input-component",
        persistence=True,
        persistence_type="memory",
    )

    download_component = dcc.Download(
        id="download-data",
    )

    available_formats = ", ".join(
        [option["label"] for option in download_format_options]
    )
    body = html.Div(
        [
            html.H1("Download the generated MSA"),
            html.P(
                f"You can download the generated MSA file in the following formats: {available_formats}"
            ),
            html.Div(
                [
                    download_filename,
                    download_format,
                ],
                className="horizontal-align",
            ),
            html.Button(
                "Download MSA",
                id="download-button",
                n_clicks=0,
                className="button-component",  # "btn btn-primary",
            ),
            download_component,
        ],
        className="shaded-bordered",
    )
    return body


def _parse_a3m_simple(path: str):
    """
    Minimal A3M reader that also handles ColabFold multimer A3M.
    Returns a list of (header, sequence) tuples.
    It skips a leading '#' header line and concatenates wrapped sequence lines.
    """
    records = []
    header = None
    seq_buf = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line:
                continue
            if line.startswith("#"):
                # multimer header line like "#12,10\t1,1"
                # ignore, real sequences start at the first '>'
                continue
            if line.startswith(">"):
                if header is not None:
                    records.append((header, "".join(seq_buf)))
                header = line.strip()
                seq_buf = []
            else:
                seq_buf.append(line)
    if header is not None:
        records.append((header, "".join(seq_buf)))
    return records


def multimer_builder_layout():
    return html.Div(
        [
            html.H1("Build a multimer A3M"),
            html.P(
                "Select 2 or more MSAs (unpaired). The selection order defines chain order (A, B, C, …). We will generate a ColabFold multimer A3M.",
                style={"marginBottom": "8px"},
            ),
            dcc.Dropdown(
                id="multimer-chains",
                options=[],
                multi=True,
                placeholder="Pick 2+ MSAs in order (A, B, C, …)",
                className="dropdown-component",
                style={"width": "90%", "maxWidth": "680px", "margin": "0 auto"},
                persistence=True,
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Input(
                            id="multimer-name",
                            type="text",
                            placeholder="Output filename",
                            className="input-component",
                            style={"width": "100%", "maxWidth": "420px"},
                            persistence=True,
                        ),
                        md="auto",
                    ),
                    dbc.Col(
                        html.Button(
                            "Build Multimer",
                            id="multimer-build",
                            className="button-component",
                            style={"height": "42px", "padding": "0 16px"},
                        ),
                        md="auto",
                    ),
                ],
                className="g-2 justify-content-center align-items-center",
                style={"marginTop": "8px", "textAlign": "center"},
            ),
            html.Small(
                "Tip: If left blank, the filename will be auto-generated as <chain1>_<chain2>_... .a3m",
                className="text-muted",
                style={"display": "block", "marginTop": "6px"},
            ),
            html.Div(id="multimer-status"),
        ],
        className="shaded-bordered",
    )


@callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    State("download-format", "value"),
    State("download-filename", "value"),
)
def download_file(n_clicks, main_msa, msa_data, format, filename):
    if not n_clicks:
        return None

    import os, re, tempfile
    import pandas as pd

    if not msa_data or not main_msa:
        return dash.no_update

    df = pd.DataFrame(msa_data[main_msa])

    # build a safe base name
    base = (filename or str(main_msa)).strip()
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base) or "msa"

    # decide extension and writer
    if format == ".a3m":
        ext = ".a3m"
        from frankenmsa.utils import write_a3m as writer
    elif format == ".fasta":
        ext = ".fasta"
        from frankenmsa.utils import write_a3m as writer
    elif format == ".csv":
        ext = ".csv"
        writer = None
    else:
        raise ValueError("Invalid file format")

    tmp_dir = tempfile.gettempdir()
    out_path = os.path.join(tmp_dir, base + ext)

    if writer is not None:
        writer(df, out_path)
    else:
        df.to_csv(out_path, index=False)

    return dcc.send_file(out_path)



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
                f"#### A3M '{name}.a3m' already available. Selected it for you.")
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
            f"#### Registered A3M '{name}.a3m' from ProteinMPNN with {msa_length} entries.")

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


@callback(
    Output("multimer-chains", "options"),
    Input("msa-data", "data"),
)
def _populate_multimer_options(msa_data):
    if not msa_data:
        return []
    keys = sorted(msa_data.keys())
    return [{"label": k, "value": k} for k in keys]


@callback(
    Output("multimer-status", "children"),
    Output("msa-data", "data", allow_duplicate=True),
    Output("main-msa", "data", allow_duplicate=True),
    Input("multimer-build", "n_clicks"),
    State("multimer-chains", "value"),
    State("multimer-name", "value"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def _build_multimer(n_clicks, chains_multi, out_name, msa_data):
    import os, re, tempfile, sys, traceback
    from pathlib import Path
    import pandas as pd

    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update
    if not msa_data:
        return dcc.Markdown("Please select two source MSAs."), dash.no_update, dash.no_update

    # Validate list of chains
    if not chains_multi or not isinstance(chains_multi, list) or len(chains_multi) < 2:
        return dcc.Markdown("Please pick at least two MSAs in order (A, B, ...)."), dash.no_update, dash.no_update
    # Ensure all unique
    if len(set(chains_multi)) != len(chains_multi):
        return dcc.Markdown("Duplicate selections detected. Please choose unique MSAs."), dash.no_update, dash.no_update

    chain_list = chains_multi

    try:
        # Build a safe filename (no path separators, ascii-only whitelist) and ensure .a3m
        base_default = "_".join(chain_list)
        safe = (out_name or base_default).strip()
        safe = re.sub(r"[\\/]+", "_", safe)                     # collapse any slashes
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", safe) or base_default
        safe = safe.lstrip(".").strip("_") or base_default
        if not safe.lower().endswith(".a3m"):
            safe += ".a3m"

        from frankenmsa.utils import write_a3m
        from frankenmsa.utils.multimer_a3m import combine_unpaired_a3m

        # Stable temp workspace
        tmpdir = Path(tempfile.gettempdir()) / "frankenmsa"
        tmpdir.mkdir(parents=True, exist_ok=True)

        # Materialize input chains into temp A3Ms
        in_paths = []
        for idx, cname in enumerate(chain_list):
            df_i = pd.DataFrame(msa_data[cname])
            p = tmpdir / f"{cname}.a3m"
            write_a3m(df_i, str(p))
            if not p.is_file():
                return dcc.Markdown(f"Input {idx+1} is not a file: `{p}`"), dash.no_update, dash.no_update
            in_paths.append(str(p))
        out_path = tmpdir / safe  # always a file inside tmpdir

        # Debug prints to stderr
        print(f"[MULTIMER][DEBUG] tmpdir={tmpdir}", file=sys.stderr)
        print(f"[MULTIMER][DEBUG] in_paths={in_paths}", file=sys.stderr)
        print(f"[MULTIMER][DEBUG] out_path={out_path}", file=sys.stderr)

        # Build multimer file on disk
        combine_unpaired_a3m(in_paths, str(out_path))

        # Parse back and register in store (use local parser that supports multimer A3M)
        combined_records = _parse_a3m_simple(str(out_path))
        headers = [h for (h, s) in combined_records]
        sequences = [s for (h, s) in combined_records]
        new_msa_df = pd.DataFrame({"header": headers, "sequence": sequences})

        msa_key = out_path.stem
        msa_data = {} if msa_data is None else dict(msa_data)
        msa_data[msa_key] = new_msa_df.to_dict("list")

        chains_str = " + ".join(chain_list)
        msg = dbc.Alert(
            f"Built multimer A3M '{out_path.name}' from {chains_str}. It is now available in the file selector.",
            color="success",
            className="py-2",
            style={"fontSize": "14px", "marginTop": "8px"},
        )
        return msg, msa_data, msa_key

    except Exception as e:
        # Provide rich debug info to help diagnose path issues
        err_md = f"""
        **Failed to build multimer**: {e.__class__.__name__}: {e}

        Debug paths:

        - inputs : `
""" + "\n".join(f"  - `{p}`" for p in locals().get("in_paths", [])) + """
`
        - output : `{locals().get('out_path','')}`
        """
        return dcc.Markdown(err_md), dash.no_update, dash.no_update
