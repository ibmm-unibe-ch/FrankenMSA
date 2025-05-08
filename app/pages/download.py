import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State

dash.register_page(
    __name__,
)


def layout():

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
        className="gradient-background",
    )
    return body


@callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("main-msa", "data"),
    State("download-format", "value"),
    State("download-filename", "value"),
)
def download_file(n_clicks, msa, format, filename):
    if n_clicks > 0:
        import pandas as pd

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
