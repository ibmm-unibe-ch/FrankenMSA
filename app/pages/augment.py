import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from frankenmsa.augment import run_ghostfold_augmentation, run_softmax_augmentation
from frankenmsa.runtime import log_message


dash.register_page(
    __name__,
)


def layout():
    return html.Div([dbc.Row([augmentation_layout()])], className="gradient-background")


def augmentation_layout():
    return html.Div(
        [
            html.H1("Sequence Augmentation", style={"marginBottom": "10px"}),
            html.Div(
                [
                    html.Span("Augment one sequence with "),
                    html.A(
                        "GhostFold",
                        href="https://www.biorxiv.org/content/10.1101/2025.10.13.682177v1",
                        target="_blank",
                    ),
                    html.Span(" or sampling from a "),
                    html.A(
                        "Softmax distribution",
                        href="https://en.wikipedia.org/wiki/Softmax_function",
                        target="_blank",
                    ),
                    html.Span(" based on a "),
                    html.A(
                        "BLOSUM",
                        href="https://en.wikipedia.org/wiki/BLOSUM",
                        target="_blank",
                    ),
                    html.Span(" matrix with O and U replaced."),
                ],
                style={"marginBottom": "20px", "fontSize": "1.1rem"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Augmentation backend", className="mb-1"),
                            dcc.Dropdown(
                                id="augmentation-method",
                                options=[
                                    {"label": "GhostFold", "value": "ghostfold"},
                                    {"label": "Softmax", "value": "softmax"},
                                ],
                                value="softmax",
                                clearable=False,
                                style={"textAlign": "left"},
                            ),
                        ],
                        md=4,
                    ),
                ],
                className="g-2",
                style={"justifyContent": "center", "marginBottom": "12px"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Softmax temperature, lower = more diverse", className="mb-1"),
                            dcc.Input(
                                id="softmax-temperature",
                                type="number",
                                value=1.0,
                                min=0.1,
                                max=10.0,
                                step=0.1,
                                style={"width": "100%"},
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Softmax depth", className="mb-1"),
                            dcc.Input(
                                id="softmax-depth",
                                type="number",
                                value=128,
                                min=1,
                                max=1000,
                                step=1,
                                style={"width": "100%"},
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Softmax BLOSUM matrix", className="mb-1"),
                            dcc.Dropdown(
                                id="softmax-matrix",
                                options=[
                                    {"label": "BLOSUM 45", "value": "BLOSUM45"},
                                    {"label": "BLOSUM 50", "value": "BLOSUM50"},
                                    {"label": "BLOSUM 62", "value": "BLOSUM62"},
                                    {"label": "BLOSUM 80", "value": "BLOSUM80"},
                                    {"label": "BLOSUM 90", "value": "BLOSUM90"},
                                ],
                                value="BLOSUM62",
                                clearable=False,
                                style={"textAlign": "left"},
                            ),
                        ],
                        md=3,
                    ),
                ],
                className="g-2",
                style={"justifyContent": "center", "marginBottom": "12px"},
            ),
            dcc.Textarea(
                id="ghostfold-input",
                placeholder="Enter sequence here...\nExample:\nACDEFGHIKLMNPQRSTVWY",
                style={
                    "width": "100%",
                    "padding": "15px",
                    "height": "120px",
                    "width": "80%",
                    "borderRadius": "8px",
                    "border": "1px solid #ccc",
                    "fontSize": "14px",
                    "fontFamily": "monospace",
                },
                className="input-component",
                persistence=True,
                persistence_type="memory",
            ),
            html.Button(
                "Run Augmentation",
                id="ghostfold-run-button",
                n_clicks=0,
                className="button-component",
                style={
                    "width": "80%",
                    "fontSize": "16px",
                    "fontWeight": "bold",
                    "padding": "12px",
                },
            ),
            dcc.Loading(
                html.Div(
                    id="ghostfold-output",
                    className="output-component",
                    style={
                        "marginTop": "20px",
                        "width": "80%",
                        "marginLeft": "auto",
                        "marginRight": "auto",
                    },
                ),
                type="dot",
                color="#333",
            ),
        ],
        style={"textAlign": "center", "paddingBottom": "50px"},
    )


@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Output("ghostfold-output", "children"),
    Input("ghostfold-run-button", "n_clicks"),
    State("ghostfold-input", "value"),
    State("augmentation-method", "value"),
    State("softmax-temperature", "value"),
    State("softmax-depth", "value"),
    State("softmax-matrix", "value"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_augmentation(
    n_clicks,
    input_data,
    method,
    softmax_temperature,
    softmax_depth,
    softmax_matrix,
    msa_data,
):
    """Execute the selected augmentation backend and store the created MSA."""
    log_message(
        f"Augmentation run button clicked {n_clicks} times with backend={method}. Received input: {input_data}"
    )
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        if (method or "ghostfold") == "softmax":
            msa_data, new_main_key, _, result_df = run_softmax_augmentation(
                input_data,
                msa_data,
                prefix="softmax_aug",
                temperature=float(softmax_temperature or 1.0),
                depth=int(softmax_depth or 128),
                matrix=softmax_matrix or "BLOSUM62",
            )
            label = "Softmax"
        else:
            msa_data, new_main_key, _, result_df = run_ghostfold_augmentation(
                input_data,
                msa_data,
            )
            label = "GhostFold"

        log_message(
            f"{label} augmentation successful, generated {len(result_df['sequence'])} sequences."
        )
        msg = f"Success! Generated {new_main_key} with {len(result_df['sequence'])} sequences."
        return new_main_key, msa_data, dbc.Alert(msg, color="success")

    except Exception as e:
        import traceback

        log_message(f"Error during augmentation: {str(e)}")
        log_message(f"Traceback:\n{traceback.format_exc()}")
        return (
            dash.no_update,
            dash.no_update,
            dbc.Alert(str(e), color="danger"),
        )
