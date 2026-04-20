import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
import pandas as pd
import os

from frankenmsa.align.plm_search import PLMSearch
from frankenmsa.align.workflows import (
    attach_alignment_result,
    attach_plm_search_results,
    build_result_key,
    normalize_mmseqs_input,
    parse_plm_input,
    validate_mmseqs_request,
    validate_similarity_cutoff,
)
from frankenmsa.runtime import log_message

dash.register_page(
    __name__,
)

# =============================================================================
#  UI Layout
# =============================================================================


def layout():
    return html.Div(
        [dbc.Row([mmseqs_colab_layout(), plm_search_layout()])],
        className="gradient-background",
    )


def mmseqs_colab_layout():

    return html.Div(
        [
            # 1. Title
            html.H1("MMseqs2 ColabFold", style={"marginBottom": "10px"}),
            # 2. Citation Link
            html.Div(
                [
                    html.Span("Align one or more sequences using "),
                    html.A(
                        "MMseqs2",
                        href="https://www.nature.com/articles/s41467-018-04964-5",
                        target="_blank",
                    ),
                    html.Span("."),
                ],
                style={"marginBottom": "20px", "fontSize": "1.1rem"},
            ),
            # 3. Instructions Section
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Markdown(
                                """
                        * **Monomer:** Enter sequence. Select `Pairing: None`.
                        * **Multimer:** Join chains with `:` (e.g. `AAAA:BBBB`). Select `Pairing: Greedy` or `All`.
                        """,
                                style={"color": "#444", "lineHeight": "1.6"},
                            )
                        ],
                        style={
                            "display": "inline-block",
                            "textAlign": "left",
                            "marginBottom": "5px",
                        },
                    ),
                    html.Details(
                        [
                            html.Summary(
                                "ℹ️ Click to learn about Pairing Modes (Greedy vs All)",
                                style={
                                    "cursor": "pointer",
                                    "color": "#56CCF2",
                                    "fontSize": "0.9rem",
                                    "fontWeight": "500",
                                    "marginTop": "5px",
                                },
                            ),
                            html.Div(
                                [
                                    dcc.Markdown(
                                        """
                            **Greedy (Strict):** Attempts to find the single best matching pair per species. *Warning: Often returns empty results on public servers.*
                            
                            **All (Recommended):** Finds all possible matching sequences per species. *Success rate is much higher.*
                            """,
                                        style={
                                            "fontSize": "0.9rem",
                                            "color": "#555",
                                            "marginTop": "10px",
                                            "textAlign": "left",
                                            "maxWidth": "600px",
                                            "marginLeft": "auto",
                                            "marginRight": "auto",
                                            "lineHeight": "1.5",
                                        },
                                    )
                                ]
                            ),
                        ]
                    ),
                ],
                style={"textAlign": "center", "marginBottom": "20px"},
            ),
            # 4. Input Area
            dcc.Textarea(
                id="mmseqs-input",
                placeholder="Enter sequences here...\n\nExample Multimer: AAAAA:BBBBB\nExample Monomer: AAAAA",
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
            # 5. Options Row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P(
                                "Pairing mode",
                                style={"fontWeight": "bold", "marginBottom": "10px"},
                            ),
                            dcc.RadioItems(
                                id="mmseqs-pairing-mode",
                                options=[
                                    {"label": "None (Monomer)", "value": "none"},
                                    {"label": "Greedy", "value": "greedy"},
                                    {"label": "All", "value": "complete"},
                                ],
                                value="none",
                                persistence=True,
                                persistence_type="memory",
                                inline=True,
                                inputStyle={"marginRight": "5px", "marginLeft": "10px"},
                                labelStyle={"marginRight": "15px"},
                            ),
                            html.Small(
                                [
                                    html.Span("💡 Tip: ", style={"color": "#56CCF2"}),
                                    html.Strong("All", style={"color": "#444"}),
                                    html.Span(
                                        " is recommended.", style={"color": "#666"}
                                    ),
                                ],
                                style={
                                    "display": "block",
                                    "marginTop": "8px",
                                    "fontSize": "0.85rem",
                                },
                            ),
                        ],
                        width=6,
                        style={"textAlign": "center", "paddingRight": "20px"},
                    ),
                    dbc.Col(
                        [
                            html.P(
                                "Use Filtering",
                                style={"fontWeight": "bold", "marginBottom": "10px"},
                            ),
                            dcc.RadioItems(
                                id="mmseqs-filter-mode",
                                options=[
                                    {"label": "Yes", "value": True},
                                    {"label": "No", "value": False},
                                ],
                                value=True,
                                persistence=True,
                                persistence_type="memory",
                                inline=True,
                                inputStyle={"marginRight": "5px", "marginLeft": "10px"},
                                labelStyle={"marginRight": "15px"},
                            ),
                            html.Small(
                                "Remove low-complexity regions.",
                                className="text-muted",
                                style={
                                    "display": "block",
                                    "marginTop": "8px",
                                    "fontSize": "0.85rem",
                                },
                            ),
                        ],
                        width=6,
                        style={
                            "textAlign": "center",
                            "borderLeft": "1px solid #ddd",
                            "paddingLeft": "20px",
                        },
                    ),
                ],
                className="g-0",
                style={
                    "marginTop": "30px",
                    "marginBottom": "30px",
                    "width": "80%",
                    "marginLeft": "auto",
                    "marginRight": "auto",
                    "alignItems": "start",
                },
            ),
            # 5. Run Button
            html.Button(
                "Run MMseqs2",
                id="mmseqs-run-button",
                n_clicks=0,
                className="button-component",
                style={
                    "width": "80%",
                    "fontSize": "16px",
                    "fontWeight": "bold",
                    "padding": "12px",
                },
            ),
            html.Div(
                html.Small(
                    "Output files (Main MSA + split chains) will be available in the file selector after computation.",
                    style={"color": "#888", "fontSize": "0.85rem"},
                ),
                style={"marginTop": "10px", "marginBottom": "5px"},
            ),
            # 6. Output / Status
            dcc.Loading(
                html.Div(
                    id="mmseqs-output",
                    className="output-component",
                    style={
                        "marginTop": "10px",
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


def plm_search_layout():
    return html.Div(
        [
            # 1. Title
            html.H1("PLM-Search", style={"marginBottom": "10px"}),
            # 2. Citation Link
            html.Div(
                [
                    html.Span("Find similar sequences using "),
                    html.A(
                        "PLM-Search",
                        href="https://www.nature.com/articles/s41467-024-46808-5",
                        target="_blank",
                    ),
                    html.Span(". Please cite the paper if you use this feature. \n"),
                    html.Span(
                        "Downloading sequences might take some time, we advise to use sensible cutoffs for similarity or max sequences per query."
                    ),
                ],
                style={
                    "marginBottom": "20px",
                    "fontSize": "1.1rem",
                    "whiteSpace": "normal",
                    "overflowWrap": "break-word",
                    "wordBreak": "break-word",
                },
            ),
            # 3. Instructions Section
            html.Div(
                [
                    dcc.Markdown(
                        """
                    Enter one or more sequences to search for similar proteins in the database.
                    Results will include sequences with similarity above the cutoff.
                    """,
                        style={"color": "#444", "lineHeight": "1.6"},
                    )
                ],
                style={"textAlign": "center", "marginBottom": "20px"},
            ),
            # 4. Input Area
            dcc.Textarea(
                id="plm-input",
                placeholder="Enter sequences here...\nExample:\n>seq1\nAAAA\n>seq2\nCCCCC",
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
            # 5. Options Row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P(
                                "Database",
                                style={"fontWeight": "bold", "marginBottom": "10px"},
                            ),
                            dcc.Dropdown(
                                id="plm-database",
                                options=[
                                    {"label": "UniRef50", "value": "uniref50"},
                                    {"label": "PDB", "value": "PDB"},
                                    {"label": "Swiss-Prot", "value": "Swiss-Prot"},
                                ],
                                value="uniref50",
                                persistence=True,
                                persistence_type="memory",
                            ),
                            html.Small(
                                "Which PLM-Search database to query.",
                                className="text-muted",
                                style={
                                    "display": "block",
                                    "marginTop": "8px",
                                    "fontSize": "0.85rem",
                                },
                            ),
                        ],
                        width=4,
                        style={"textAlign": "center", "paddingRight": "20px"},
                    ),
                    dbc.Col(
                        [
                            html.P(
                                "Similarity Cutoff",
                                style={"fontWeight": "bold", "marginBottom": "10px"},
                            ),
                            dcc.Input(
                                id="plm-similarity-cutoff",
                                type="number",
                                min=0.0,
                                max=1.0,
                                step=0.05,
                                value=0.9,
                                persistence=True,
                                persistence_type="memory",
                                style={"width": "80%"},
                            ),
                            html.Small(
                                "Minimum similarity to include in results.",
                                className="text-muted",
                                style={
                                    "display": "block",
                                    "marginTop": "8px",
                                    "fontSize": "0.85rem",
                                },
                            ),
                        ],
                        width=4,
                        style={
                            "textAlign": "center",
                            "borderLeft": "1px solid #ddd",
                            "paddingLeft": "20px",
                        },
                    ),
                    dbc.Col(
                        [
                            html.P(
                                "Max sequences per query",
                                style={"fontWeight": "bold", "marginBottom": "10px"},
                            ),
                            dcc.Slider(
                                id="plm-max-sequences",
                                min=1,
                                max=1000,
                                step=1,
                                value=200,
                                persistence=True,
                                persistence_type="memory",
                                marks={
                                    1: "1",
                                    200: "200",
                                    500: "500",
                                    700: "700",
                                    1000: "1000",
                                },
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": False,
                                },
                            ),
                            html.Small(
                                "Max number of similar sequences to return per query.",
                                className="text-muted",
                                style={
                                    "display": "block",
                                    "marginTop": "8px",
                                    "fontSize": "0.85rem",
                                },
                            ),
                        ],
                        width=4,
                        style={
                            "textAlign": "center",
                            "borderLeft": "1px solid #ddd",
                            "paddingLeft": "20px",
                        },
                    ),
                ],
                className="g-0",
                style={
                    "marginTop": "30px",
                    "marginBottom": "30px",
                    "width": "80%",
                    "marginLeft": "auto",
                    "marginRight": "auto",
                    "alignItems": "start",
                },
            ),
            # 6. Run Button
            html.Button(
                "Run PLM-Search",
                id="plm-run-button",
                n_clicks=0,
                className="button-component",
                style={
                    "width": "80%",
                    "fontSize": "16px",
                    "fontWeight": "bold",
                    "padding": "12px",
                },
            ),
            # 7. Output / Status
            dcc.Loading(
                html.Div(
                    id="plm-output",
                    className="output-component",
                    style={
                        "marginTop": "10px",
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
    Output("mmseqs-output", "children"),
    Input("mmseqs-run-button", "n_clicks"),
    State("mmseqs-input", "value"),
    State("mmseqs-pairing-mode", "value"),
    State("mmseqs-filter-mode", "value"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_mmseqs(n_clicks, input_data, pairing_mode, filter_mode, msa_data):
    """
    Execute MMseqs2 alignment and store results in msa_data.

    Validates input, handles monomers and multimers, submits to API,
    and splits multimer results by chain.
    """
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        full_sequence = normalize_mmseqs_input(input_data)
        is_multimer = validate_mmseqs_request(full_sequence, pairing_mode)
    except ValueError as exc:
        return dash.no_update, dash.no_update, dbc.Alert(str(exc), color="danger")

    # 3. Execute alignment
    try:
        multimer_header_str = None
        chain_lengths = []

        if is_multimer:
            from frankenmsa.align import LocalMMSeqs2Colab

            runner = LocalMMSeqs2Colab()
            msa_df, header_str, chain_lengths = runner.align(
                full_sequence, pairing_mode
            )
            multimer_header_str = header_str
            chains_count = full_sequence.count(":") + 1
            base_name = f"mmseqs_multimer_{chains_count}chains"
        else:
            from frankenmsa.align import MMSeqs2Colab

            runner = MMSeqs2Colab("frankenmsa-gui")
            msa_df = runner.align([full_sequence], True, filter_mode, None)
            base_name = "mmseqs"

        new_main_key = build_result_key(msa_data, base_name)
        msa_data = attach_alignment_result(
            msa_data,
            new_main_key,
            msa_df,
            multimer_header_str=multimer_header_str,
        )

        # 5. Handle multimer chain splitting
        if is_multimer and chain_lengths:
            from frankenmsa.utils.seqtools import multimer_chain_splitting

            split_msg, msa_data = multimer_chain_splitting(
                msa_df, chain_lengths, new_main_key
            )
        else:
            split_msg = ""
        msg = f"Success! Generated {new_main_key}.{split_msg}"
        return new_main_key, msa_data, dbc.Alert(msg, color="success")

    except Exception as e:
        import traceback

        traceback.print_exc()
        return (
            dash.no_update,
            dash.no_update,
            dbc.Alert(f"API Error: {str(e)}", color="danger"),
        )


@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Output("plm-output", "children"),
    Input("plm-run-button", "n_clicks"),
    State("plm-input", "value"),
    State("plm-database", "value"),
    State("plm-similarity-cutoff", "value"),
    State("plm-max-sequences", "value"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_plm_search(
    n_clicks, input_data, database, similarity_cutoff, max_sequences, msa_data
):
    """
    Execute PLM-Search query and store results in msa_data.

    Validates input, parses FASTA format, submits query to PLM-Search API,
    and organizes results by query sequence.
    """
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        sequences, descriptions = parse_plm_input(input_data)
        validate_similarity_cutoff(similarity_cutoff)

        # 3. Initialize msa_data if needed
        if not isinstance(msa_data, dict):
            msa_data = {}

        # 4. Execute PLM-Search
        runner = PLMSearch()
        log_message(
            f"Running PLM-Search with {len(sequences)} query sequences, database={database}, similarity_cutoff={similarity_cutoff}, max_sequences={max_sequences}"
        )
        df = runner.align(
            sequences, descriptions, database, similarity_cutoff, max_sequences
        )
        log_message(f"PLM-Search returned {len(df)} results.")
        if df is None or df.empty:
            return (
                dash.no_update,
                dash.no_update,
                dbc.Alert(
                    "No results found with the given similarity cutoff.",
                    color="warning",
                ),
            )

        # 5. Store results organized by query sequence
        msa_data, main_key, new_keys = attach_plm_search_results(msa_data, df)
        total_results = len(df)
        num_queries = len(df["query"].unique())

        msg = (
            f"Found {total_results} results from {num_queries} "
            f"{'query' if num_queries == 1 else 'queries'}. "
            f"Generated {len(new_keys)} MSA file(s)."
        )

        return main_key, msa_data, dbc.Alert(msg, color="success")

    except Exception as e:
        import traceback

        traceback.print_exc()
        error_msg = str(e)
        return (
            dash.no_update,
            dash.no_update,
            dbc.Alert(f"API Error: {error_msg}", color="danger"),
        )
