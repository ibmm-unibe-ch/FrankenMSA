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
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Row(afcluster_layout()),
                            dbc.Row(kmeans_layout()),
                        ],
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Encoding",
                                            style={"fontWeight": "600", "marginRight": "8px"},
                                        ),
                                        dbc.RadioItems(
                                            id="visualise-encoding",
                                            options=[
                                                {"label": "onehot", "value": "onehot"},
                                                {"label": "esm", "value": "esm"},
                                            ],
                                            value="onehot",
                                            inline=True,
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center", "gap": "8px", "padding": "8px 0"},
                                ),
                            ),
                            dcc.Loading(
                                html.Div(
                                    id="cluster-visual-container",
                                    className="shaded-bordered",
                                ),
                                color="white",
                            ),
                            html.Div(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="clusters-to-save-dropdown",
                                                    options=[],
                                                    value=[],
                                                    multi=True,
                                                    className="dropdown-component",
                                                    placeholder="Select clusters to save",
                                                    style={
                                                        "height": "44px",
                                                        "alignSelf": "center",
                                                        "width": "280px",
                                                        "margin": "0",
                                                        "boxSizing": "border-box",
                                                    },
                                                ),
                                                width=True,
                                            ),
                                            dbc.Col(
                                                html.Button(
                                                    "Save Selected Clusters",
                                                    id="save-selected-clusters-button",
                                                    className="button-component",
                                                    n_clicks=0,
                                                    style={
                                                        "height": "44px",
                                                        "lineHeight": "44px",
                                                        "alignSelf": "center",
                                                        "padding": "0 18px",
                                                        "width": "240px",
                                                        "margin": "0",
                                                        "boxSizing": "border-box",
                                                    },
                                                ),
                                                width="auto",
                                            ),
                                        ],
                                        style={
                                            "alignItems": "center",
                                            "justifyContent": "center",
                                            "display": "flex",
                                            "gap": "8px",
                                            "marginTop": "4px",
                                            "marginBottom": "4px",
                                        },
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="ward-clusters-to-save-dropdown",
                                                    options=[],
                                                    value=[],
                                                    multi=True,
                                                    className="dropdown-component",
                                                    placeholder="Select ward clusters to save",
                                                    style={
                                                        "height": "44px",
                                                        "alignSelf": "center",
                                                        "width": "280px",
                                                        "margin": "0",
                                                        "boxSizing": "border-box",
                                                    },
                                                ),
                                                width=True,
                                            ),
                                            dbc.Col(
                                                html.Button(
                                                    "Save Ward Clusters",
                                                    id="save-ward-selected-clusters-button",
                                                    className="button-component",
                                                    n_clicks=0,
                                                    style={
                                                        "height": "44px",
                                                        "lineHeight": "44px",
                                                        "alignSelf": "center",
                                                        "padding": "0 18px",
                                                        "width": "240px",
                                                        "margin": "0",
                                                        "boxSizing": "border-box",
                                                    },
                                                ),
                                                width="auto",
                                            ),
                                        ],
                                        style={
                                            "alignItems": "center",
                                            "justifyContent": "center",
                                            "display": "flex",
                                            "gap": "8px",
                                            "marginTop": "4px",
                                            "marginBottom": "4px",
                                        },
                                    ),
                                ],
                                id="save-clusters-container",
                                className="shaded-bordered",
                            ),
                        ],
                    ),
                ]
            )
        ],
        className="gradient-background",
    )


def afcluster_layout():
    return html.Div(
        [
            html.H1("Cluster Sequences with AFCluster"),
            dcc.Markdown(
                "Cluster sequences based on their similarity using `DBSCAN` as done by [Wayment-Steele et al. (2024)](https://www.nature.com/articles/s41586-023-06832-9) in `AF-Cluster`. Clusters can be saved as new MSAs to be used in downstream tasks. Once clustering is performed a 'cluster_id' column is added to the current MSA which can be obtained by downloading the MSA as CSV."
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            id="cluster-controls-container",
                        ),
                    )
                ]
            ),
            html.Div(
                id="cluster-save-container",
            ),
            ward_controls_layout(),
        ],
        className="shaded-bordered",
    )


def ward_controls_layout():
    header = html.H4("Ward-Linking")

    explain = dcc.Markdown(
        "After `AF-Cluster` assigns cluster_id, merge clusters hierarchically using "
        "[Agglomerative (Ward) linkage](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html) "
        "on cluster centroids. For an application to AF-based conformational ensembles, see "
        "[Piomponi et al., 2025](https://pubs.acs.org/doi/10.1021/acs.jcim.5c01090)."
    )

    # centered controls: label + slider with min/max display
    top_controls = dbc.Row(
        [
            dbc.Col(
                dcc.Input(
                    id="ward-n-clusters-min-box",
                    type="number",
                    value=2,
                    min=2,
                    max=100,
                    style={"width": "80px"},
                ),
                width="auto",
            ),
            dbc.Col(
                [
                    html.Label(
                        "Final number of clusters",
                        style={
                            "textAlign": "center",
                            "display": "block",
                            "marginBottom": "6px",
                            "fontWeight": "600",
                        },
                    ),
                    dcc.Slider(
                        id="ward-n-clusters-slider",
                        min=2,
                        max=15,
                        step=1,
                        value=3,
                        marks={2: "2", 50: "50", 100: "100"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    dcc.Input(
                        id="ward-n-clusters",
                        type="number",
                        value=3,
                        min=2,
                        max=15,
                        step=1,
                        style={"marginTop": "8px", "width": "100px"},
                    ),
                ],
                width=True,
            ),
            dbc.Col(
                dcc.Input(
                    id="ward-n-clusters-max-box",
                    type="number",
                    value=15,
                    min=3,
                    max=200,
                    # allow user to edit max so slider bounds follow both boxes
                    disabled=False,
                    style={"width": "80px"},
                ),
                width="auto",
            ),
        ],
        style={
            "margin": "20px",
            "alignItems": "center",
            "justifyContent": "center",
            "display": "flex",
            "gap": "12px",
        },
    )

    # big button below, full width (similar to Run AFCluster)
    bottom_button = dbc.Row(
        html.Button(
            "Run Ward-Linking",
            id="run-ward-linking-button",
            className="button-component",
            n_clicks=0,
        ),
        style={"width": "100%"},
    )

    return html.Div([html.Hr(), header, explain, top_controls, bottom_button])


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
        persistence_type="memory",
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
        persistence_type="memory",
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
        persistence_type="memory",
        tooltip={"placement": "bottom", "always_visible": True},
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
        persistence_type="memory",
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
        persistence_type="memory",
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
                    other_columns_to_include,
                ],
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
        },
    )
    bottomrow = dbc.Row(
        run_button,
        style={"width": "100%"},
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
    State("visualise-encoding", "value"),
)
def visualise_clusters(msa_data, main_msa, encoding):
    if not msa_data or not main_msa:
        return no_msa_yet()
    df = pd.DataFrame.from_dict(msa_data[main_msa])
    if "cluster_id" not in df.columns:
        return dbc.Alert("No clusters found. Please run AFCluster first.")

    graphs = []
    graphs.append(
        pca_plot(
            df,
            graph_id="pca-af",
            title="PCA of AFCluster Clusters",
            color_col="cluster_id",
            encoding=encoding,
        )
    )

    if "ward_id" in df.columns:
        graphs.append(
            pca_plot(
                df,
                graph_id="pca-ward",
                title="PCA of Ward-merged Clusters",
                color_col="ward_id",
                encoding=encoding,
            )
        )

    return html.Div(graphs)

@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("run-ward-linking-button", "n_clicks"),
    State("ward-n-clusters", "value"),
    State("msa-data", "data"),
    State("main-msa", "data"),
    prevent_initial_call=True,
)
def run_ward_linking(n_clicks, n_clusters, msa_data, main_msa, encoding):
    if (not (n_clicks or 0) > 0) or (not msa_data or not main_msa) or (n_clusters is None or n_clusters < 1):
        return dash.no_update
    df = pd.DataFrame.from_dict(msa_data[main_msa])
    
    from frankenmsa.cluster.ward import ward_linking

    linked = ward_linking(df, n_clusters, encoding)
    if linked is None:
        return dash.no_update
    msa_data[main_msa] = linked
    return msa_data

@callback(
    Output("ward-clusters-to-save-dropdown", "options"),
    Input("msa-data", "data"),
    State("main-msa", "data"),
)
def update_ward_clusters_to_save_options(msa_data, main_msa):
    if not msa_data or not main_msa:
        return dash.no_update
    df = pd.DataFrame.from_dict(msa_data[main_msa])
    if "ward_id" not in df.columns:
        return dash.no_update
    clusters = df["ward_id"].unique()
    options = [{"label": f"Ward {c}", "value": int(c)} for c in clusters]
    options.insert(0, {"label": "All", "value": "all"})
    return options


def pca_plot(msa, graph_id="pca-plot", title="PCA of Clusters", color_col="cluster_id", encoding=None):
    import plotly.express as px
    from frankenmsa.visual.dimension_reduction import compute_PCA

    rest, query = compute_PCA(msa, encoding)
    if rest is None:
        return dcc.Graph(id=graph_id)

    fig = px.scatter(
        rest,
        x="PC 1",
        y="PC 2",
        color=color_col if color_col in rest.columns else None,
        hover_name="header" if "header" in rest.columns else None,
        title=title,
        template="plotly_white",
        color_continuous_scale="deep",
    )

    if len(query):
        fig_query = px.scatter(
            query,
            x="PC 1",
            y="PC 2",
            hover_name="header" if "header" in query.columns else None,
        )
        fig_query.update_traces(marker=dict(size=20, color="red"))
        fig.add_trace(fig_query.data[0])

    return dcc.Graph(id=graph_id, figure=fig)


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


def kmeans_layout():
    return html.Div(
        [
            html.H1("Cluster Sequences with KMeans"),
            html.P(
                "Cluster sequences based on their similarity using KMeans clustering. Clusters can be saved as new MSAs to be used in downstream tasks."
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            id="kmeans-controls-container",
                        ),
                    ),
                ]
            ),
            html.Div(
                id="kmeans-save-container",
            ),
        ],
        className="shaded-bordered",
    )


@callback(
    Output("kmeans-controls-container", "children"),
    Input("kmeans-controls-container", "children"),
)
def kmeans_controls(_):
    n_clusters = dcc.Input(
        id="kmeans-n-clusters",
        type="number",
        placeholder="Number of clusters",
        value=5,
        min=1,
        max=1000,
        step=1,
        persistence=True,
        persistence_type="memory",
    )
    n_clusters_tooltip = dbc.Tooltip(
        "Number of clusters to form.",
        target="kmeans-n-clusters",
        placement="bottom",
    )

    n_clusters_label = html.Label(
        "Number of Clusters",
    )

    run_button = html.Button(
        "Run KMeans",
        id="run-kmeans-button",
        className="button-component",
        style={"margin-top": "20px"},
        n_clicks=0,
    )

    other_columns_to_include = dcc.Dropdown(
        id="kmeans-other-columns",
        options=[],
        value=[],
        multi=True,
        className="dropdown-component",
        placeholder="Other columns...",
    )
    other_columns_to_include_tooltip = dbc.Tooltip(
        "Optionally, select other columns whose data to include during clustering. These columns have to be numeric. By default only the 'sequence' column is considered (this is the only non-numeric column allowed).",
        target="kmeans-other-columns",
        placement="top",
    )

    encoding_label = html.Label("Encoding")
    encoding_selector = dbc.RadioItems(
        id="kmeans-encoding",
        options=[
            {"label": "onehot", "value": "onehot"},
            {"label": "esm", "value": "esm"},
        ],
        value="onehot",
        inline=True,
        persistence=True,
        persistence_type="memory",
    )
    encoding_tooltip = dbc.Tooltip(
        "Encoding to use for sequence representation during clustering.",
        target="kmeans-encoding",
        placement="bottom",
    )

    top_row = dbc.Row(
        [
            dbc.Col(
                [
                    n_clusters_tooltip,
                    n_clusters_label,
                    n_clusters,
                ],
                width="auto",
            ),
            dbc.Col(
                [
                    encoding_tooltip,
                    encoding_label,
                    encoding_selector,
                ],
                width="auto",
            ),
            dbc.Col(
                [
                    other_columns_to_include_tooltip,
                    other_columns_to_include,
                ],
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
    bottom_row = dbc.Row(
        run_button,
        style={"width": "100%"},
    )
    return html.Div(
        [top_row, bottom_row],
    )


@callback(
    Output("kmeans-other-columns", "options"),
    Input("msa-data", "data"),
    State("main-msa", "data"),
)
def update_kmeans_other_columns_options(msa_data, main_msa):
    if not msa_data or not main_msa:
        return dash.no_update

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)

    columns = msa.select_dtypes(include=["number"]).columns.tolist()

    # Create options for the dropdown
    options = [{"label": col, "value": col} for col in columns]

    return options


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("run-kmeans-button", "n_clicks"),
    State("kmeans-n-clusters", "value"),
    State("kmeans-other-columns", "value"),
    State("kmeans-encoding", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def run_kmeans(
    n_clicks,
    n_clusters,
    columns_to_include,
    encoding,
    main_msa,
    msa_data,
):
    if not (n_clicks or 0) > 0:
        return dash.no_update

    if not msa_data or not main_msa:
        return dash.no_update

    from frankenmsa.cluster import KMeans

    clusterer = KMeans()

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)

    msa = clusterer.cluster(
        msa,
        n_clusters=n_clusters,
        columns=(columns_to_include or None),
        encoding=encoding,
    )

    msa_data[main_msa] = msa.to_dict("list")
    return msa_data


@callback(
    Output("kmeans-save-container", "children"),
    Output("msa-data", "data", allow_duplicate=True),
    Input("save-kmeans-clusters-button", "n_clicks"),
    State("msa-data", "data"),
    State("main-msa", "data"),
    prevent_initial_call=True,
)
def save_kmeans_clusters(
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
        return dbc.Alert("No clusters found. Please run KMeans first."), msa_data

    for cluster_id, subset in msa.groupby("cluster_id"):

        name = f"{main_msa}_kmeans_cluster_{cluster_id}"
        msa_data[name] = subset.to_dict("list")

    info = f"Saved {len(msa['cluster_id'].unique())} clusters to MSA data."
    return (
        dbc.Alert(
            info,
            color="success",
            is_open=True,
        ),
        msa_data,
    )


@callback(
    Output("clusters-to-save-dropdown", "options"),
    Input("msa-data", "data"),
    State("main-msa", "data"),
)
def update_clusters_to_save_options(msa_data, main_msa):
    if not msa_data or not main_msa:
        return dash.no_update

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)

    if "cluster_id" not in msa.columns:
        return dash.no_update

    clusters = msa["cluster_id"].unique()
    options = [{"label": f"Cluster {c}", "value": c} for c in clusters]
    options.insert(0, {"label": "All", "value": "all"})
    return options


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("save-selected-clusters-button", "n_clicks"),
    State("clusters-to-save-dropdown", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def save_selected_clusters(
    n_clicks,
    selected_clusters,
    main_msa,
    msa_data,
):
    if not (n_clicks or 0) > 0:
        return dash.no_update

    if not msa_data or not main_msa:
        return dash.no_update

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)

    if "cluster_id" not in msa.columns:
        return dash.no_update

    if "all" in selected_clusters:
        selected_clusters = msa["cluster_id"].unique()

    for cluster_id in selected_clusters:
        subset = msa[msa["cluster_id"] == cluster_id]
        name = f"{main_msa}_selected_cluster_{cluster_id}"
        msa_data[name] = subset.to_dict("list")

    info = f"Saved {len(selected_clusters)} clusters to MSA data."
    return msa_data


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("save-ward-selected-clusters-button", "n_clicks"),
    State("ward-clusters-to-save-dropdown", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def save_ward_selected_clusters(n_clicks, selected, main_msa, msa_data):
    if not (n_clicks or 0) > 0:
        return dash.no_update
    if not msa_data or not main_msa:
        return dash.no_update
    df = pd.DataFrame.from_dict(msa_data[main_msa])
    if "ward_id" not in df.columns:
        return dash.no_update
    if not selected:
        return dash.no_update
    if "all" in selected:
        selected = df["ward_id"].unique()
    for wid in selected:
        subset = df[df["ward_id"] == wid]
        name = f"{main_msa}_ward_cluster_{wid}"
        msa_data[name] = subset.to_dict("list")
    return msa_data


# sync ward-n-clusters-slider to hidden input for compatibility
@callback(
    Output("ward-n-clusters", "value"),
    Input("ward-n-clusters-slider", "value"),
    prevent_initial_call=True,
)
def _sync_ward_slider_to_input(val):
    return val


# sync ward-n-clusters input to slider
@callback(
    Output("ward-n-clusters-slider", "value"),
    Input("ward-n-clusters", "value"),
    State("ward-n-clusters-min-box", "value"),
    State("ward-n-clusters-max-box", "value"),
    prevent_initial_call=True,
)
def _sync_ward_input_to_slider(val, min_box, max_box):
    # Validate using the dynamic min/max from the boxes
    if val is None:
        return dash.no_update
    try:
        v = int(val)
    except Exception:
        return dash.no_update

    # fall back to sensible defaults if boxes are missing
    try:
        min_v = int(min_box) if min_box is not None else 2
    except Exception:
        min_v = 2
    try:
        max_v = int(max_box) if max_box is not None else 100
    except Exception:
        max_v = 100

    if v < min_v or v > max_v:
        return dash.no_update
    return v


@callback(
    Output("ward-n-clusters-slider", "min"),
    Output("ward-n-clusters-slider", "max"),
    Output("ward-n-clusters", "min"),
    Output("ward-n-clusters", "max"),
    Input("ward-n-clusters-min-box", "value"),
    Input("ward-n-clusters-max-box", "value"),
)
def update_ward_slider_min_max(min_box, max_box):
    # Ensure both boxes are present and form a valid range
    if min_box is None or max_box is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    try:
        min_v = int(min_box)
        max_v = int(max_box)
    except Exception:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    if min_v >= max_v:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    return min_v, max_v, min_v, max_v
