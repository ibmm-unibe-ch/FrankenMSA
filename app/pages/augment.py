import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from frankenmsa.augment import run_ghostfold_augmentation
from frankenmsa.runtime import log_message


dash.register_page(
    __name__,
)


def layout():
    return html.Div([dbc.Row([ghostfold_layout()])], className="gradient-background")


def ghostfold_layout():
    return html.Div(
        [
            # 1. Title
            html.H1("GhostFold", style={"marginBottom": "10px"}),
            # 2. Citation Link
            html.Div(
                [
                    html.Span("Augment one sequence using "),
                    html.A(
                        "GhostFold",
                        href="https://www.biorxiv.org/content/10.1101/2025.10.13.682177v1",
                        target="_blank",
                    ),
                    html.Span("."),
                ],
                style={"marginBottom": "20px", "fontSize": "1.1rem"},
            ),
            # 3. Input Area
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
            # 4. Run Button
            html.Button(
                "Run GhostFold Augmentation",
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
            # 5. Output / Status spinner
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


# =============================================================================
#  Callback
# =============================================================================
@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Output("ghostfold-output", "children"),
    Input("ghostfold-run-button", "n_clicks"),
    State("ghostfold-input", "value"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_ghostfold(n_clicks, input_data, msa_data):
    """Execute GhostFold augmentation and store the created MSA."""
    log_message(
        f"GhostFold run button clicked {n_clicks} times. Received input: {input_data}"
    )
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        msa_data, new_main_key, _, result_df = run_ghostfold_augmentation(
            input_data,
            msa_data,
        )
        log_message(
            f"GhostFold augmentation successful, generated {len(result_df['sequence'])} sequences."
        )
        msg = f"Success! Generated {new_main_key} with {len(result_df['sequence'])} sequences."
        return new_main_key, msa_data, dbc.Alert(msg, color="success")

    except Exception as e:
        import traceback

        log_message(f"Error during GhostFold augmentation: {str(e)}")
        log_message(f"Traceback:\n{traceback.format_exc()}")
        return (
            dash.no_update,
            dash.no_update,
            dbc.Alert(str(e), color="danger"),
        )
