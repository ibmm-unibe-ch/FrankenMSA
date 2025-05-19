import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from frankenmsa.visual import visualise_msa

dash.register_page(
    __name__,
)


def no_msa_yet():
    return dbc.Alert(
        "No MSA data is available to visualize. Please upload or generate MSA data to proceed.",
        color="warning",
        className="shaded-bordered",
        is_open=True,
    )


def layout():
    return html.Div(
        [
            html.H1("Visualise the MSA", style={"padding-bottom": "20px"}),
            dcc.Loading(
                id="loading",
                type="circle",
                children=[
                    html.Div(
                        id="plotly-visualisation",
                        className="shaded-bordered",
                        style={
                            "height": "100%",
                            "width": "100%",
                            "overflow": "hidden",
                            "background-color": "transparent",
                        },
                    ),
                ],
            ),
        ],
        className="gradient-background",
    )


@callback(
    Output("plotly-visualisation", "children"),
    Input("main-msa", "data"),
    Input("msa-data", "data"),
)
def update_plotly_visualisation(main, data):
    if not data:
        return no_msa_yet()

    import pandas as pd

    msa = data[main]
    msa = pd.DataFrame.from_dict(msa)

    plotly_component = visualise_msa(msa, backend="plotly")

    if len(msa) > 150:
        plotly_component = html.Div(
            [
                plotly_component,
                html.P(
                    "Note: The MSA is too large to visualize fully, it was subsampled evenly to 150 entries.",
                    style={"color": "red"},
                ),
            ],
        )
    return plotly_component
