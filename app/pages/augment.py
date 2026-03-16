import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from frankenmsa.augment import GhostFoldAugmentation
import pandas as pd


dash.register_page(
    __name__,
)

def log_message(message:str):
    with open("app.log", "a") as log_file:
        log_file.write(f"{message}\n")

def layout():
    return html.Div([
        dbc.Row([ghostfold_layout()])
    ], className="gradient-background")

def ghostfold_layout():
    return html.Div(
        [
            # 1. Title
            html.H1("GhostFold", style={"marginBottom": "10px"}),
            
            # 2. Citation Link
            html.Div([
                html.Span("Augment one sequence using "),
                html.A("GhostFold", href="https://www.biorxiv.org/content/10.1101/2025.10.13.682177v1", target="_blank"),
                html.Span("."),
            ], style={"marginBottom": "20px", "fontSize": "1.1rem"}),
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
                    "fontFamily": "monospace"
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
                style={"width": "80%", "fontSize": "16px", "fontWeight": "bold", "padding": "12px"},
            ),
        ],
        style={"textAlign": "center", "paddingBottom": "50px"}
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
    """
    Execute GhostFold augmentation and store results in msa_data.

    Validates input, handles monomers and multimers, submits to API,
    and splits multimer results by chain.
    """
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    if not input_data:
        return dash.no_update, dash.no_update, dbc.Alert("Please provide input data.", color="danger")

    # 1. Parse and clean input
    input_data = "".join(input_data.strip().upper().split())

    if not input_data or not all(c in "ACDEFGHIKLMNPQRSTVWY:" for c in input_data):
        return dash.no_update, dash.no_update, dbc.Alert("No valid sequences found.", color="danger")
    try:
        new_main_key = f"ghostfold_aug_{n_clicks}"
        log_message(f"Running GhostFold augmentation for input: {input_data}")
        data_dict = GhostFoldAugmentation().align(sequence=input_data)    
        msa_data[new_main_key] = data_dict
        log_message(f"GhostFold augmentation successful, generated {len(data_dict['sequence'])} sequences.")
        msg = f"Success! Generated {new_main_key} with {len(data_dict['sequence'])} sequences."
        return new_main_key, msa_data, dbc.Alert(msg, color="success")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return dash.no_update, dash.no_update, dbc.Alert(f"API Error: {str(e)}", color="danger")
