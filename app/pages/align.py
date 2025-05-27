import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State

dash.register_page(
    __name__,
)


def layout():
    return html.Div([mmseqs_colab_layout()], className="gradient-background")


def mmseqs_colab_layout():
    pairing_tooltip = dbc.Tooltip(
        dcc.Markdown(
            "Pairing mode determines how sequences are paired for alignment. `None` means no pairing (i.e. single sequence -> MSA). If multiple sequences are provided `Greedy` provides a quicker but less accurate alignment, while `All` pairs all uses a more exhaustive but more accurate algorithm."
        ),
        target="mmseqs-pairing-mode",
    )
    filter_tooltip = dbc.Tooltip(
        dcc.Markdown(
            "Filtering mode determines whether to filter sequences before alignment. Filtering can improve alignment quality by removing low-quality sequences."
        ),
        target="mmseqs-filter-mode",
    )
    return html.Div(
        [
            html.H1("MMseqs2 ColabFold"),
            dcc.Markdown(
                """
                Align one or more sequences using [MMseqs2](https://www.nature.com/articles/s41467-018-04964-5). This is a fast and accurate sequence alignment tool that can handle large datasets efficiently.
                """
            ),
            dcc.Textarea(
                id="mmseqs-input",
                placeholder="Enter your sequences here. Separate multiple sequences with newlines. Fasta format is also accepted.",
                style={
                    "width": "100%",
                    "padding": "10px",
                    "margin-bottom": "20px",
                    "height": "100px",
                    "width": "80%",
                    "margin-top": "20px",
                },
                className="input-component",
                persistence=True,
                persistence_type="memory",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P("Pairing mode"),
                            dcc.RadioItems(
                                id="mmseqs-pairing-mode",
                                options=[
                                    {"label": "None", "value": "none"},
                                    {"label": "Greedy", "value": "greedy"},
                                    {"label": "All", "value": "complete"},
                                ],
                                value="none",
                                persistence=True,
                                persistence_type="memory",
                            ),
                        ]
                    ),
                    dbc.Col(
                        [
                            html.P("Use Filtering"),
                            dcc.RadioItems(
                                id="mmseqs-filter-mode",
                                options=[
                                    {"label": "Yes", "value": True},
                                    {"label": "No", "value": False},
                                ],
                                value=True,
                                persistence=True,
                                persistence_type="memory",
                            ),
                        ]
                    ),
                    pairing_tooltip,
                    filter_tooltip,
                ]
            ),
            html.Button(
                "Run MMseqs2",
                id="mmseqs-run-button",
                n_clicks=0,
                className="button-component",
                style={"width": "80%"},
            ),
            dcc.Loading(
                html.Div(
                    id="mmseqs-output",
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "margin-top": "20px",
                        "height": "100px",
                        "overflow": "auto",
                    },
                    className="output-component",
                ),
            ),
        ]
    )


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
    if n_clicks == 0:
        raise dash.exceptions.PreventUpdate

    # Check if input data is provided
    if not input_data:
        return dash.no_update, dash.no_update, "Please provide input data."

    # Process the input data
    sequences = input_data.strip().split("\n")
    sequences = [
        seq.strip().upper() for seq in sequences if seq.strip() if ">" not in seq
    ]

    # Check if any sequences are provided
    if not sequences:
        return dash.no_update, dash.no_update, "No valid sequences provided."

    # Run MMseqs2 alignment
    try:
        from frankenmsa.align import MMSeqs2Colab

        mmseqs = MMSeqs2Colab("frankenmsa-gui")
        msa_df = mmseqs.align(
            sequences,
            True,  # use env-mode by default
            filter_mode,
            None if pairing_mode == "none" else pairing_mode,
        )
        n_mmseqs_generated = sum(1 for i in msa_data.keys() if "mmseqs" in i)
        new_main_msa = f"mmseqs_{n_mmseqs_generated + 1}"
        msa_data[new_main_msa] = msa_df.to_dict("list")
        return new_main_msa, msa_data, "Alignment completed successfully."
    except Exception as e:
        return dash.no_update, dash.no_update, f"Error during alignment: {str(e)}"
