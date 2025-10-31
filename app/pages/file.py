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
                dbc.Col(file_download_layout()),
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
        success_message = dcc.Markdown(
            f"""
            #### File uploaded successfully and MSA with {msa_length} entries loaded!
            You can now navigate to the other pages to perform operations on the MSA.
            """
        )
        name = Path(filename).stem
        msa_data = {} if msa_data is None else msa_data
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


@callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    State("download-format", "value"),
    State("download-filename", "value"),
)
def download_file(n_clicks, main_msa, msa_data, format, filename):
    if n_clicks > 0:
        import pandas as pd

        if msa_data is None:
            return dash.no_update
        msa = msa_data[main_msa]
        msa = pd.DataFrame(msa)

        if filename == "" or filename is None:
            filename = main_msa
        if format == ".a3m":
            filename += ".a3m"
            from frankenmsa.utils import write_a3m

            write_a3m(msa, filename)
        elif format == ".fasta":
            filename += ".fasta"
            from frankenmsa.utils import write_a3m

            write_a3m(msa, filename)
        elif format == ".csv":
            filename += ".csv"

            msa.to_csv(filename, index=False)
        else:
            raise ValueError("Invalid file format")
        return dcc.send_file(filename)
    return None



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

        # If already present, just switch selection and clear the store
        msa_data = {} if msa_data is None else msa_data
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
