import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State

dash.register_page(
    __name__,
)


def make_siderbar():

    sidebar = html.Div(
        [
            dbc.Nav(
                [
                    dbc.NavLink("Filter", id="edit-filter", active="exact"),
                    dbc.NavLink("Slice & Crop", id="edit-crop", active="exact"),
                    dbc.NavLink(
                        "Free Table Editor", id="edit-table-editor", active="exact"
                    ),
                    dbc.NavLink("Run Python Code", id="edit-python", active="exact"),
                    dbc.NavLink(
                        "Clear MSA Data",
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
            # "height": "100vh",
        },
    )
    print("Edit page layout created")
    return layout


@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Input("edit-clear", "n_clicks"),
    State("main-msa", "data"),
    prevent_initial_call=True,
)
def clear_msa_data(n_clicks, msa_data):
    if (n_clicks or 0) > 0:
        print("Clearing MSA data")
        return None
    else:
        return dash.no_update


@callback(
    Output("edit-main-content", "children"),
    Input("edit-filter", "n_clicks"),
    Input("edit-crop", "n_clicks"),
    Input("edit-table-editor", "n_clicks"),
    Input("edit-python", "n_clicks"),
    State("main-msa", "data"),
)
def update_edit_content(
    filter_clicks, crop_clicks, table_editor_clicks, python_clicks, msa_data
):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "edit-filter":
        return filter_layout()
    elif triggered_id == "edit-crop":
        return html.Div("Crop layout")
    elif triggered_id == "edit-table-editor":
        return html.Div("Table editor layout")
    elif triggered_id == "edit-python":
        return html.Div("Python code layout")
    elif msa_data is None:
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


def filter_layout():

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
        id="filter-diff",
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
        id="filter-max-pairwise-identity",
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
        id="filter-min-query-coverage",
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
        id="filter-min-query-identity",
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
        id="filter-min-query-score",
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
        id="filter-target-diversity",
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
        id="filter-button",
        n_clicks=0,
        className="button-component",  # "btn btn-primary",
    )
    filter_status = html.Div(
        [
            dcc.Loading(
                id="filter-loading",
                type="circle",
                children=html.Div(id="filter-status-text"),
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
    )
    return layout


@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Input("filter-button", "n_clicks"),
    State("filter-diff", "value"),
    State("filter-max-pairwise-identity", "value"),
    State("filter-min-query-coverage", "value"),
    State("filter-min-query-identity", "value"),
    State("filter-min-query-score", "value"),
    State("filter-target-diversity", "value"),
    State("main-msa", "data"),
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
    msa_data,
):
    if (n_clicks or 0) > 0:
        if not msa_data:
            print("No MSA data available to filter.")
            return None

        from frankenmsa.filter.hhsuite import hhfilter
        from pandas import DataFrame

        print("Running HHFilter with the following parameters:")
        print(f"diff: {diff}")
        print(f"max_pairwise_identity: {max_pairwise_identity}")
        print(f"min_query_coverage: {min_query_coverage}")
        print(f"min_query_identity: {min_query_identity}")
        print(f"min_query_score: {min_query_score}")
        print(f"target_diversity: {target_diversity}")
        print(f"msa_data: {msa_data}")

        print("DEBUG WARNING: HHFIlter is disabled for work on macbook!")
        # msa_data = DataFrame.from_dict(msa_data)
        # filtered_msa = hhfilter(
        #     msa_data,
        #     diff=diff,
        #     max_pairwise_identity=max_pairwise_identity,
        #     min_query_coverage=min_query_coverage,
        #     min_query_identity=min_query_identity,
        #     min_query_score=min_query_score,
        #     target_diversity=target_diversity,
        # )
        # print("Filtered MSA:")
        # return filtered_msa.to_json()
        return msa_data

    else:
        print("No button click detected.")
        return dash.no_update
