import dash
from dash import html, dcc
from dash import callback, Input, Output, State, clientside_callback
import dash_bootstrap_components as dbc
from urllib.parse import urlencode
import time

# HOTFIX: point to upstream public ProteinMPNN demo until our notebook exists on dev
COLAB_URL = (
    "https://colab.research.google.com/github/ibmm-unibe-ch/FrankenMSA/blob/feature/colab-runner/app/proteinmpnn_runner.ipynb?v=2025-10-09-1205"
)

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
                                placeholder="e.g., 1ABC",
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
            html.Div(style={"height": "32px"}),  # add spacing between title and description
            html.Div(
                dcc.Markdown(
                    "Run inverse folding using **ProteinMPNN** on a **Google Colab GPU**.\n"
                    "Parameters you set on this page (temperature, number of sequences, PDB code, chains, homomer) will be passed to Colab.\n"
                    "Click **Open Colab (with these parameters)** to launch the notebook. If a pop-up is blocked, use the backup link, or copy the parameter string and paste into the first Colab cell (`QUERY`).\n"
                    "Note: currently FrankenMSA only supports homomers (single chain)."
                )
            ),
            html.Div(
                dbc.Alert(
                    [
                        html.Strong("Heads up: "),
                        html.Span("Please upload your .pdb file in Google Colab after clicking the button below. "),
                        html.Span("This page no longer uploads PDBs; Colab will handle files and GPU execution."),
                    ],
                    color="info",
                    className="mb-3",
                ),
                style={"width": "100%"},
            ),
            options,
            advanced_collapse,
            html.Div(
                [
                    html.Button(
                        "Open Colab (with these parameters)",
                        id="open-proteinmpnn-colab",
                        n_clicks=0,
                        className="button-component",
                        style={"width": "100%", "fontWeight": 700},
                    ),
                    # anchor to carry the computed href (updated by build_colab_href)
                    html.A(
                        id="proteinmpnn-colab-link",
                        href=COLAB_URL,
                        target="_blank",
                        style={"display": "inline-block", "marginTop": "8px"},
                        children="If a pop-up is blocked, click here to open Colab",
                    ),
                    # hidden dummy for clientside callback output
                    html.Div(id="colab-launch-dummy", style={"display": "none"}),
                ],
                style={"width": "56%", "maxWidth": "620px", "marginTop": "12px", "margin": "20px auto", "textAlign": "center"},
            ),
            html.Div(
                [
                    html.Small(
                        "Or copy these parameters and paste into the first Colab cell (QUERY):",
                        className="text-muted",
                        style={"display": "block", "marginBottom": "6px", "textAlign": "center"},
                    ),
                    dbc.InputGroup(
                        [
                            dbc.Input(
                                id="proteinmpnn-param-string",
                                value="",
                                readonly=True,
                                style={"fontFamily": "monospace"},
                            ),
                            dbc.Button("Copy", id="proteinmpnn-copy-btn", n_clicks=0, outline=True),
                        ],
                        style={"maxWidth": "620px", "margin": "0 auto"},
                    ),
                    html.Div(id="proteinmpnn-copy-status", style={"fontSize": "0.9rem", "marginTop": "6px", "minHeight": "1.2rem"}),
                ],
                style={"width": "56%", "maxWidth": "620px", "margin": "0 auto 24px auto", "textAlign": "center"},
            ),
        ],
        style={"width": "80%", "maxWidth": "1000px"},
    )

    return html.Div([page_container], style={"display": "flex", "justifyContent": "center", "width": "100%"})


# This callback serializes the current UI state into a Colab URL query string
# so the notebook can parse it with parse_qs(location.search).
@callback(
    Output("proteinmpnn-colab-link", "href"),
    Output("proteinmpnn-param-string", "value"),
    Input("open-proteinmpnn-colab", "n_clicks"),  # build on click
    State("proteinmpnn-sampling-temperature", "value"),
    State("proteinmpnn-sequence-count", "value"),
    State("proteinmpnn-design-chains", "value"),
    State("proteinmpnn-fixed-chains", "value"),
    State("proteinmpnn-pdb-code", "value"),
    State("proteinmpnn-homomer", "value"),
    prevent_initial_call=True,
)

def build_colab_href(n, temp, num, design, fixed, pdb_code, homomer):
    if not n:
        raise dash.exceptions.PreventUpdate
    # Basic defaults
    try:
        t = round(float(temp), 3) if temp not in (None, "") else 1.0
    except Exception:
        t = 1.0
    try:
        n_val = int(num) if num not in (None, "") else 128
    except Exception:
        n_val = 128

    params = {}
    params["temp"] = t
    params["num"] = n_val

    # optional PDB code (uppercased, no spaces)
    if pdb_code is not None:
        p = str(pdb_code).strip().upper()
        if p:
            params["pdb"] = p

    # homomer flag: encode as 1/0 for easier parsing in Colab
    try:
        hflag = bool(homomer) if homomer is not None else True
    except Exception:
        hflag = True
    params["homomer"] = 1 if hflag else 0

    def _norm_chains(s):
        if not s:
            return ""
        return s.replace(" ", "").upper()

    d = _norm_chains(design)
    f = _norm_chains(fixed)
    if d:
        params["design"] = d
    if f:
        params["fixed"] = f

    params["ts"] = int(time.time())

    # Always include all params, even if some are blank
    # Ensure all keys are present for: temp, num, pdb, homomer, design, fixed
    for key in ["pdb", "design", "fixed"]:
        if key not in params:
            params[key] = ""

    # Append '?' + encoded params to COLAB_URL
    href = COLAB_URL + "?" + urlencode(params)
    param_str = "?" + urlencode(params)
    return href, param_str


# ---- Client-side: open the already-built URL in a new tab ----
clientside_callback(
    """
    function(href, n) {
      // Open Colab in a new tab and pass parameters via the NEW window's window.name
      if (!href || !n) { return ""; }
      try {
        // Parse params from href (already built server-side)
        const u = new URL(href, window.location.href);
        const params = Object.fromEntries(u.searchParams.entries());

        // Open new tab
        const win = window.open(href, "_blank");

        // Write params to the NEW window's name (not the current window)
        if (win) {
          try { win.name = JSON.stringify(params); } catch (e) {}
        } else {
          console.warn("Popup blocked: please allow popups for this site.");
        }
      } catch (e) {
        console.error("Failed to open Colab with window.name handoff:", e);
        try { window.location.href = href; } catch (_) {}
      }
      return "";
    }
    """,
    Output("colab-launch-dummy", "children"),
    Input("proteinmpnn-colab-link", "href"),
    State("open-proteinmpnn-colab", "n_clicks"),
    prevent_initial_call=True,
)


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


# ---- Clipboard copy clientside callback ----
clientside_callback(
    """
    function(n, text) {
      if (!n) { return ""; }
      try {
        if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text || "");
          return "✅ Parameters copied to clipboard.";
        }
      } catch (e) {}
      return "⚠️ Copy failed. Please select and copy manually.";
    }
    """,
    Output("proteinmpnn-copy-status", "children"),
    Input("proteinmpnn-copy-btn", "n_clicks"),
    State("proteinmpnn-param-string", "value"),
    { "prevent_initial_call": True }
)