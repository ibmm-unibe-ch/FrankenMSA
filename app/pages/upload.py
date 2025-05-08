import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State

dash.register_page(
    __name__,
)


def layout():

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
        className="gradient-background",
    )


@callback(
    Output("upload-status", "children"),
    Output("main-msa", "data"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def upload_file(contents, filename):
    if contents is not None:
        if (
            filename.endswith(".fasta")
            or filename.endswith(".a3m")
            or filename.endswith(".fa")
        ):
            from frankenmsa.utils import read_a3m

            # turn the octet-stream into a string
            import base64
            import io

            from pathlib import Path

            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)
            decoded = io.BytesIO(decoded)
            decoded = decoded.read().decode("utf-8")
            with open("temp_file.a3m", "w") as f:
                f.write(decoded)
            msa = read_a3m("temp_file.a3m")

            # Path("temp_file.a3m").unlink()

        elif filename.endswith(".csv"):
            import pandas as pd
            from io import StringIO

            msa = pd.read_csv(StringIO(contents))
            if "sequence" not in msa.columns:
                err = dcc.ConfirmDialog(
                    id="upload-error",
                    message="The uploaded CSV file does not contain a 'sequence' column.",
                    displayed=True,
                )
                return err, None
        else:
            from pathlib import Path

            suffix = Path(filename).suffix
            err = dcc.ConfirmDialog(
                id="upload-error",
                message=f"Unsupported file format '{suffix}'. Please upload a .fasta, .a3m, or .csv file.",
                displayed=True,
            )
            return err, None

        msa_length = len(msa)
        success_message = dcc.Markdown(
            f"""
            #### File uploaded successfully and MSA with {msa_length} entries loaded!
            You can now navigate to the other pages to perform operations on the MSA.
            """
        )
        return success_message, msa.to_dict()

    return dash.no_update, dash.no_update
