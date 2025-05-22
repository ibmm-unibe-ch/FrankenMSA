import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from pandas import DataFrame

dash.register_page(
    __name__,
)


def make_siderbar():

    sidebar = html.Div(
        [
            dbc.Nav(
                [
                    dbc.NavLink("Filter", id="edit-filter", active="exact"),
                    dbc.NavLink("Sort", id="edit-sort", active="exact"),
                    dbc.NavLink("Slice & Crop", id="edit-crop", active="exact"),
                    # dbc.NavLink(
                    #     "Free Table Editor", id="edit-table-editor", active="exact"
                    # ),
                    # dbc.NavLink("Run Python Code", id="edit-python", active="exact"),
                    dbc.NavLink(
                        "Separate Query Sequence",
                        id="edit-separate-query",
                        active="exact",
                    ),
                    dbc.NavLink(
                        "Duplicate MSA",
                        id="edit-copy",
                        active="exact",
                    ),
                    dbc.NavLink(
                        "Rename MSA",
                        id="edit-rename",
                        active="exact",
                    ),
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
                vertical=True,
                pills=True,
            ),
        ],
        className="sidebar",
    )
    return sidebar


def layout():
    sidebar = make_siderbar()
    body = html.Div(id="edit-main-content", className="main-next-to-sidebar")

    layout = html.Div(
        [
            body,
            sidebar,
        ],
        className="gradient-background",
        style={
            "display": "flex",
            "flex-direction": "column",
            # "align-items": "stretch",
            "padding-top": "0px",
            # "height": "100vh",y
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
        # print("Clearing MSA data")
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
        # print(f"Deleting MSA data: {msa_name}")
        msa_data.pop(msa_name, None)
        if main_msa == msa_name:
            if len(msa_data):
                main_msa = next(iter((msa_data.keys())))
            else:
                main_msa = None
        # print("main is now: ", main_msa)
        return msa_data, main_msa
    else:
        return dash.no_update, dash.no_update


@callback(
    Output("edit-main-content", "children"),
    Input("edit-filter", "n_clicks"),
    Input("edit-crop", "n_clicks"),
    Input("edit-sort", "n_clicks"),
    Input("edit-rename", "n_clicks"),
    # Input("edit-table-editor", "n_clicks"),
    # Input("edit-python", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
)
def update_edit_content(
    filter_clicks,
    crop_clicks,
    sort_clicks,
    rename_clicks,
    # table_editor_clicks,
    # python_clicks,
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
    elif triggered_id == "edit-rename":
        return rename_layout()
    # elif triggered_id == "edit-table-editor":
    #     return table_editor_layout()
    # elif triggered_id == "edit-python":
    #     return html.Div("Python code layout")
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
    return html.Div(
        [
            gapsfilter_layout(),
            hhfilter_layout(),
            free_query_filter_layout(),
        ]
    )


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
        persistence_type="session",
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
        persistence_type="session",
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
        persistence_type="session",
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
        persistence_type="session",
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
        persistence_type="session",
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
        persistence_type="session",
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
            top_row,
            sliders,
            bottom_row,
        ],
        style={"padding": "20px"},
        className="shaded-bordered",
    )
    return layout


def free_query_filter_layout():
    upper = html.Div(
        [
            html.H1("Free Query"),
            html.P(
                "Use the DataFrame.query(...) interface to filter the MSA in any way you like."
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
            ),
            html.Button(
                "Filter MSA",
                id="free-query-filter-button",
                n_clicks=0,
                className="button-component",  # "btn btn-primary",
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
    Input("free-query-filter-button", "n_clicks"),
    State("free-query-filter-input", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_free_query_filter(n_clicks, query_string, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            # print("No MSA data available to filter.")
            return dash.no_update

        from pandas import DataFrame

        # print("Running Free Query Filter with the following parameters:")
        # print(f"query_string: {query_string}")
        # print(f"msa_data: {msa_data}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        filtered_msa = msa.query(query_string)
        # print("Filtered MSA:")
        msa_data[main_msa] = filtered_msa.to_dict("list")
        return msa_data
    else:
        # print("No button click detected.")
        return dash.no_update


@callback(
    Output("msa-data", "data", allow_duplicate=True),
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
            return dash.no_update

        from frankenmsa.filter.hhsuite import hhfilter
        from pandas import DataFrame

        # print("Running HHFilter with the following parameters:")
        # print(f"diff: {diff}")
        # print(f"max_pairwise_identity: {max_pairwise_identity}")
        # print(f"min_query_coverage: {min_query_coverage}")
        # print(f"min_query_identity: {min_query_identity}")
        # print(f"min_query_score: {min_query_score}")
        # print(f"target_diversity: {target_diversity}")
        # print(f"msa_data: {msa_data}")

        # print("DEBUG WARNING: HHFIlter is disabled for work on macbook!")
        from time import sleep

        sleep(5)
        # msa = msa_data[main_msa]
        # msa = DataFrame.from_dict(msa)
        # filtered_msa = hhfilter(
        #     msa,
        #     diff=diff,
        #     max_pairwise_identity=max_pairwise_identity,
        #     min_query_coverage=min_query_coverage,
        #     min_query_identity=min_query_identity,
        #     min_query_score=min_query_score,
        #     target_diversity=target_diversity,
        # )
        # msa_data[main_msa] = msa.to_dict("list")
        # # print("Filtered MSA:")
        # return filtered_msa.to_json()
        return msa_data

    else:
        # print("No button click detected.")
        return dash.no_update


@callback(
    Output("msa-data", "data", allow_duplicate=True),
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
            return "No MSA data available to filter."

        from frankenmsa.utils.msatools import filter_gaps
        from pandas import DataFrame

        # print("Running GapsFilter with the following parameters:")
        # print(f"gap: {gap}")
        # print(f"msa_data: {msa_data}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        filtered_msa = filter_gaps(msa, allowed_gaps_faction=gap / 100)
        msa_data[main_msa] = filtered_msa.to_dict("list")
        # print("Filtered MSA:")
        return msa_data
    else:
        # print("No button click detected.")
        return dash.no_update


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
            # print("No MSA data available to drop duplicates.")
            return dash.no_update

        from frankenmsa.utils.msatools import drop_duplicates
        from pandas import DataFrame

        # print("Dropping duplicates with the following parameters:")
        # print(f"msa_data: {msa_data}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        filtered_msa = drop_duplicates(msa)
        msa_data[main_msa] = filtered_msa.to_dict("list")
        # print("Filtered MSA:")
        return msa_data
    else:
        # print("No button click detected.")
        return dash.no_update


# ======================================================================
# Sort layout
# ======================================================================


def sort_by_layout():
    return html.Div(
        [
            sort_special_layout(),
            sort_by_column_layout(),
        ],
    )


def sort_special_layout():
    return html.Div(
        [
            html.H1("Sort by MSA Properties"),
            html.P("Sort the MSA by special properties such as sequence identity."),
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
                    dcc.RadioItems(
                        id="sort-special-order-radio",
                        options=[
                            {"label": "Ascending", "value": "asc"},
                            {"label": "Descending", "value": "desc"},
                        ],
                        value="desc",
                        labelStyle={"display": "block"},
                        style={"flex": "1", "margin-right": "10px"},
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
            # print("No MSA data available to sort by identity.")
            return dash.no_update

        from frankenmsa.utils.msatools import sort_identity
        from pandas import DataFrame

        # print("Sorting MSA by identity with the following parameters:")
        # print(f"sort_order: {sort_order}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        sorted_msa = sort_identity(msa, ascending=(sort_order == "asc"))
        msa_data[main_msa] = sorted_msa.to_dict("list")
        # print("Sorted MSA:")
        return msa_data
    else:
        # print("No button click detected.")
        return dash.no_update


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("sort-special-gaps-button", "n_clicks"),
    Input("sort-special-order-radio", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def sort_by_gaps(n_clicks, sort_order, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            # print("No MSA data available to sort by gaps.")
            return dash.no_update

        from frankenmsa.utils.msatools import sort_gaps
        from pandas import DataFrame

        # print("Sorting MSA by gaps with the following parameters:")
        # print(f"sort_order: {sort_order}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        sorted_msa = sort_gaps(msa, ascending=(sort_order == "asc"))
        msa_data[main_msa] = sorted_msa.to_dict("list")
        return msa_data
    else:
        # print("No button click detected.")
        return dash.no_update


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
            return dash.no_update

        from pandas import DataFrame
        import pandas as pd

        # print("Sorting MSA with the following parameters:")
        # print(f"sort_by: {sort_by}")
        # print(f"sort_order: {sort_order}")
        # print(f"msa_data: {msa_data}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        query = msa.iloc[0]
        msa = msa.iloc[1:]
        sorted_msa = msa.sort_values(by=sort_by, ascending=(sort_order == "asc"))
        sorted_msa = pd.concat([query, sorted_msa], ignore_index=True)
        msa_data[main_msa] = sorted_msa.to_dict("list")
        return msa_data
    else:
        # print("No button click detected.")
        return dash.no_update


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
    return html.Div(
        [
            slice_msa_layout(),
            set_depth_layout(),
            set_sequence_length_layout(),
        ],
    )


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
        persistence_type="session",
    )

    slice_button = html.Button(
        "Slice MSA",
        id="slice-button",
        n_clicks=0,
        className="button-component",
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
            range_slider,
            html.Div(
                [
                    html.Div(slice_status, style={"flex": "1", "textAlign": "left"}),
                    html.Div(slice_button, style={"flex": "1", "textAlign": "right"}),
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
    Output("slice-status-text", "children"),
    Input("main-msa", "data"),
    Input("msa-data", "data"),
    # prevent_initial_call=True,
)
def update_range_slider(main_msa, msa_data):
    # print("Updating range slider")
    if not msa_data:
        return 0, {}, [0, 0], dash.no_update

    msa = msa_data[main_msa]
    msa = DataFrame.from_dict(msa)
    max_length = msa["sequence"].str.len().max()

    marks = {i: str(i) for i in range(0, max_length + 1, max(1, max_length // 10))}
    return (
        max_length,
        marks,
        [0, max_length],
        f"Select a range to slice (0 to {max_length})",
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("slice-button", "n_clicks"),
    Input("slice-range-slider", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def slice_msa(n_clicks, range_value, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            # print("No MSA data available to slice.")
            return dash.no_update

        from pandas import DataFrame

        # print("Slicing MSA with the following parameters:")
        # print(f"range_value: {range_value}")
        # print(f"msa_data: {msa_data}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        from frankenmsa.utils.msatools import slice_sequences

        sliced_msa = slice_sequences(msa, range_value[0], range_value[1])
        # print("Sliced MSA:")
        msa_data[main_msa] = sliced_msa.to_dict("list")
        return msa_data

    else:
        # print("No button click detected.")
        return dash.no_update


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
    Input("set-depth-button", "n_clicks"),
    Input("set-depth-input", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def set_depth(n_clicks, depth, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data:
            # print("No MSA data available to set depth.")
            return dash.no_update

        from pandas import DataFrame

        # print("Setting MSA depth with the following parameters:")
        # print(f"depth: {depth}")
        # print(f"msa_data: {msa_data}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        from frankenmsa.utils.msatools import adjust_depth

        new_msa = adjust_depth(msa, depth)
        msa_data[main_msa] = new_msa.to_dict("list")
        # print("New MSA:")
        return msa_data
    else:
        # print("No button click detected.")
        return dash.no_update


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
    Input("match-query-length-button", "n_clicks"),
    Input("pad-longest-sequence-button", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def set_sequence_length(n_clicks_match, n_clicks_pad, main_msa, msa_data):
    if (n_clicks_match or n_clicks_pad or 0) > 0:
        if not msa_data:
            # print("No MSA data available to set sequence length.")
            return dash.no_update

        from pandas import DataFrame

        # print("Setting MSA sequence length with the following parameters:")
        # print(f"msa_data: {msa_data}")
        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        from frankenmsa.utils.msatools import unify_length

        if n_clicks_match > 0:
            mode = "first"
        else:
            mode = "max"

        new_msa = unify_length(msa, mode)
        # print("New MSA:")
        msa_data[main_msa] = new_msa.to_dict("list")
        return msa_data
    else:
        # print("No button click detected.")
        return dash.no_update


def rename_layout():
    return html.Div(
        [
            html.H1("Rename MSA"),
            html.P("Rename the current MSA"),
            dcc.Input(
                id="rename-input",
                type="text",
                placeholder="New MSA",
                className="input-component",
                style={"width": "50%"},
            ),
            html.Button(
                "Rename",
                id="rename-button",
                n_clicks=0,
                className="button-component",
            ),
        ],
        className="shaded-bordered",
    )


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
            # print("No MSA data available to rename.")
            return dash.no_update, dash.no_update

        from pandas import DataFrame

        # print("Renaming MSA with the following parameters:")
        # print(f"new_name: {new_name}")
        # print(f"msa_data: {msa_data}")

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        msa_data[new_name] = msa.to_dict("list")
        del msa_data[main_msa]
        # print("Renamed MSA:")
        return new_name, msa_data
    else:
        # print("No button click detected.")
        return dash.no_update, dash.no_update


@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Output("msa-data", "data", allow_duplicate=True),
    Input("edit-copy", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def copy_msa(n_clicks, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            # print("No MSA data available to copy.")
            return dash.no_update, dash.no_update

        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)

        n_present = sum(1 for i in msa_data if i.startswith(main_msa))
        new_msa_name = f"{main_msa}_{n_present + 1}"
        msa_data[new_msa_name] = msa.to_dict("list")
        # print("New MSA:")
        return new_msa_name, msa_data
    else:
        # print("No button click detected.")
        return dash.no_update, dash.no_update


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("edit-separate-query", "n_clicks"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def separate_query(n_clicks, main_msa, msa_data):
    if (n_clicks or 0) > 0:
        if not msa_data or not main_msa:
            # print("No MSA data available to separate query.")
            return dash.no_update

        from pandas import DataFrame

        msa = msa_data[main_msa]
        msa = DataFrame.from_dict(msa)
        query = msa.iloc[0]
        msa = msa.iloc[1:]

        query_name = main_msa + "_query"
        qdict = query.to_dict()
        qdict = {i: [v] for i, v in qdict.items()}
        msa_data[query_name] = qdict
        print(msa_data[query_name])
        msa_data[main_msa] = msa.to_dict("list")

    return msa_data
