import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from pandas import DataFrame

dash.register_page(
    __name__,
)


def make_siderbar():

    dup_tooltip = dbc.Tooltip(
        "Duplicate the current MSA and store it in a new MSA with the name '..._N' where N is the next available number.",
        target="edit-copy",
    )
    delete_tooltip = dbc.Tooltip(
        "Delete the currently selected MSA. This will remove it from the list of MSAs and delete all associated data.",
        target="edit-delete",
    )
    clear_tooltip = dbc.Tooltip(
        "Clear all MSA data. This will remove all MSAs and their associated data from the application.",
        target="edit-clear",
    )
    sidebar = html.Div(
        [
            dbc.Nav(
                [
                    dbc.NavLink("Filter", id="edit-filter", active="exact"),
                    dbc.NavLink("Sort & Shuffle", id="edit-sort", active="exact"),
                    dbc.NavLink("Slice & Crop", id="edit-crop", active="exact"),
                    dbc.NavLink("Edit Sequences", id="edit-sequences", active="exact"),
                    dbc.NavLink(
                        "Delete MSA",
                        id="edit-delete",
                        active="exact",
                        className="text-danger",
                    ),
                    dbc.NavLink(
                        "Clear All MSA Data",
                        id="edit-clear",
                        active="exact",
                        className="text-danger",
                    ),
                ],
                vertical=False,
                pills=True,
                style={"width": "100%"},
            ),
            dup_tooltip,
            delete_tooltip,
            clear_tooltip,
        ],
        className="header",
        style={
            "height": "50px",
            "margin-top": "0px",
        },
    )
    return sidebar


def layout():
    sidebar = make_siderbar()
    body = html.Div(
        msa_overview_layout(), id="edit-main-content", className="main-next-to-sidebar"
    )

    layout = html.Div(
        [
            dbc.Row([sidebar]),
            html.Div(
                # className="header",
                style={
                    "position": "absolute",
                    "top": "00px",
                    "left": "0",
                    "right": "0",
                    "height": "60px",
                    "width": "100vw",
                    "backgroundColor": "#2c2c2c",
                    "marginLeft": "calc(-50vw + 50%)",
                    "zIndex": "-1",
                },
            ),
            dbc.Row(body),
        ],
        className="gradient-background",
        style={
            "display": "flex",
            "flex-direction": "column",
            "padding-top": "0px",
            "position": "relative",
        },
    )
    return layout


@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Input("edit-clear", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def clear_msa_data(n_clicks, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        return None, {}
    else:
        return dash.no_update, dash.no_update


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("main-msa", "data", allow_duplicate=True),
    Input("edit-delete", "n_clicks"),
    State("select-main-msa", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def delete_msa_data(n_clicks, msa_name, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        msa_data.pop(msa_name, None)
        if main_msa == msa_name:
            if len(msa_data):
                main_msa = next(iter((msa_data.keys())))
            else:
                main_msa = None
        return msa_data, main_msa
    else:
        return dash.no_update, dash.no_update


@callback(
    Output("edit-main-content", "children"),
    Input("edit-filter", "n_clicks"),
    Input("edit-crop", "n_clicks"),
    Input("edit-sort", "n_clicks"),
    Input("edit-sequences", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
)
def update_edit_content(
    filter_clicks,
    crop_clicks,
    sort_clicks,
    sequences_clicks,
    main_msa,
    msa_data,
):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "edit-filter":
        return filter_layout()
    elif triggered_id == "edit-crop":
        return slice_crop_layout()
    elif triggered_id == "edit-sort":
        return sort_by_layout()
    elif triggered_id == "edit-sequences":
        return edit_sequences_layout()
    elif main_msa is None:
        return no_msa_yet()
    else:
        return html.Div("Please select an option from the sidebar to edit the MSA.")


def no_msa_yet():
    return dbc.Alert(
        "No MSA data is available to edit. Please upload or generate MSA data to proceed.",
        color="warning",
        className="shaded-bordered",
        is_open=True,
    )


@callback(
    Output("edit-main-content", "children", allow_duplicate=True),
    Input("edit-filter", "n_clicks"),
    State("main-msa", "data"),
    prevent_initial_call=True,
)
def activate_filter_layout(n_clicks, msa_data):
    if (n_clicks or 0) > 0:
        if msa_data is not None:
            return filter_layout()
        else:
            return no_msa_yet()
    else:
        raise dash.exceptions.PreventUpdate


# ======================================================================
# Filter layout
# ======================================================================


def filter_layout():
    top = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Row(gapsfilter_layout()),
                    dbc.Row(regex_filter_layout()),
                    dbc.Row(free_query_filter_layout()),
                ],
                style={
                    "display": "flex",
                    "flex-direction": "column",
                    "align-items": "stretch",
                    "justify-content": "space-between",
                    "width": "100%",
                },
            ),
            dbc.Col(
                hhfilter_layout(),
            ),
        ],
    )
    return top


def gapsfilter_layout():

    title = html.H1("Filter the MSA to remove gaps")

    gap_input_label = html.P(
        "Maximum gap percentage (0-100):",
        style={
            "textAlign": "center",
            "font-size": "16px",
            "margin-top": "10px",
            "margin-bottom": "10px",
        },
    )
    gap_input = dcc.Slider(
        id="gapsfilter-gap",
        value=50,
        min=0,
        max=100,
        step=1,
        marks={
            0: "0",
            25: "25",
            50: "50",
            75: "75",
            100: "100",
        },
        className="input-component",
        persistence=True,
        persistence_type="memory",
        tooltip={"placement": "bottom", "always_visible": True},
    )

    filter_button = html.Button(
        "Filter MSA",
        id="gapsfilter-button",
        n_clicks=0,
        className="button-component",  # "btn btn-primary",
    )
    filter_status = html.Div(
        [
            dcc.Loading(
                id="gapsfilter-loading",
                type="circle",
                children=html.Div(id="gapsfilter-status-text"),
                color="white",
            )
        ],
        style={
            "margin-top": "20px",
            "textAlign": "center",
        },
    )

    bottom_row = html.Div(
        [
            html.Div(filter_status, style={"flex": "1", "textAlign": "left"}),
            html.Div(filter_button, style={"flex": "1", "textAlign": "right"}),
        ],
        style={
            "display": "flex",
            "justify-content": "space-between",
            "margin-top": "20px",
        },
    )

    layout = html.Div(
        [title, gap_input_label, gap_input, bottom_row],
        style={"padding": "20px"},
        className="shaded-bordered",
    )
    return layout


def hhfilter_layout():

    title = html.H1("Filter the MSA with HHFilter")
    descr = dcc.Markdown(
        """
Use HHFilter from HH-Suite by [Soeding et al. (2019)](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-019-3019-7) to filter the MSA based on sequence homology.
You can find more information about the parameters in the [HHFilter documentation](https://github.com/soedinglab/hh-suite/wiki#hhfilter--filter-an-msa).
"""
    )

    diff_input_label = html.P(
        "Sequence diversity factor (0-10000):",
        style={
            "textAlign": "center",
            "font-size": "16px",
            "margin-top": "10px",
            "margin-bottom": "10px",
        },
    )
    diff_input = dcc.Input(
        id="hhfilter-diff",
        type="number",
        value=10,
        min=0,
        max=10000,
        step=1,
        className="input-component",
    )

    max_pairwise_identity_input_label = html.P(
        "Maximum pairwise sequence identity (0-100):",
        style={
            "textAlign": "center",
            "font-size": "16px",
            "margin-top": "10px",
            "margin-bottom": "10px",
        },
    )
    max_pairwise_identity_input_label = html.P(
        "Maximum pairwise sequence identity (0-100):",
        style={
            "textAlign": "center",
            "font-size": "16px",
            "margin-top": "10px",
            "margin-bottom": "10px",
        },
    )
    max_pairwise_identity_input = dcc.Slider(
        id="hhfilter-max-pairwise-identity",
        value=100,
        min=0,
        max=100,
        step=1,
        marks={
            0: "0",
            25: "25",
            50: "50",
            75: "75",
            100: "100",
        },
        className="input-component",
        persistence=True,
        persistence_type="memory",
        tooltip={"placement": "bottom", "always_visible": True},
    )
    min_query_coverage_input_label = html.P(
        "Minimum coverage with query sequence (0-100):",
        style={
            "textAlign": "center",
            "font-size": "16px",
            "margin-top": "10px",
            "margin-bottom": "10px",
        },
    )
    min_query_coverage_input = dcc.Slider(
        id="hhfilter-min-query-coverage",
        value=50,
        min=0,
        max=100,
        step=1,
        marks={
            0: "0",
            25: "25",
            50: "50",
            75: "75",
            100: "100",
        },
        className="input-component",
        persistence=True,
        persistence_type="memory",
        tooltip={"placement": "bottom", "always_visible": True},
    )
    min_query_identity_input_label = html.P(
        "Minimum sequence identity with query sequence (0-100):",
        style={
            "textAlign": "center",
            "font-size": "16px",
            "margin-top": "10px",
            "margin-bottom": "10px",
        },
    )
    min_query_identity_input = dcc.Slider(
        id="hhfilter-min-query-identity",
        value=0,
        min=0,
        max=100,
        step=1,
        marks={
            0: "0",
            25: "25",
            50: "50",
            75: "75",
            100: "100",
        },
        className="input-component",
        persistence=True,
        persistence_type="memory",
        tooltip={"placement": "bottom", "always_visible": True},
    )
    min_query_score_input_label = html.P(
        "Minimum sequence score with query sequence (-100 to 100):",
        style={
            "textAlign": "center",
            "font-size": "16px",
            "margin-top": "10px",
            "margin-bottom": "10px",
        },
    )
    min_query_score_input = dcc.Slider(
        id="hhfilter-min-query-score",
        value=-20,
        min=-100,
        max=100,
        step=1,
        marks={
            -100: "-100",
            -50: "-50",
            0: "0",
            50: "50",
            100: "100",
        },
        className="input-component",
        persistence=True,
        persistence_type="memory",
        tooltip={"placement": "bottom", "always_visible": True},
    )
    target_diversity_input_label = html.P(
        "Target diversity (1-10000):",
        style={
            "textAlign": "center",
            "font-size": "16px",
            "margin-top": "10px",
            "margin-bottom": "10px",
        },
    )
    target_diversity_input = dcc.Input(
        id="hhfilter-target-diversity",
        type="number",
        value=1,
        min=1,
        max=10000,
        step=1,
        className="input-component",
        persistence=True,
        persistence_type="memory",
    )

    filter_button = html.Button(
        "Filter MSA",
        id="hhfilter-button",
        n_clicks=0,
        className="button-component",  # "btn btn-primary",
    )
    filter_status = dcc.Loading(
        [
            html.Div(
                id="hhfilter-loading",
            )
        ],
        style={
            "margin-top": "20px",
            "textAlign": "center",
        },
    )

    # Top row: Number inputs
    top_row = html.Div(
        [
            html.Div(
                [
                    html.Div(diff_input_label, style={"margin-bottom": "5px"}),
                    diff_input,
                ],
            ),
            html.Div(
                [
                    html.Div(
                        target_diversity_input_label, style={"margin-bottom": "5px"}
                    ),
                    target_diversity_input,
                ],
            ),
        ],
        style={
            "display": "flex",
            "flex-direction": "row",
            "align-items": "bottom",
            "justify-content": "space-between",
        },
    )

    # Middle rows: Slider inputs
    sliders = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        max_pairwise_identity_input_label,
                        style={"margin-bottom": "5px"},
                    ),
                    max_pairwise_identity_input,
                ],
                style={"margin-bottom": "20px"},
            ),
            html.Div(
                [
                    html.Div(
                        min_query_coverage_input_label, style={"margin-bottom": "5px"}
                    ),
                    min_query_coverage_input,
                ],
                style={"margin-bottom": "20px"},
            ),
            html.Div(
                [
                    html.Div(
                        min_query_identity_input_label, style={"margin-bottom": "5px"}
                    ),
                    min_query_identity_input,
                ],
                style={"margin-bottom": "20px"},
            ),
            html.Div(
                [
                    html.Div(
                        min_query_score_input_label, style={"margin-bottom": "5px"}
                    ),
                    min_query_score_input,
                ],
                style={"margin-bottom": "20px"},
            ),
        ],
        style={"margin-top": "20px"},
    )

    # Bottom row: Button and status
    bottom_row = html.Div(
        [
            html.Div(filter_status, style={"flex": "1", "textAlign": "left"}),
            html.Div(filter_button, style={"flex": "1", "textAlign": "right"}),
        ],
        style={
            "display": "flex",
            "justify-content": "space-between",
            "margin-top": "20px",
        },
    )

    # Combine all sections
    layout = html.Div(
        [
            title,
            descr,
            top_row,
            sliders,
            bottom_row,
        ],
        style={"padding": "20px"},
        className="shaded-bordered",
    )
    return layout


# --- Begin replacement for regex_filter_layout, run_regex_filter, and free_query_filter_layout ---
def regex_filter_layout():
    upper = html.Div(
        [
            html.H1("Filter by Regex"),
            dcc.Markdown(
                "Filter sequences in the current MSA by matching a regular expression on the `sequence` column. "
                "You can use this to select specific motifs, regions, or sequence patterns."
            ),
            dcc.Input(
                id="regex-filter-pattern",
                type="text",
                placeholder="Enter a regex pattern, e.g. ^M.*K$",
                className="input-component",
                style={"width": "100%"},
            ),
            html.Div(
                [
                    dcc.RadioItems(
                        id="regex-filter-method",
                        options=[
                            {
                                "label": "contains (anywhere in sequence)",
                                "value": "contains",
                            },
                            {
                                "label": "match (from start of sequence)",
                                "value": "match",
                            },
                        ],
                        value="contains",
                        labelStyle={"display": "block"},
                    ),
                    dcc.Checklist(
                        id="regex-filter-inverse",
                        options=[
                            {
                                "label": "Inverse match (keep non-matching sequences)",
                                "value": "inverse",
                            }
                        ],
                        value=[],
                        style={"marginTop": "8px"},
                    ),
                ],
                style={"marginTop": "12px"},
            ),
        ],
        style={"padding": "20px"},
    )
    lower = html.Div(
        [
            dcc.Loading(
                id="regex-filter-loading",
                type="circle",
                children=html.Div(id="regex-filter-status-text"),
                color="white",
            ),
            html.Button(
                "Filter by Regex",
                id="regex-filter-button",
                n_clicks=0,
                className="button-component",
            ),
        ],
        style={
            "display": "flex",
            "justify-content": "space-between",
            "margin-top": "20px",
        },
    )
    return html.Div(
        [
            upper,
            lower,
        ],
        style={"padding": "20px"},
        className="shaded-bordered",
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("regex-filter-button", "n_clicks"),
    State("regex-filter-pattern", "value"),
    State("regex-filter-method", "value"),
    State("regex-filter-inverse", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_regex_filter(n_clicks, pattern, method, inverse_flags, main_msa, msa_data):
    if (n_clicks or 0) <= 0:
        return dash.no_update, dash.no_update, False

    if not msa_data or not main_msa:
        return dash.no_update, "No data to filter!", True

    if not pattern:
        return dash.no_update, "Please enter a regex pattern.", True

    try:
        from pandas import DataFrame
        from frankenmsa.utils.msatools import filter_by_regex

        msa = msa_data[main_msa]
        msa_df = DataFrame.from_dict(msa)
        inverse = "inverse" in (inverse_flags or [])
        filtered_msa = filter_by_regex(msa_df, pattern, method=method, inverse=inverse)
        msa_data[main_msa] = filtered_msa.to_dict("list")

        mode_desc = "match" if method == "match" else "contains"
        if inverse:
            mode_desc = f"inverse {mode_desc}"

        msg = f"Regex filter applied with pattern '{pattern}' ({mode_desc})."
        return msa_data, msg, True

    except Exception as e:
        return dash.no_update, f"Regex filter failed: {e}", True


def free_query_filter_layout():
    upper = html.Div(
        [
            html.H1("Free Query"),
            dcc.Markdown(
                "Use the `DataFrame.query(...)` interface to filter the MSA in any way you like. "
                "See the [pandas documentation](https://pandas.pydata.org/docs/dev/reference/api/pandas.DataFrame.query.html) "
                "or [this blog](https://note.nkmk.me/en/python-pandas-query/) for more details and examples.",
            ),
            dcc.Input(
                id="free-query-filter-input",
                type="text",
                placeholder="Enter any valid pandas query string",
                className="input-component",
                style={"width": "100%"},
            ),
        ],
        style={"padding": "20px"},
    )
    lower = html.Div(
        [
            dcc.Loading(
                id="free-query-filter-loading",
                type="circle",
                children=html.Div(id="free-query-filter-status-text"),
                color="white",
            ),
            html.Button(
                "Filter MSA",
                id="free-query-filter-button",
                n_clicks=0,
                className="button-component",
            ),
        ],
        style={
            "display": "flex",
            "justify-content": "space-between",
            "margin-top": "20px",
        },
    )
    return html.Div(
        [
            upper,
            lower,
        ],
        style={"padding": "20px"},
        className="shaded-bordered",
    )


# --- End replacement ---


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("free-query-filter-button", "n_clicks"),
    State("free-query-filter-input", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_free_query_filter(n_clicks, query_string, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            return dash.no_update, "No data to filter!", True

        from pandas import DataFrame
        from frankenmsa.utils.msatools import filter_by_query

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        filtered_msa = filter_by_query(msa, query_string)
        msa_data[main_msa] = filtered_msa.to_dict("list")
        return msa_data, f"Filtered by '{query_string}' successfully.", True
    else:
        return dash.no_update, dash.no_update, False


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("hhfilter-button", "n_clicks"),
    State("hhfilter-diff", "value"),
    State("hhfilter-max-pairwise-identity", "value"),
    State("hhfilter-min-query-coverage", "value"),
    State("hhfilter-min-query-identity", "value"),
    State("hhfilter-min-query-score", "value"),
    State("hhfilter-target-diversity", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    background=False,
    prevent_initial_call=True,
)
def run_hhfilter(
    n_clicks,
    diff,
    max_pairwise_identity,
    min_query_coverage,
    min_query_identity,
    min_query_score,
    target_diversity,
    main_msa,
    msa_data,
):
    if (n_clicks or 0) > 0:
        if not msa_data:
            # print("No MSA data available to filter.")
            return dash.no_update, "No data to filter!", True

        try:
            from frankenmsa.filter.hhsuite import hhfilter
            from pandas import DataFrame

            msa = msa_data[main_msa]
            msa = DataFrame.from_dict(msa)
            filtered_msa = hhfilter(
                msa,
                diff=diff,
                max_pairwise_identity=max_pairwise_identity,
                min_query_coverage=min_query_coverage,
                min_query_identity=min_query_identity,
                min_query_score=min_query_score,
                target_diversity=target_diversity,
            )
            msa_data[main_msa] = msa.to_dict("list")
            # print("Filtered MSA:")
            return msa_data, "HHFilter applied successfully.", True
        except:
            return (
                dash.no_update,
                "HHFilter failed to run. Please check the parameters and make sure it is installed!",
                True,
            )

    else:
        # print("No button click detected.")
        return dash.no_update, dash.no_update, False


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("gapsfilter-button", "n_clicks"),
    State("gapsfilter-gap", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_gapsfilter(n_clicks, gap, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            # print("No MSA data available to filter.")
            return dash.no_update, "No data to filter!", True

        from frankenmsa.utils.msatools import filter_gaps
        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        filtered_msa = filter_gaps(msa, allowed_gaps_faction=gap / 100)
        msa_data[main_msa] = filtered_msa.to_dict("list")
        # print("Filtered MSA:")
        return msa_data, "Gaps filter applied successfully.", True
    else:
        # print("No button click detected.")
        return dash.no_update, dash.no_update, False


def drop_duplicates_layout():
    return html.Div(
        [
            html.H1("Drop Duplicates"),
            html.P(
                "Drop duplicate sequences from the MSA. This will keep the first occurrence of each sequence."
            ),
            html.Button(
                "Drop Duplicates",
                id="drop-duplicates-button",
                n_clicks=0,
                className="button-component",
            ),
        ],
        className="shaded-bordered",
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("drop-duplicates-button", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def drop_duplicates(n_clicks, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            return dash.no_update

        from frankenmsa.utils.msatools import drop_duplicates
        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        filtered_msa = drop_duplicates(msa)
        msa_data[main_msa] = filtered_msa.to_dict("list")
        return msa_data
    else:
        return dash.no_update


# ======================================================================
# Sort layout
# ======================================================================


def sort_special_layout():
    return html.Div(
        [
            html.H1("Sort by MSA Properties"),
            html.P("Sort the MSA by special properties such as sequence identity."),
            html.Div(
                [
                    html.Div(
                        [
                            html.Button(
                                "Sort by Sequence Identity",
                                id="sort-special-identity-button",
                                n_clicks=0,
                                className="button-component",
                            ),
                            html.Button(
                                "Sort by Gaps",
                                id="sort-special-gaps-button",
                                n_clicks=0,
                                className="button-component",
                            ),
                            html.Button(
                                "Shuffle MSA",
                                id="shuffle-button",
                                n_clicks=0,
                                className="button-component",
                            ),
                        ],
                        style={"display": "flex", "gap": "8px"},
                    ),
                    dcc.RadioItems(
                        id="sort-special-order-radio",
                        options=[
                            {"label": "Ascending", "value": "asc"},
                            {"label": "Descending", "value": "desc"},
                        ],
                        value="desc",
                        labelStyle={"display": "block"},
                        style={"margin-left": "20px"},
                    ),
                ],
                style={
                    "display": "flex",
                    "flex-direction": "row",
                    "align-items": "center",
                    "justify-content": "center",
                    "gap": "40px",
                },
            ),
        ],
        className="shaded-bordered",
    )


def shuffle_columns_layout():

    start_input = dcc.Input(
        id="shuffle-range-start",
        type="number",
        value=0,
        min=0,
        step=1,
        style={"width": "120px", "marginRight": "8px"},
    )
    end_input = dcc.Input(
        id="shuffle-range-end",
        type="number",
        value=0,
        min=0,
        step=1,
        style={"width": "120px", "marginLeft": "8px"},
    )

    range_slider = dcc.RangeSlider(
        id="shuffle-range-slider",
        min=0,
        max=0,
        step=1,
        value=[0, 0],
        marks={0: "0"},
        tooltip={"placement": "bottom", "always_visible": True},
        className="input-component",
        persistence=True,
        persistence_type="memory",
        allowCross=False,
    )
    checklist = dcc.Checklist(
        id="shuffle-preserve-gaps",
        options=[{"label": "Preserve gaps", "value": "keep"}],
        value=["keep"],
        labelStyle={"marginRight": "16px"},
        inline=True,
    )
    # Collapsible seed input section
    seed_toggle = html.Button(
        "Advanced (optional) ▼",
        id="toggle-seed-btn",
        n_clicks=0,
        style={
            "background": "none",
            "border": "none",
            "fontWeight": "bold",
            "fontSize": "1rem",
            "cursor": "pointer",
            "marginBottom": "6px",
        },
    )
    seed_collapse = dbc.Collapse(
        html.Div(
            [
                dbc.Label("Random seed:", className="mb-1"),
                dcc.Input(
                    id="shuffle-seed",
                    type="number",
                    placeholder="e.g. 42",
                    min=0,
                    step=1,
                    debounce=True,
                    style={"width": "120px"},
                ),
            ],
            style={"marginTop": "4px"},
        ),
        id="seed-collapse",
        is_open=False,
    )
    button = html.Button(
        "Apply Column Shuffle",
        id="apply-shuffle-button",
        n_clicks=0,
        className="button-component",
        style={
            "marginTop": "16px",
            "fontSize": "1.25rem",
            "fontWeight": 600,
            "padding": "14px 40px",
            "borderRadius": "8px",
            "boxShadow": "0 2px 8px rgba(43,124,255,0.08)",
        },
    )
    return html.Div(
        [
            html.H1("Column-wise Shuffle", className="section-title"),
            html.Div(
                [
                    start_input,
                    html.Div(range_slider, style={"flex": 1, "margin": "0 12px"}),
                    end_input,
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginBottom": "12px",
                },
            ),
            html.Div(checklist, style={"marginBottom": "10px"}),
            seed_toggle,
            seed_collapse,
            html.Div(button, style={"textAlign": "center"}),
        ],
        className="shaded-bordered",
    )


from dash import callback, Output, Input, State
import dash
from pandas import DataFrame


@callback(
    Output("shuffle-range-slider", "max"),
    Output("shuffle-range-slider", "marks"),
    Output("shuffle-range-slider", "value"),
    Output("shuffle-range-start", "value"),
    Output("shuffle-range-end", "value"),
    Output("shuffle-range-start", "max"),
    Output("shuffle-range-end", "max"),
    Input("main-msa", "data"),
    Input("msa-data", "data"),
    # prevent_initial_call=True,
)
def update_shuffle_range_slider(main_msa, msa_data):
    if not msa_data or not main_msa:
        return 0, {0: "0"}, [0, 0], 0, 0, 0, 0
    msa = msa_data[main_msa]
    msa = DataFrame.from_dict(msa)
    if msa.empty or "sequence" not in msa:
        return 0, {0: "0"}, [0, 0], 0, 0, 0, 0

    if "sequence" in msa and len(msa["sequence"]) > 0:
        n_cols = len(msa["sequence"].iloc[0])
    else:
        n_cols = 0
    mid = n_cols // 2
    marks = {0: "0", mid: str(mid), n_cols: str(n_cols)} if n_cols > 0 else {0: "0"}
    return n_cols, marks, [0, n_cols], 0, n_cols, n_cols, n_cols


from dash import callback, no_update, ctx


@callback(
    Output("shuffle-range-slider", "value", allow_duplicate=True),
    Output("shuffle-range-start", "value", allow_duplicate=True),
    Output("shuffle-range-end", "value", allow_duplicate=True),
    Input("shuffle-range-slider", "value"),
    Input("shuffle-range-start", "value"),
    Input("shuffle-range-end", "value"),
    prevent_initial_call=True,
)
def sync_shuffle_slider_and_inputs(slider_value, start_value, end_value):
    triggered = ctx.triggered_id
    if triggered == "shuffle-range-slider":
        if not slider_value or len(slider_value) != 2:
            return no_update, no_update, no_update
        return slider_value, slider_value[0], slider_value[1]
    elif triggered in ("shuffle-range-start", "shuffle-range-end"):
        if start_value is None or end_value is None:
            return no_update, no_update, no_update
        return [start_value, end_value], start_value, end_value
    else:
        return no_update, no_update, no_update


# Callback to toggle the seed collapse section
@callback(
    Output("seed-collapse", "is_open"),
    Output("toggle-seed-btn", "children"),
    Input("toggle-seed-btn", "n_clicks"),
)
def toggle_seed(n):
    if (n or 0) % 2 == 1:
        return True, "Advanced (optional) ▲"
    return False, "Advanced (optional) ▼"


def sort_by_layout():
    return html.Div(
        [
            sort_special_layout(),
            shuffle_columns_layout(),
            sort_by_column_layout(),
        ],
    )


def parse_indices_input(input_str: str) -> list[int]:
    """
    Parse a string input into a list of indices.
    Supports:
    - Individual numbers: "5" -> [5]
    - Comma-separated: "5,10,15" -> [5, 10, 15]
    - Ranges: "10-12" -> [10, 11, 12]
    - Combinations: "5,10-12,20" -> [5, 10, 11, 12, 20]

    Returns:
        list[int]: Sorted list of unique indices
    """
    if not input_str or not input_str.strip():
        return []

    indices = set()
    parts = input_str.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            # Handle range like "10-12"
            try:
                start, end = part.split("-", 1)
                start = int(start.strip())
                end = int(end.strip())
                if start > end:
                    raise ValueError(f"Invalid range: {part} (start > end)")
                indices.update(range(start, end + 1))
            except ValueError as e:
                raise ValueError(
                    f"Invalid range format: {part}. Expected format like '10-12'."
                ) from e
        else:
            # Handle single number
            try:
                indices.add(int(part))
            except ValueError:
                raise ValueError(f"Invalid number: {part}")

    return sorted(list(indices))


def edit_sequences_layout():
    return html.Div(
        [
            html.H1("Edit Sequences"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Separate Query Sequence"),
                            html.P(
                                "Remove the first sequence from the MSA and store it in a separate singleton MSA named '_query'."
                            ),
                            html.Button(
                                "Separate Query",
                                id="edit-separate-query",
                                n_clicks=0,
                                className="button-component",
                            ),
                        ],
                        width=6,
                        className="shaded-bordered",
                        style={"padding": "15px", "marginBottom": "15px"},
                    ),
                    dbc.Col(
                        [
                            html.H5("Insertions to Gaps"),
                            html.P(
                                "Replace all insertions (lowercase characters) with gaps ('-') in the MSA."
                            ),
                            html.Button(
                                "Convert Insertions to Gaps",
                                id="edit-insertions-to-gaps",
                                n_clicks=0,
                                className="button-component",
                            ),
                        ],
                        width=6,
                        className="shaded-bordered",
                        style={"padding": "15px", "marginBottom": "15px"},
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Unknown to Gaps"),
                            html.P(
                                "Replace all unknown residues ('X') with gaps ('-') in the MSA."
                            ),
                            html.Button(
                                "Convert Unknown to Gaps",
                                id="edit-unknown-to-gaps",
                                n_clicks=0,
                                className="button-component",
                            ),
                        ],
                        width=6,
                        className="shaded-bordered",
                        style={"padding": "15px", "marginBottom": "15px"},
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Replace at Position"),
                            html.P(
                                "Replace a substring in all sequences at a specified position with a new sequence."
                            ),
                            dcc.Input(
                                id="replace-at-sequence",
                                type="text",
                                placeholder="sequence to insert e.g. ACGT",
                                className="input-component",
                                style={"width": "100%", "marginBottom": "10px"},
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Position Index (start):"),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Input(
                                                id="replace-at-index",
                                                type="number",
                                                placeholder="0",
                                                min=0,
                                                className="input-component",
                                                style={"width": "100%"},
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Checklist(
                                                id="replace-at-include-query",
                                                options=[
                                                    {
                                                        "label": "Also replace in query sequence",
                                                        "value": "include",
                                                    }
                                                ],
                                                value=[],
                                                style={"marginTop": "5px"},
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ],
                                style={"marginBottom": "15px"},
                            ),
                            html.Div(
                                html.Button(
                                    "Replace",
                                    id="replace-at-button",
                                    n_clicks=0,
                                    className="button-component",
                                ),
                                style={"textAlign": "right"},
                            ),
                        ],
                        width=12,
                        className="shaded-bordered",
                        style={"padding": "15px", "marginBottom": "15px"},
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Insert at Position"),
                            html.P(
                                "Insert a sequence at a specified position in all sequences, shifting existing residues."
                            ),
                            dcc.Input(
                                id="insert-at-sequence",
                                type="text",
                                placeholder="sequence to insert e.g. ACGT",
                                className="input-component",
                                style={"width": "100%", "marginBottom": "10px"},
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Position Index (insert at):"),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Input(
                                                id="insert-at-index",
                                                type="number",
                                                placeholder="0",
                                                min=0,
                                                className="input-component",
                                                style={"width": "100%"},
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Checklist(
                                                id="insert-at-include-query",
                                                options=[
                                                    {
                                                        "label": "Also insert in query sequence",
                                                        "value": "include",
                                                    }
                                                ],
                                                value=["include"],
                                                style={"marginTop": "5px"},
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ],
                                style={"marginBottom": "15px"},
                            ),
                            html.Div(
                                html.Button(
                                    "Insert",
                                    id="insert-at-button",
                                    n_clicks=0,
                                    className="button-component",
                                ),
                                style={"textAlign": "right"},
                            ),
                        ],
                        width=12,
                        className="shaded-bordered",
                        style={"padding": "15px", "marginBottom": "15px"},
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Fix Positions to Query"),
                            html.P(
                                "Propagate residues from the query sequence to all other sequences at specified positions. These can be specified as a comma-separated list of indices or ranges; e.g., '0, 5, 10-15' would fix positions 0, 5, and all positions from 10 to 15 inclusive."
                            ),
                            dcc.Input(
                                id="fix-at-indices",
                                type="text",
                                placeholder="Positions to fix e.g., 0, 5, 10-15",
                                className="input-component",
                                style={"width": "100%", "marginBottom": "15px"},
                            ),
                            html.Div(
                                html.Button(
                                    "Fix Positions",
                                    id="fix-at-button",
                                    n_clicks=0,
                                    className="button-component",
                                ),
                                style={"textAlign": "right"},
                            ),
                        ],
                        width=12,
                        className="shaded-bordered",
                        style={"padding": "15px", "marginBottom": "15px"},
                    ),
                ]
            ),
        ],
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("sort-special-identity-button", "n_clicks"),
    Input("sort-special-order-radio", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def sort_by_identity(n_clicks, sort_order, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            return dash.no_update

        from frankenmsa.utils.msatools import sort_identity
        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        sorted_msa = sort_identity(msa, ascending=(sort_order == "asc"))
        msa_data[main_msa] = sorted_msa.to_dict("list")
        return msa_data
    else:
        return dash.no_update


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("sort-special-gaps-button", "n_clicks"),
    Input("sort-special-order-radio", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def sort_by_gaps(n_clicks, sort_order, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            return dash.no_update, "No data to sort!", True

        from frankenmsa.utils.msatools import sort_gaps
        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        sorted_msa = sort_gaps(msa, ascending=(sort_order == "asc"))
        msa_data[main_msa] = sorted_msa.to_dict("list")
        return msa_data, "Sorted by gaps successfully.", True
    else:
        return dash.no_update, dash.no_update, False


def sort_by_column_layout():
    return html.Div(
        [
            html.H1("Sort by Column"),
            html.P(
                "Sort the MSA by a specific column. You can choose to sort in ascending or descending order."
            ),
            html.Div(
                [
                    dcc.Dropdown(
                        id="sort-by-dropdown",
                        options=[],  # needs to come from callback
                        placeholder="Select a column to sort by",
                        className="dropdown-component",
                        style={"flex": "1", "margin-right": "10px"},
                    ),
                    dcc.RadioItems(
                        id="sort-order-radio",
                        options=[
                            {"label": "Ascending", "value": "asc"},
                            {"label": "Descending", "value": "desc"},
                        ],
                        value="desc",
                        labelStyle={"display": "block"},
                        style={"flex": "1", "margin-right": "10px"},
                    ),
                    html.Button(
                        "Sort MSA",
                        id="sort-button",
                        n_clicks=0,
                        className="button-component",
                        style={"flex": "1"},
                    ),
                ],
                style={
                    "display": "flex",
                    "flex-direction": "row",
                    "align-items": "center",
                    "justify-content": "space-between",
                    "width": "100%",
                },
            ),
        ],
        className="shaded-bordered",
    )


@callback(
    Output("sort-by-dropdown", "options"),
    Input("main-msa", "data"),
    State("msa-data", "data"),
)
def update_sort_by_options(main_msa, msa_data):
    if msa_data is None or not main_msa:
        return []

    # Convert the MSA data to a DataFrame
    msa = msa_data[main_msa]
    msa_df = DataFrame.from_dict(msa)

    # Get the column names
    columns = msa_df.columns.tolist()

    # Create options for the dropdown
    options = [{"label": col, "value": col} for col in columns]

    return options


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("sort-button", "n_clicks"),
    Input("sort-by-dropdown", "value"),
    Input("sort-order-radio", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def sort_msa(n_clicks, sort_by, sort_order, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            # print("No MSA data available to sort.")
            return dash.no_update, "No data to sort!", True

        from pandas import DataFrame
        from frankenmsa.utils.msatools import sort_by_column

        # print("Sorting MSA with the following parameters:")
        # print(f"sort_by: {sort_by}")
        # print(f"sort_order: {sort_order}")
        # print(f"msa_data: {msa_data}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        sorted_msa = sort_by_column(msa, sort_by, ascending=(sort_order == "asc"))
        msa_data[main_msa] = sorted_msa.to_dict("list")
        return msa_data, "Sequences sorted successfully", True
    else:
        # print("No button click detected.")
        return dash.no_update, dash.no_update, False


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("shuffle-button", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def shuffle_msa(n_clicks, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            # print("No MSA data available to shuffle.")
            return dash.no_update, "No data to shuffle!", True

        from pandas import DataFrame
        from frankenmsa.utils.msatools import shuffle_rows

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        shuffled_msa = shuffle_rows(msa)
        msa_data[main_msa] = shuffled_msa.to_dict("list")
        return msa_data, "MSA shuffled successfully.", True
    else:
        return dash.no_update, dash.no_update, False


from dash import callback, Input, Output, State
import dash


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("apply-shuffle-button", "n_clicks"),
    State("shuffle-range-start", "value"),
    State("shuffle-range-end", "value"),
    State("shuffle-preserve-gaps", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def apply_column_shuffle(n_clicks, start, end, preserve_vals, main_msa, msa_data):
    """Apply column-wise shuffle using msatools.shuffle_msa (keeps row 0 fixed)."""
    if (n_clicks or 0) <= 0:
        return dash.no_update, dash.no_update, False

    if not msa_data or not main_msa:
        return dash.no_update, "No data to shuffle!", True

    try:
        import pandas as pd
        from frankenmsa.utils.msatools import (
            shuffle_msa as shuffle_msa_cols,
            unify_length,
        )

        # Load current MSA into DataFrame
        df = pd.DataFrame.from_dict(msa_data[main_msa])

        # Ensure equal lengths (use first row length as reference)
        df = unify_length(df, "first")

        # Parse UI options
        preserve_gaps = "keep" in (preserve_vals or [])
        s = int(start) if start not in (None, "") else None
        e = int(end) if end not in (None, "") else None

        # Read seed value from kwargs (dash supplies all States as kwargs; fallback to dash.callback_context.inputs if needed)
        seed_value = dash.callback_context.inputs.get("shuffle-seed.value", None)
        if seed_value is None or seed_value == "":
            random_state = None
        else:
            random_state = int(seed_value)

        # Do the column-wise shuffle (row 0 kept fixed)
        shuffled = shuffle_msa_cols(
            df,
            start=s,
            end=e,
            preserve_gaps=preserve_gaps,
            inplace=False,
            random_state=random_state,
        )

        # Write back to store
        msa_data[main_msa] = shuffled.to_dict("list")

        # Build a small status message
        L = len(shuffled["sequence"].iloc[0])
        range_txt = f"[{0 if s is None else s}:{L if e is None else e}]"
        gap_txt = "(preserved gaps)" if preserve_gaps else "(gaps shuffled)"

        msg = f"Shuffled columns {range_txt} {gap_txt}."
        return msa_data, msg, True

    except Exception as ex:
        return dash.no_update, f"Shuffle failed: {ex}", True


# ======================================================================
# Slice & Crop layout
# ======================================================================


def slice_crop_layout():
    top = dbc.Row(
        [
            dbc.Row(
                [dbc.Col(set_depth_layout()), dbc.Col(set_sequence_length_layout())],
            ),
            dbc.Row([slice_msa_layout()], style={"width": "100%"}),
        ],
        style={
            "display": "flex",
            "flex-direction": "row",
            "align-items": "stretch",
            "justify-content": "space-between",
            "width": "100%",
        },
    )
    return top



def slice_msa_layout():
    range_slider_label = html.P(
        "Slice sequences to a specific range of indices within the alignment.",
    )

    range_slider = dcc.RangeSlider(
        id="slice-range-slider",
        min=0,
        max=0,  # This will be updated dynamically
        step=1,
        value=[0, 0],  # Default range
        marks={},  # This will be updated dynamically
        className="input-component",
        persistence=True,
        persistence_type="memory",
        tooltip={"placement": "bottom", "always_visible": True},
    )

    slice_start_input = dcc.Input(
        id="slice-range-start",
        type="number",
        value=0,
        min=0,
        step=1,
        style={"width": "60px"},
    )

    slice_end_input = dcc.Input(
        id="slice-range-end",
        type="number",
        value=0,
        min=0,
        step=1,
        style={"width": "60px"},
    )

    slice_button = html.Button(
        "Slice MSA",
        id="slice-button",
        n_clicks=0,
        className="button-component",
    )

    slice_copy_button = html.Button(
        "Slice MSA copy",
        id="slice-copy-button",
        n_clicks=0,
        className="button-component",
        style={"margin-left": "10px"},
    )

    slice_status = dcc.Loading(
        [
            html.Div(
                id="slice-status-text",
            )
        ],
        style={
            "margin-top": "20px",
            "textAlign": "center",
        },
    )

    layout = html.Div(
        [
            html.H1("Slice the MSA"),
            range_slider_label,
            dbc.Row(
                [
                    dbc.Col(slice_start_input, width="auto"),
                    dbc.Col(range_slider),
                    dbc.Col(slice_end_input, width="auto"),
                ],
                align="center",
                style={"margin-bottom": "20px"},
            ),
            html.Div(
                [
                    html.Div(slice_status, style={"flex": "1", "textAlign": "left"}),
                    html.Div(
                        [slice_button, slice_copy_button],
                        style={"flex": "1", "textAlign": "right"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "space-between",
                    "margin-top": "20px",
                },
            ),
        ],
        style={"padding": "20px"},
        className="shaded-bordered",
    )
    return layout


@callback(
    Output("slice-range-slider", "max"),
    Output("slice-range-slider", "marks"),
    Output("slice-range-slider", "value"),
    Output("slice-range-start", "value"),
    Output("slice-range-end", "value"),
    Output("slice-range-start", "max"),
    Output("slice-range-end", "max"),
    Output("slice-status-text", "children"),
    Input("main-msa", "data"),
    Input("msa-data", "data"),
    # prevent_initial_call=True,
)
def update_range_slider(main_msa, msa_data):
    # print("Updating range slider")
    if not msa_data:
        return 0, {}, [0, 0], 0, 0, 0, 0, dash.no_update

    msa = msa_data[main_msa]
    msa = DataFrame.from_dict(msa)
    max_length = msa["sequence"].str.len().max()

    marks = {i: str(i) for i in range(0, max_length + 1, max(1, max_length // 10))}
    return (
        max_length,
        marks,
        [0, max_length],
        0,
        max_length,
        max_length,
        max_length,
        f"Select a range to slice (0 to {max_length})",
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("slice-button", "n_clicks"),
    State("slice-range-slider", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def slice_msa(n_clicks, range_value, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            return dash.no_update, "No data to slice!", True

        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        from frankenmsa.utils.msatools import slice_sequences

        sliced_msa = slice_sequences(msa, range_value[0], range_value[1])
        msa_data[main_msa] = sliced_msa.to_dict("list")
        return (
            msa_data,
            f"Sliced MSA successfully to {range_value[0]}-{range_value[1]}.",
            True,
        )

    else:
        return dash.no_update, dash.no_update, False


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("slice-copy-button", "n_clicks"),
    State("slice-range-slider", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def slice_msa_copy(n_clicks, range_value, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            return dash.no_update, "No data to slice!", True

        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        from frankenmsa.utils.msatools import slice_sequences

        sliced_msa = slice_sequences(msa, range_value[0], range_value[1])

        # Create new MSA name with the format {name}_{start}_{end}
        new_msa_name = f"{main_msa}_{range_value[0]}_{range_value[1]}"

        # Ensure the name is unique
        counter = 1
        base_name = new_msa_name
        while new_msa_name in msa_data:
            new_msa_name = f"{base_name}_{counter}"
            counter += 1

        # Add the sliced MSA as a new entry
        msa_data[new_msa_name] = sliced_msa.to_dict("list")

        return (
            msa_data,
            f"Created sliced MSA copy '{new_msa_name}' with range {range_value[0]}-{range_value[1]}.",
            True,
        )

    else:
        return dash.no_update, dash.no_update, False


# Callbacks to sync input fields with slider for slice functionality
@callback(
    Output("slice-range-slider", "value", allow_duplicate=True),
    Input("slice-range-start", "value"),
    Input("slice-range-end", "value"),
    prevent_initial_call=True,
)
def update_slice_range_from_inputs(start_value, end_value):
    return [start_value, end_value]


@callback(
    Output("slice-range-start", "value", allow_duplicate=True),
    Output("slice-range-end", "value", allow_duplicate=True),
    Input("slice-range-slider", "value"),
    prevent_initial_call=True,
)
def update_slice_inputs_from_range(range_value):
    return range_value


def set_depth_layout():
    return html.Div(
        [
            html.H1("Set MSA Depth"),
            html.P(
                "Set the depth of the MSA to a specific value. This will either increase the MSA by duplicating entries (if MSA is currently smaller) or drop entries (if MSA is currently larger) to achieve the desired depth."
            ),
            dcc.Input(
                id="set-depth-input",
                type="number",
                placeholder="Enter depth",
                className="input-component",
                style={"width": "50%"},
            ),
            html.Button(
                "Set Depth",
                id="set-depth-button",
                n_clicks=0,
                className="button-component",
            ),
        ],
        className="shaded-bordered",
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("set-depth-button", "n_clicks"),
    Input("set-depth-input", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def set_depth(n_clicks, depth, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            return dash.no_update, "No data to crop or extend", True

        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        from frankenmsa.utils.msatools import adjust_depth

        old = len(msa)
        new_msa = adjust_depth(msa, depth)
        new = len(new_msa)
        msa_data[main_msa] = new_msa.to_dict("list")
        # print("New MSA:")
        return msa_data, f"Set MSA depth successfully from {old} to {new}.", True
    else:
        return dash.no_update, dash.no_update, False


def set_sequence_length_layout():
    return html.Div(
        [
            html.H1("Unify Sequence Length"),
            html.P(
                "Adjust the sequence lengths in the MSA. You can either match all sequences to the query sequence length or pad all sequences to match the longest sequence."
            ),
            html.Div(
                [
                    html.Button(
                        "Match Query Length",
                        id="match-query-length-button",
                        n_clicks=0,
                        className="button-component",
                    ),
                    html.Button(
                        "Pad to Longest Sequence",
                        id="pad-longest-sequence-button",
                        n_clicks=0,
                        className="button-component",
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "space-between",
                    "gap": "10px",
                    "width": "50%",
                },
            ),
        ],
        className="shaded-bordered",
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("match-query-length-button", "n_clicks"),
    Input("pad-longest-sequence-button", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def set_sequence_length(n_clicks_match, n_clicks_pad, main_msa, msa_data):
    if (n_clicks_match or n_clicks_pad or 0) > 0:
        if not msa_data:
            return dash.no_update, "No data to unify sequence lengths!", True

        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        from frankenmsa.utils.msatools import unify_length

        if n_clicks_match > 0:
            mode = "first"
        else:
            mode = "max"

        new_msa = unify_length(msa, mode)
        unified_length = len(new_msa.iloc[[0]]["sequence"])
        msa_data[main_msa] = new_msa.to_dict("list")
        return (
            msa_data,
            f"Unified sequence lengths to {unified_length} characters.",
            True,
        )
    else:
        return dash.no_update, dash.no_update, False


@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Input("rename-button", "n_clicks"),
    Input("rename-input", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def rename_msa(n_clicks, new_name, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            return dash.no_update, dash.no_update

        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        msa_data[new_name] = msa.to_dict("list")
        del msa_data[main_msa]
        return new_name, msa_data
    else:
        return dash.no_update, dash.no_update


@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("duplicate-button", "n_clicks"),
    State("duplicate-name-input", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def copy_msa(n_clicks, custom_name, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            return dash.no_update, dash.no_update, dash.no_update, False

        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        # Use custom name if provided, otherwise generate default name
        if custom_name and custom_name.strip():
            new_msa_name = custom_name.strip()
        else:
            n_present = sum(1 for i in msa_data if i.startswith(main_msa))
            new_msa_name = f"{main_msa}_{n_present + 1}"

        msa_data[new_msa_name] = msa.to_dict("list")
        return new_msa_name, msa_data, "Copied MSA as: " + new_msa_name, True
    else:
        return dash.no_update, dash.no_update, dash.no_update, False


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("edit-separate-query", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def separate_query(n_clicks, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            return dash.no_update, dash.no_update, False

        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        if msa.empty:
            return dash.no_update, "MSA is empty, cannot separate query.", True

        query = msa.iloc[[0]]
        msa = msa.iloc[1:]

        query_name = main_msa + "_query"
        qdict = query.to_dict()
        qdict = {i: [v] for i, v in qdict.items()}
        msa_data[query_name] = qdict
        print(msa_data[query_name]) # delete?
        msa_data[main_msa] = msa.to_dict("list")

        return msa_data, "Query separated as a new MSA named: " + query_name, True
    return dash.no_update, dash.no_update, False


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("replace-at-button", "n_clicks"),
    State("replace-at-sequence", "value"),
    State("replace-at-index", "value"),
    State("replace-at-include-query", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def replace_at_position(
    n_clicks, replacement, index, include_query_list, main_msa, msa_data
):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            return dash.no_update, "No MSA data available.", True

        if not replacement:
            return dash.no_update, "Please enter a replacement sequence.", True

        if index is None or index < 0:
            return dash.no_update, "Please enter a valid position index (>= 0).", True

        from pandas import DataFrame
        from frankenmsa.utils.msatools import replace_at

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        # Check if index is within bounds
        if msa.empty:
            return dash.no_update, "MSA is empty.", True

        max_length = msa["sequence"].str.len().max()
        if index >= max_length:
            return (
                dash.no_update,
                f"Index {index} is out of bounds. Maximum index is {max_length - 1}.",
                True,
            )

        # Convert checklist value to boolean
        include_query = "include" in include_query_list if include_query_list else False

        try:
            msa = replace_at(msa, replacement, index, include_query=include_query)
            msa_data[main_msa] = msa.to_dict("list")

            query_text = "including query" if include_query else "excluding query"
            return (
                msa_data,
                f"Replaced {len(replacement)} characters at position {index} ({query_text}).",
                True,
            )
        except Exception as e:
            return dash.no_update, f"Error: {str(e)}", True

    return dash.no_update, dash.no_update, False


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("insert-at-button", "n_clicks"),
    State("insert-at-sequence", "value"),
    State("insert-at-index", "value"),
    State("insert-at-include-query", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def insert_at_position(
    n_clicks, insertion, index, include_query_list, main_msa, msa_data
):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            return dash.no_update, "No MSA data available.", True

        if not insertion:
            return dash.no_update, "Please enter a sequence to insert.", True

        if index is None or index < 0:
            return dash.no_update, "Please enter a valid position index (>= 0).", True

        from pandas import DataFrame
        from frankenmsa.utils.msatools import insert_at

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        # Check if MSA is empty
        if msa.empty:
            return dash.no_update, "MSA is empty.", True

        max_length = msa["sequence"].str.len().max()
        if index > max_length:
            return (
                dash.no_update,
                f"Index {index} is out of bounds. Maximum index is {max_length}.",
                True,
            )

        # Convert checklist value to boolean
        include_query = "include" in include_query_list if include_query_list else False

        try:
            msa = insert_at(msa, insertion, index, include_query=include_query)
            msa_data[main_msa] = msa.to_dict("list")

            query_text = "including query" if include_query else "excluding query"
            return (
                msa_data,
                f"Inserted {len(insertion)} characters at position {index} ({query_text}).",
                True,
            )
        except Exception as e:
            return dash.no_update, f"Error: {str(e)}", True

    return dash.no_update, dash.no_update, False


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("fix-at-button", "n_clicks"),
    State("fix-at-indices", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def fix_at_positions(n_clicks, indices_str, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            return dash.no_update, "No MSA data available.", True

        if not indices_str or not indices_str.strip():
            return dash.no_update, "Please enter at least one position index.", True

        from pandas import DataFrame
        from frankenmsa.utils.msatools import fix_at

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        # Check if MSA is empty
        if msa.empty:
            return dash.no_update, "MSA is empty.", True

        # Parse indices
        try:
            indices = parse_indices_input(indices_str)
        except ValueError as e:
            return dash.no_update, f"Invalid index input: {str(e)}", True

        if not indices:
            return dash.no_update, "No valid indices provided.", True

        # Check if indices are within bounds
        max_length = msa["sequence"].str.len().max()
        invalid_indices = [idx for idx in indices if idx >= max_length or idx < 0]
        if invalid_indices:
            return (
                dash.no_update,
                f"Indices out of bounds: {invalid_indices}. Valid range: 0 to {max_length - 1}.",
                True,
            )

        try:
            msa = fix_at(msa, indices)
            msa_data[main_msa] = msa.to_dict("list")

            indices_display = ", ".join(map(str, indices[:5]))
            if len(indices) > 5:
                indices_display += f", ... ({len(indices)} total)"

            return (
                msa_data,
                f"Fixed {len(indices)} position(s) to query residues: {indices_display}",
                True,
            )
        except Exception as e:
            return dash.no_update, f"Error: {str(e)}", True

    return dash.no_update, dash.no_update, False


def msa_overview_layout():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dash_table.DataTable(
                                id="msa-overview-table",
                                columns=[
                                    {"name": "", "id": "column"},
                                    {"name": "", "id": "value"},
                                ],
                                data=[
                                    {"column": "Number of sequences", "value": 0},
                                    {"column": "Max. sequence length", "value": 0},
                                    {"column": "Min. sequence length", "value": 0},
                                    {"column": "Avg. sequence length", "value": 0},
                                    {"column": "Number of gaps", "value": 0},
                                ],
                                style_table={"overflowX": "auto"},
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            html.H5("Rename MSA"),
                            dcc.Input(
                                id="rename-input",
                                type="text",
                                placeholder="New Name",
                                className="input-component",
                                style={"width": "100%", "marginBottom": "10px"},
                            ),
                            html.Button(
                                "Rename",
                                id="rename-button",
                                n_clicks=0,
                                className="button-component",
                            ),
                        ],
                        width=4,
                        style={"paddingLeft": "20px"},
                    ),
                    dbc.Col(
                        [
                            html.H5("Duplicate MSA"),
                            dcc.Input(
                                id="duplicate-name-input",
                                type="text",
                                placeholder="New Name (optional)",
                                className="input-component",
                                style={"width": "100%", "marginBottom": "10px"},
                            ),
                            html.Button(
                                "Duplicate",
                                id="duplicate-button",
                                n_clicks=0,
                                className="button-component",
                            ),
                        ],
                        width=4,
                        style={"paddingLeft": "20px"},
                    ),
                ],
                style={"marginBottom": "20px"},
            ),
            html.H2("Consensus Sequence"),
            html.P(
                "query sequence",
                id="msa-consensus-seq",
                className="shaded-bordered",
                style={
                    "display": "inline-block",
                    "textAlign": "center",
                    "maxWidth": "1000px",
                    "width": "100%",
                    "overflow-wrap": "anywhere",
                },
            ),
        ],
    )


@callback(
    Output("msa-overview-table", "data"),
    Output("msa-consensus-seq", "children"),
    Input("main-msa", "data"),
    Input("msa-data", "data"),
)
def update_msa_overview(main_msa, msa_data):
    if not msa_data or not main_msa:
        return dash.no_update, dash.no_update

    from pandas import DataFrame

    msa = msa_data[main_msa]
    msa = DataFrame.from_dict(msa)

    if msa.empty:
        return dash.no_update, "No query sequence available."

    from frankenmsa.utils.seqtools import consensus_sequence

    consensus = consensus_sequence(msa["sequence"])

    # Calculate MSA statistics
    num_sequences = len(msa)
    max_length = msa["sequence"].str.len().max()
    min_length = msa["sequence"].str.len().min()
    avg_length = msa["sequence"].str.len().mean()
    num_gaps = (msa["sequence"].str.count("-")).sum()

    # Prepare data for the table
    overview_data = [
        {"column": "Number of sequences", "value": num_sequences},
        {"column": "Max. sequence length", "value": max_length},
        {"column": "Min. sequence length", "value": min_length},
        {"column": "Avg. sequence length", "value": avg_length},
        {"column": "Number of gaps", "value": num_gaps},
    ]

    return overview_data, consensus


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("edit-insertions-to-gaps", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def insertions_to_gaps(n_clicks, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            return dash.no_update, dash.no_update, False

        from pandas import DataFrame
        from frankenmsa.utils.msatools import replace_insertions_with_gaps

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        msa = replace_insertions_with_gaps(msa)
        msa_data[main_msa] = msa.to_dict("list")
        return (
            msa_data,
            "Inserted gaps for all lowercase characters in the sequences.",
            True,
        )
    else:
        return dash.no_update, dash.no_update, False


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("notification", "children", allow_duplicate=True),
    Output("notification", "is_open", allow_duplicate=True),
    Input("edit-unknown-to-gaps", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def unknown_to_gaps(n_clicks, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            return dash.no_update, dash.no_update, False

        from pandas import DataFrame
        from frankenmsa.utils.msatools import replace_unknown_with_gaps

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        msa = replace_unknown_with_gaps(msa)
        msa_data[main_msa] = msa.to_dict("list")

        return msa_data, "Replaced all 'X' residues with gaps in the sequences.", True
    else:
        return dash.no_update, dash.no_update, False
