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
                "Cluster sequences based on their similarity. Clusters can be saved as new MSAs to be used in downstream tasks."
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
                className="shaded-bordered",
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
    Input("main-msa", "data"),
    Input("msa-data", "data"),
)
def afcluster_controls(
    main_msa,
    msa_data,
):
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
        value=0.5,
        min=0,
        max=10,
        step=0.1,
        persistence=True,
        persistence_type="memory",
    )
    epsilon_tooltip = dbc.Tooltip(
        "Epsilon value for DBSCAN. The maximum distance between two samples for them to be considered as in the same neighborhood.",
        target="epsilon",
        placement="bottom",
    )
    epsilon_label = html.Label(
        "Epsilon",
        id="epsilon-label",
    )
    search_epsilon_button = html.Button(
        "Search for best epsilon",
        id="search-epsilon",
        className="button-component",
        n_clicks=0,
    )
    search_epsilon_tooltip = dbc.Tooltip(
        "Search for the best epsilon value for DBSCAN to maximize the number of clusters. This will take longer to run.",
        target="search-epsilon",
        placement="bottom",
    )
    search_epsilon_value_range_slider = dcc.RangeSlider(
        id="search-epsilon-value-range",
        min=1,
        max=100,
        step=0.5,
        value=[3, 20],
        marks={i: str(i) for i in range(1, 101, 10)},
        persistence=True,
        persistence_type="session",
    )
    search_epsilon_value_range_tooltip = dbc.Tooltip(
        "Range of epsilon values to search for the best value. A gridsearch is performed to find the best value.",
        target="search-epsilon-value-range",
        placement="bottom",
    )
    search_epsilon_value_range_label = html.Label(
        "Epsilon value range",
        id="search-epsilon-value-range-label",
        style={"margin-left": "10px"},
    )

    search_epsilon_value_step_input = dcc.Input(
        id="search-epsilon-value-step",
        type="number",
        placeholder="Epsilon value step",
        value=0.5,
        min=0.01,
        max=10,
        step=0.01,
        persistence=True,
        persistence_type="session",
    )
    search_epsilon_value_step_tooltip = dbc.Tooltip(
        "Step size to use when performing the gridsearch for the best epsilon values. Smaller values will cause the search to run for longer.",
        target="search-epsilon-value-step",
        placement="bottom",
    )
    search_epsilon_value_step_label = html.Label(
        "Epsilon value step",
        id="search-epsilon-value-step-label",
        style={"margin-left": "10px"},
    )
    run_button = html.Button(
        "Run AFCluster",
        id="run-afcluster-button",
        className="button-component",
        style={"margin-top": "20px"},
        n_clicks=0,
    )
    save_clusters = html.Button(
        "Save Clusters",
        id="save-clusters-button",
        className="button-component",
        style={"margin-top": "20px"},
        n_clicks=0,
    )
    toprow = dbc.Row(
        [
            dbc.Col(
                [
                    min_samples_tooltip,
                    min_samples_label,
                    min_samples,
                ]
            ),
            dbc.Col(
                [
                    epsilon_tooltip,
                    epsilon_label,
                    epsilon,
                ]
            ),
        ],
        style={
            "margin-top": "20px",
            "align-items": "center",
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
                    search_epsilon_value_range_tooltip,
                    search_epsilon_value_range_label,
                    search_epsilon_value_range_slider,
                ],
            ),
            dbc.Col(
                [
                    search_epsilon_value_step_tooltip,
                    search_epsilon_value_step_label,
                    search_epsilon_value_step_input,
                ],
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
            dbc.Col(search_epsilon_button),
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
    Output("epsilon", "value"),
    Output("cluster-visual-container", "children", allow_duplicate=True),
    Input("search-epsilon", "n_clicks"),
    State("search-epsilon-value-range", "value"),
    State("search-epsilon-value-step", "value"),
    State("min-samples", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def search_epsilon(
    n_clicks,
    search_epsilon_value_range,
    search_epsilon_value_step,
    min_samples,
    main_msa,
    msa_data,
):
    if not (n_clicks or 0) > 0:
        return dash.no_update, dash.no_update

    if not msa_data or not main_msa:
        return dash.no_update, no_msa_yet()

    from frankenmsa.cluster import AFCluster

    clusterer = AFCluster()

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)

    best_eps = clusterer.gridsearch_eps(
        msa,
        min_eps=search_epsilon_value_range[0],
        max_eps=search_epsilon_value_range[1],
        step=search_epsilon_value_step,
        min_samples=min_samples,
    )

    return best_eps, html.Div()


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("run-afcluster-button", "n_clicks"),
    State("min-samples", "value"),
    State("epsilon", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_afcluster(
    n_clicks,
    min_samples,
    epsilon,
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
        consensus_sequence=False,
        levenshtein=False,
    )

    msa_data[main_msa] = msa.to_dict()
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
            size=10,
            line=dict(width=2),
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
        msa_data[name] = subset.to_dict()

    info = f"Saved {len(msa['cluster_id'].unique())} clusters to MSA data."
    return msa_data, dbc.Alert(
        info,
        color="success",
        is_open=True,
    )
