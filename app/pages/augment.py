import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from frankenmsa.augment import run_ghostfold_augmentation
from frankenmsa.runtime import log_message
from helpers.layout import page


dash.register_page(
    __name__,
)


def layout():
    return page(
        "Augment",
        "Generate a synthetic MSA for a single sequence.",
        ghostfold_layout(),
        narrow=True,
    )


def ghostfold_layout():
    return html.Div(
        [
            # 1. Title
            html.H1("GhostFold"),
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
                style={"marginBottom": "16px", "color": "var(--fm-muted)"},
            ),
            # 3. Input Area
            dcc.Textarea(
                id="ghostfold-input",
                placeholder="Enter sequence here...\nExample:\nACDEFGHIKLMNPQRSTVWY",
                className="sequence-input",
                persistence=True,
                persistence_type="memory",
            ),
            # 4. Run Button
            html.Button(
                "Run GhostFold Augmentation",
                id="ghostfold-run-button",
                n_clicks=0,
                className="button-component button-primary button-block",
            ),
            # 5. Output / Status spinner
            dcc.Loading(
                html.Div(
                    id="ghostfold-output",
                    className="output-component",
                    style={"marginTop": "16px"},
                ),
                type="dot",
                color="#333",
            ),
        ],
        className="shaded-bordered",
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
