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
        multiple=False,  # Allow only a single file to be uploaded
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
    if contents is not None:
        # turn the octet-stream into a string
        import base64
        import io

        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        decoded = io.BytesIO(decoded)
        decoded = decoded.read().decode("utf-8")
        if (
            filename.endswith(".fasta")
            or filename.endswith(".a3m")
            or filename.endswith(".fa")
        ):
            from frankenmsa.utils import read_a3m

            from pathlib import Path

            with open("temp_file.a3m", "w") as f:
                f.write(decoded)
            msa = read_a3m("temp_file.a3m")

            # Path("temp_file.a3m").unlink()

        elif filename.endswith(".csv"):
            import pandas as pd
            from io import StringIO

            msa = pd.read_csv(StringIO(decoded), header=0)
            if "sequence" not in msa.columns:
                err = dcc.ConfirmDialog(
                    id="upload-error",
                    message="The uploaded CSV file does not contain a 'sequence' column.",
                    displayed=True,
                )
                return err, dash.no_update, dash.no_update
        else:
            from pathlib import Path

            suffix = Path(filename).suffix
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
        msa_data[filename] = msa.to_dict()
        return success_message, filename, msa_data

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
        persistence_type="session",
        className="dropdown-component",
    )
    download_filename = dcc.Input(
        id="download-filename",
        type="text",
        placeholder="my_frankenmsa",
        style={"width": "50%"},
        className="input-component",
        persistence=True,
        persistence_type="session",
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

        if filename == "":
            filename = "my_frankenmsa"
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
