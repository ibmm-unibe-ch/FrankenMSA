import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State

dash.register_page(
    __name__,
)


def layout():
    return html.Div(proteinmpnn_layout(), className="gradient-background")
    return html.Div(
        [
            html.H1("Run Inverse Folding"),
            html.P(
                "This is the home page of the application. You can navigate to different pages using the links below."
            ),
        ],
        className="gradient-background",
    )


def proteinmpnn_layout():
    upload_component = dcc.Upload(
        id="upload-pdb-data",
        children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
        className="upload-component",
        multiple=False,  # Allow only a single file to be uploaded
        style={
            "width": "100%",
        },
    )

    options = dbc.Row(
        [
            dbc.Col(
                [
                    html.P("Sampling Temperature (higher values = more diversity)"),
                    dcc.Slider(
                        id="proteinmpnn-sampling-temperature",
                        min=0.1,
                        max=5.0,
                        step=0.1,
                        value=1.0,
                        marks={i / 10: str(i / 10) for i in range(10, 50, 10)},
                        persistence=True,
                        persistence_type="memory",
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ]
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
                        persistence=True,
                        persistence_type="memory",
                    ),
                ]
            ),
        ],
        style={
            "align-items": "center",
            "justify-content": "center",
        },
    )

    return html.Div(
        [
            html.H1("Inverse Fold with ProteinMPNN"),
            html.P(
                dcc.Markdown(
                    "Repeatedly run inverse folding using [ProteinMPNN](https://www.science.org/doi/10.1126/science.add2187). To generate an arbitrary pseudo-MSA from a given protein structure. This uses the [biolib](https://biolib.com/) remote ProteinMPNN server. Since this is a remote server with a queue it may take a while to get results. Please be patient. Note that at this point only homomers are supported by FrankenMSA so please only upload PDBs with a single protein and chain.",
                )
            ),
            upload_component,
            options,
            html.Button(
                "Run ProteinMPNN",
                id="run-proteinmpnn-button",
                n_clicks=0,
                className="button-component",
                style={"width": "80%"},
            ),
            dcc.Loading(
                html.Div(
                    id="pdb-upload-status",
                    style={
                        "margin-top": "20px",
                        "textAlign": "center",
                    },
                ),
                color="white",
            ),
        ],
        style={
            "align-items": "center",
            "justify-content": "center",
            "align-content": "center",
            "flex-direction": "column",
            "display": "flex",
            "width": "100%",
        },
    )


@callback(
    Output("pdb-upload-status", "children"),
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Input("run-proteinmpnn-button", "n_clicks"),
    State("upload-pdb-data", "contents"),
    State("upload-pdb-data", "filename"),
    State("proteinmpnn-sampling-temperature", "value"),
    State("proteinmpnn-sequence-count", "value"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_proteinmpnn(
    n_clicks, contents, filename, sampling_temperature, sequence_count, msa_data
):
    if (n_clicks or 0) == 0:
        return dash.no_update, dash.no_update, dash.no_update
    if contents is not None:
        if filename.lower().endswith(".pdb"):
            # turn the octet-stream into a string
            import base64
            import io

            from pathlib import Path

            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)
            with open("temp.pdb", "wb") as f:
                f.write(decoded)
            # Run ProteinMPNN
            from frankenmsa.inverse_fold import (
                BiolibProteinMPNN as ProteinMPNN,
            )

            proteinmpnn = ProteinMPNN()
            msa_df, _ = proteinmpnn.generate(
                "temp.pdb",
                n=sequence_count,
                temperature=sampling_temperature,
            )
            # Clean up the temporary file
            Path("temp.pdb").unlink()
            # Return the generated MSA

            name = f"proteinmpnn_{Path(filename).name}"
            msa_data[name] = msa_df.to_dict()

            return (
                f"'{filename}' successfully uploaded. {sequence_count} sequences generated.",
                name,
                msa_data,
            )
        else:
            return (
                f"'{filename}' has an unknown format. Please upload a .pdb file",
                dash.no_update,
                dash.no_update,
            )
    else:
        return (
            "No file uploaded",
            dash.no_update,
            dash.no_update,
        )


@callback(
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("run-proteinmpnn-button", "n_clicks"),
    State("upload-pdb-data", "filename"),
    prevent_initial_call=True,
)
def show_notification(n_clicks, filename):
    if n_clicks > 0:
        if filename:
            return (
                f"Running ProteinMPNN on '{filename}'. This will take some time as it is a remote server. Go for a coffee or tea and come back later ☕.",
                True,
            )
    return dash.no_update, False
