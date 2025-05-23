import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
import pandas as pd


dash.register_page(
    __name__,
)


def layout():
    return html.Div(
        [
            html.H1("Cluster Sequences with AFCluster"),
            html.P(
                "Cluster sequences based on their similarity. Clusters can be saved as new MSAs to be used in downstream tasks. Once clustering is performed a 'cluster_id' column is added to the current MSA which can be obtained by downloading the MSA as CSV."
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            id="cluster-controls-container",
                            className="shaded-bordered",
                        ),
                    ),
                    dbc.Col(dcc.Loading(html.Div(id="cluster-visual-container"))),
                ]
            ),
            html.Div(
                id="cluster-save-container",
                # className="shaded-bordered",
            ),
        ],
        className="gradient-background",
    )


def no_msa_yet():
    return dbc.Alert(
        "No MSA data is available to cluster. Please upload or generate MSA data to proceed.",
        color="warning",
        className="shaded-bordered",
        is_open=True,
    )


@callback(
    Output("cluster-controls-container", "children"),
    Input("cluster-controls-container", "children"),
)
def afcluster_controls(_):
    min_samples = dcc.Input(
        id="min-samples",
        type="number",
        placeholder="Minimum samples per cluster",
        value=5,
        min=1,
        max=1000,
        step=1,
        persistence=True,
        persistence_type="session",
    )
    min_samples_tooltip = dbc.Tooltip(
        "Minimum number of samples per cluster. Clusters with fewer samples will be ignored.",
        target="min-samples",
        placement="bottom",
    )

    min_samples_label = html.Label(
        "Samples",
    )

    epsilon = dcc.Input(
        id="epsilon",
        type="number",
        placeholder="Epsilon value for DBSCAN",
        value=0.50,
        min=0.01,
        max=1000.0,
        persistence=True,
        persistence_type="session",
    )
    epsilon_tooltip = dbc.Tooltip(
        "Epsilon value for DBSCAN. The maximum distance between two samples for them to be considered as in the same neighborhood. The range slider below can be used to set this value as well.",
        target="epsilon",
        placement="bottom",
    )
    epsilon_label = html.Label(
        "Epsilon",
        id="epsilon-label",
    )
    search_epsilon_value_range_slider = dcc.Slider(
        id="search-epsilon-value-range",
        min=1,
        max=100,
        step=0.5,
        value=3,
        marks={i: str(i) for i in range(1, 101, 10)},
        persistence=True,
        persistence_type="session",
    )

    search_epsilon_value_range_label = html.Label(
        "Epsilon value range",
        id="search-epsilon-value-range-label",
        style={"margin-left": "10px"},
    )
    search_epsilon_value_range_start_input = dcc.Input(
        id="search-epsilon-value-range-start",
        type="number",
        placeholder="Epsilon value start",
        value=3,
        min=1,
        max=100,
        step=0.5,
        persistence=True,
        persistence_type="session",
    )
    search_epsilon_value_range_start_tooltip = dbc.Tooltip(
        "Start value of the epsilon range slider.",
        target="search-epsilon-value-range-start",
        placement="bottom",
    )
    search_epsilon_value_range_end_input = dcc.Input(
        id="search-epsilon-value-range-end",
        type="number",
        placeholder="Epsilon value end",
        value=20,
        min=1,
        max=100,
        step=0.5,
        persistence=True,
        persistence_type="session",
    )
    search_epsilon_value_range_end_tooltip = dbc.Tooltip(
        "End value of the epsilon range slider.",
        target="search-epsilon-value-range-end",
        placement="bottom",
    )

    run_button = html.Button(
        "Run AFCluster",
        id="run-afcluster-button",
        className="button-component",
        style={"margin-top": "20px"},
        n_clicks=0,
    )
    save_clusters = html.Button(
        "Save Clusters as separate MSAs",
        id="save-clusters-button",
        className="button-component",
        style={"margin-top": "20px"},
        n_clicks=0,
    )

    other_columns_to_include = dcc.Dropdown(
        id="afcluster-other-columns",
        options=[],
        value=[],
        multi=True,
        className="dropdown-component",
        placeholder="Other columns...",
    )
    other_columns_to_include_tooltip = dbc.Tooltip(
        "Optionally, select other columns whose data to include during clustering. These columns have to be numeric. By default only the 'sequence' column is considered (this is the only non-numeric column allowed).",
        target="afcluster-other-columns",
        placement="top",
    )
    other_columns_to_include_label = html.Label(
        "Other columns to include",
        id="afcluster-other-columns-label",
    )
    toprow = dbc.Row(
        [
            dbc.Col(
                [
                    min_samples_tooltip,
                    min_samples_label,
                    min_samples,
                ],
                width="auto",
            ),
            dbc.Col(
                [
                    epsilon_tooltip,
                    epsilon_label,
                    epsilon,
                ],
                width="auto",
            ),
            dbc.Col(
                [
                    other_columns_to_include_tooltip,
                    # other_columns_to_include_label,
                    other_columns_to_include,
                ],
                # width="auto",
            ),
        ],
        style={
            "margin": "20px",
            "align-items": "bottom",
            "justify-contents": "center",
            "display": "flex",
            "flex-direction": "row",
            "flex-wrap": "wrap",
        },
    )
    midrow = dbc.Row(
        [
            dbc.Col(
                [
                    # search_epsilon_value_range_start_label,
                    search_epsilon_value_range_start_tooltip,
                    search_epsilon_value_range_start_input,
                ],
                width="auto",
            ),
            dbc.Col(
                [
                    search_epsilon_value_range_label,
                    search_epsilon_value_range_slider,
                ],
            ),
            dbc.Col(
                [
                    # search_epsilon_value_range_end_label,
                    search_epsilon_value_range_end_tooltip,
                    search_epsilon_value_range_end_input,
                ],
                width="auto",
            ),
        ],
        style={
            "margin": "20px",
            "align-items": "center",
            "justify-contents": "center",
            "display": "flex",
            "flex-direction": "row",
            # "flex-wrap": "wrap",
        },
    )
    bottomrow = dbc.Row(
        [
            dbc.Col(
                run_button,
            ),
            dbc.Col(
                save_clusters,
            ),
        ]
    )
    return html.Div(
        [toprow, midrow, bottomrow],
    )


@callback(
    Output("search-epsilon-value-range", "value"),
    Input("search-epsilon-value-range-start", "value"),
    Input("search-epsilon-value-range-end", "value"),
    State("search-epsilon-value-range", "value"),
)
def update_search_epsilon_value_range(new_start, new_end, current_value):
    if not new_start or not new_end:
        return dash.no_update

    if new_start >= new_end:
        return dash.no_update

    if current_value is None:
        return (new_start + new_end) / 2

    if current_value < new_start or current_value > new_end:
        return (new_start + new_end) / 2

    return dash.no_update


@callback(
    Output("search-epsilon-value-range", "min"),
    Output("search-epsilon-value-range", "max"),
    Input("search-epsilon-value-range-start", "value"),
    Input("search-epsilon-value-range-end", "value"),
)
def update_search_epsilon_value_range_min_max(
    search_epsilon_value_range_start,
    search_epsilon_value_range_end,
):
    if not search_epsilon_value_range_start or not search_epsilon_value_range_end:
        return dash.no_update, dash.no_update

    if search_epsilon_value_range_start >= search_epsilon_value_range_end:
        return dash.no_update, dash.no_update

    return search_epsilon_value_range_start, search_epsilon_value_range_end


@callback(
    Output("epsilon", "value"),
    Input("search-epsilon-value-range", "value"),
    prevent_initial_call=True,
)
def update_epsilon_value_from_slider(search_epsilon_value_range):
    return search_epsilon_value_range


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("run-afcluster-button", "n_clicks"),
    State("min-samples", "value"),
    State("epsilon", "value"),
    State("afcluster-other-columns", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_afcluster(
    n_clicks,
    min_samples,
    epsilon,
    columns_to_include,
    main_msa,
    msa_data,
):
    if not (n_clicks or 0) > 0:
        return dash.no_update

    if not msa_data or not main_msa:
        return dash.no_update

    from frankenmsa.cluster import AFCluster

    clusterer = AFCluster()

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)

    msa = clusterer.cluster(
        msa,
        min_samples=min_samples,
        eps=epsilon,
        columns=(columns_to_include or None),
        consensus_sequence=False,
        levenshtein=False,
    )

    msa_data[main_msa] = msa.to_dict("list")
    return msa_data


@callback(
    Output("cluster-visual-container", "children"),
    Input("msa-data", "data"),
    Input("main-msa", "data"),
)
def visualise_clusters(
    msa_data,
    main_msa,
):
    if not msa_data or not main_msa:
        return no_msa_yet()

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)
    if "cluster_id" not in msa.columns:
        return dbc.Alert("No clusters found. Please run AFCluster first.")

    return pca_plot(msa)


def pca_plot(msa):
    from sklearn.decomposition import PCA
    from afcluster.af_cluster import _seqs_to_onehot
    import plotly.express as px

    df = msa.copy()

    # prepare sequences
    query = df.iloc[:1]
    df = df.iloc[1:]
    seqs_onehot = _seqs_to_onehot(
        df["sequence"].values,
        max_len=len(query["sequence"].values[0]),
    )

    # PCA
    kwargs = {}
    kwargs.pop("random_state", None)
    kwargs.setdefault("n_components", 2)
    pca = PCA(random_state=42, **kwargs)
    embedding = pca.fit_transform(seqs_onehot)

    df["PC 1"] = embedding[:, 0]
    df["PC 2"] = embedding[:, 1]

    query_onehot = _seqs_to_onehot(
        query["sequence"].values,
        max_len=len(query["sequence"].values[0]),
    )
    query_embedding = pca.transform(query_onehot)
    query["PC 1"] = query_embedding[:, 0]
    query["PC 2"] = query_embedding[:, 1]

    fig = px.scatter(
        df,
        x="PC 1",
        y="PC 2",
        color="cluster_id",
        hover_name="header",
        title="PCA of Clusters",
        template="plotly_white",
        color_continuous_scale="deep",
    )

    fig_query = px.scatter(
        query,
        x="PC 1",
        y="PC 2",
        hover_name="header",
        color_discrete_sequence=["red"],
        title="PCA of Clusters",
        template="plotly_white",
    )
    fig_query.update_traces(
        marker=dict(
            size=20,
        ),
    )
    fig.add_trace(
        fig_query.data[0],
    )
    return dcc.Graph(
        id="pca-plot",
        figure=fig,
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("cluster-save-container", "children"),
    Input("save-clusters-button", "n_clicks"),
    State("msa-data", "data"),
    State("main-msa", "data"),
    prevent_initial_call=True,
)
def save_clusters(
    n_clicks,
    msa_data,
    main_msa,
):
    if not (n_clicks or 0) > 0:
        return dash.no_update, dash.no_update

    if not msa_data or not main_msa:
        return dash.no_update, dash.no_update

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)

    if "cluster_id" not in msa.columns:
        return dash.no_update, dbc.Alert(
            "No clusters found. Please run AFCluster first."
        )

    for cluster_id, subset in msa.groupby("cluster_id"):

        name = f"{main_msa}_cluster_{cluster_id}"
        msa_data[name] = subset.to_dict("list")

    info = f"Saved {len(msa['cluster_id'].unique())} clusters to MSA data."
    return msa_data, dbc.Alert(
        info,
        color="success",
        is_open=True,
    )


@callback(
    Output("afcluster-other-columns", "options"),
    Input("msa-data", "data"),
    State("main-msa", "data"),
)
def update_other_columns_options(msa_data, main_msa):
    if not msa_data or not main_msa:
        return dash.no_update

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)

    columns = msa.select_dtypes(include=["number"]).columns.tolist()

    # Create options for the dropdown
    options = [{"label": col, "value": col} for col in columns]

    return options
