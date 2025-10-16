import dash
from dash import html, dcc
from dash import callback, Input, Output, State, clientside_callback
import dash_bootstrap_components as dbc
from urllib.parse import urlencode
import time

COLAB_URL = "https://colab.research.google.com/drive/15DjFatufe3gWY-s-Q-zfQHJL9gAHNjxk"

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
    options = dbc.Row(
        [
            dbc.Col(
                [
                    html.P("Sampling Temperature (higher values = more diversity)"),
                    html.Div(
                        dcc.Slider(
                            id="proteinmpnn-sampling-temperature",
                            min=0.1,
                            max=5.0,
                            step=0.1,
                            value=1.0,
                            marks={i / 10: str(i / 10) for i in range(10, 50, 10)},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                        style={"width": "100%"},
                    ),
                ],
                md=6,
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
                        style={"width": "100%"},
                    ),
                ],
                md=6,
            ),
        ],
        className="g-2",
        style={
            "align-items": "center",
            "justify-content": "center",
        },
    )

    advanced = html.Div(
        [
            # Row A: PDB code on the left, Homomer toggle on the right (aligned to the end)
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(
                                "PDB code (optional, leave blank to upload in Colab)",
                                className="mb-1",
                                style={"fontWeight": 500},
                            ),
                            dcc.Input(
                                id="proteinmpnn-pdb-code",
                                type="text",
                                value="",
                                placeholder="e.g., 2NNC",
                                className="input-component",
                                style={"width": "100%"},
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            # Centered heading + checkbox (baseline aligned)
                            html.Div(
                                [
                                    html.Span(
                                        "Homomer (single chain)",
                                        style={
                                            "fontWeight": 500,
                                            "color": "#212529",
                                            "marginRight": "8px",
                                            "display": "inline-flex",
                                            "alignItems": "center",
                                            "lineHeight": "1.2",
                                        },
                                    ),
                                    dbc.Checkbox(
                                        id="proteinmpnn-homomer",
                                        value=True,
                                        className="mb-0",
                                        style={
                                            "display": "inline-block",
                                            "position": "relative",
                                            "top": "6px",          # nudge checkbox down a bit to align with text
                                            "margin": 0,
                                        },
                                    ),
                                ],
                                style={
                                    "display": "inline-flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "gap": "8px",
                                    "marginBottom": "6px",
                                    "width": "100%",
                                    "textAlign": "center",
                                },
                            ),
                            html.Small(
                                "Currently only homomers (single chain) are supported.",
                                className="text-muted",
                                style={
                                    "display": "block",
                                    "textAlign": "center",
                                    "marginTop": "4px",
                                },
                            ),
                        ],
                        md=6,
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "alignItems": "center",
                            "justifyContent": "center",
                        },
                    ),
                ],
                className="g-2",
                style={"alignItems": "center"},
            ),
            # Row B: Design / Fixed chains in two equal columns
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Design chains (e.g., A or A,B)", className="mb-1", style={"fontWeight": 500}),
                            dcc.Input(
                                id="proteinmpnn-design-chains",
                                type="text",
                                value="",
                                placeholder="A or A,B",
                                className="input-component",
                                style={"width": "100%"},
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Fixed chains (optional)", className="mb-1", style={"fontWeight": 500}),
                            dcc.Input(
                                id="proteinmpnn-fixed-chains",
                                type="text",
                                value="",
                                placeholder="B or B,C",
                                className="input-component",
                                style={"width": "100%"},
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="g-2",
                style={"alignItems": "center", "marginBottom": "6px"},
            ),
        ],
        style={"paddingTop": "1px"}
    )

    advanced_collapse = html.Div([
        html.Hr(style={"margin": "6px 0 12px 0"}),
        html.Div(
            html.Button("Advanced (optional) ▼", id="toggle-advanced", n_clicks=0,
                        style={"background":"none","border":"none","fontWeight":700,"fontSize":"1.2rem"}),
            style={"textAlign":"center","marginBottom":"10px"}
        ),
        dbc.Collapse(
            advanced, 
            id="collapse-advanced", 
            is_open=False,
            style={"overflow": "hidden"}
        )
    ])

    page_container = html.Div(
        [
            html.H1("Inverse Fold with ProteinMPNN"),
            html.Div(style={"height": "32px"}),
            html.Div(
                dcc.Markdown(
                    "Run inverse folding using **ProteinMPNN** on a **Google Colab GPU**.\n"
                    "Set parameters here and click **Open Colab** to launch the notebook.\n"
                    "Note: currently FrankenMSA only supports homomers (single chain)."
                )
            ),
            options,
            advanced_collapse,
            html.Div(
                [
                    html.Button(
                        "Open in Google Colab",
                        id="open-proteinmpnn-colab",
                        n_clicks=0,
                        className="button-component",
                        style={"width": "100%", "fontWeight": 700},
                    ),
                    html.Div(
                        "Tip: parameters will be copied automatically. In Colab, paste them into the first input field and run.",
                        style={"marginTop": "10px", "fontSize": "0.95rem", "opacity": 0.9}
                    ),
                    html.Div(id="colab-launch-dummy", style={"display": "none"}),
                    dcc.Store(id="colab-url", data=COLAB_URL),
                ],
                style={
                    "width": "56%",
                    "maxWidth": "620px",
                    "marginTop": "12px",
                    "margin": "20px auto",
                    "textAlign": "center",
                },
            ),
        ],
        style={"width": "80%", "maxWidth": "1000px"},
    )

    return html.Div([page_container], style={"display": "flex", "justifyContent": "center", "width": "100%"})


@callback(
    Output("collapse-advanced", "is_open"),
    Output("toggle-advanced", "children"),
    Input("toggle-advanced", "n_clicks"),
    prevent_initial_call=True
)

def toggle_advanced(n):
    if n and n % 2 == 1:
        return True, "Advanced (optional) ▲"
    return False, "Advanced (optional) ▼"


from dash.dependencies import Input as _Input, Output as _Output, State as _State  # ensure alias not required, but keep for clarity

clientside_callback(
    """
    function(n, temp, num, design, fixed, pdb, homomer, colabUrl) {
      if (!n) { return ""; }
      try {
        const params = new URLSearchParams({
          temp: (temp ?? 1.0).toString(),
          num: (num ?? 128).toString(),
          design: (design || "").toString().trim().toUpperCase(),
          fixed: (fixed || "").toString().trim().toUpperCase(),
          pdb: (pdb || "").toString().trim().toUpperCase(),
          homomer: (homomer ? "1" : "0"),
        });
        const paramStr = "?" + params.toString();

        // Try to copy to clipboard
        if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(paramStr).then(
            () => { /* ok */ },
            () => { /* ignore */ }
          );
        }

        // Open Colab notebook in a new tab
        const url = colabUrl || "https://colab.research.google.com/";
        window.open(url, "_blank");

        // Also show a simple alert to guide the user
        try {
          alert("Parameters copied. In Colab, paste into the first input field and run.");
        } catch(e) {}

      } catch(e) {
        console.error(e);
        alert("Failed to open Colab. Please try again.");
      }
      return "";
    }
    """,
    _Output("colab-launch-dummy", "children"),
    _Input("open-proteinmpnn-colab", "n_clicks"),
    _State("proteinmpnn-sampling-temperature", "value"),
    _State("proteinmpnn-sequence-count", "value"),
    _State("proteinmpnn-design-chains", "value"),
    _State("proteinmpnn-fixed-chains", "value"),
    _State("proteinmpnn-pdb-code", "value"),
    _State("proteinmpnn-homomer", "value"),
    _State("colab-url", "data"),
    prevent_initial_call=True,
)