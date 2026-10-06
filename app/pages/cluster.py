import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
import pandas as pd

from frankenmsa.cluster import cluster_dropdown_options
from frankenmsa.cluster import cluster_pca_projection
from frankenmsa.cluster import numeric_column_options
from frankenmsa.cluster import run_ward_centroid_merge
from frankenmsa.cluster import save_cluster_subsets
from frankenmsa.runtime import log_message
from helpers.layout import page


dash.register_page(
    __name__,
)


def layout():
    return page(
        "Cluster",
        "Group the sequences of the selected MSA and save individual clusters as new MSAs.",
        dbc.Row(
            [
                dbc.Col(
                    [afcluster_layout(), kmeans_layout()],
                    lg=6,
                ),
                dbc.Col(
                    [
                        dcc.Loading(
                            html.Div(
                                id="cluster-visual-container",
                                className="shaded-bordered",
                            ),
                            color="#009e6f",
                        ),
                        dcc.Loading(
                            html.Div(id="afcluster-status"),
                            type="dot",
                            color="#009e6f",
                        ),
                        dcc.Loading(
                            html.Div(id="kmeans-status"),
                            type="dot",
                            color="#009e6f",
                        ),
                        html.Div(
                            [
                                html.H1("Save Clusters"),
                                html.P(
                                    "Select clusters and save each one as a new MSA."
                                ),
                    html.Div(
                        [
                            dcc.Dropdown(
                                id="clusters-to-save-dropdown",
                                options=[],
                                value=[],
                                multi=True,
                                className="dropdown-component",
                                placeholder="Select clusters to save",
                                style={"flex": 1, "minWidth": "200px"},
                            ),
                            html.Button(
                                "Save AFCluster",
                                id="save-afcluster-button",
                                className="button-component",
                                n_clicks=0,
                                style={"width": "260px"},
                            ),
                        ],
                        className="control-row",
                        style={"margin": "4px 0"},
                    ),
                    html.Div(
                        [
                            dcc.Dropdown(
                                id="ward-centroid-clusters-to-save-dropdown",
                                options=[],
                                value=[],
                                multi=True,
                                className="dropdown-component",
                                placeholder="Select centroid-merged clusters to save",
                                style={"flex": 1, "minWidth": "200px"},
                            ),
                            html.Button(
                                "Save Ward Centroid Merge",
                                id="save-ward-centroid-selected-clusters-button",
                                className="button-component",
                                n_clicks=0,
                                style={"width": "260px"},
                            ),
                        ],
                        className="control-row",
                        style={"margin": "4px 0"},
                    ),
                    html.Div(
                        [
                            dcc.Dropdown(
                                id="kmeans-clusters-to-save-dropdown",
                                options=[],
                                value=[],
                                multi=True,
                                className="dropdown-component",
                                placeholder="Select kmeans clusters to save",
                                style={"flex": 1, "minWidth": "200px"},
                            ),
                            html.Button(
                                "Save KMeans",
                                id="save-kmeans-clusters-button",
                                className="button-component",
                                n_clicks=0,
                                style={"width": "260px"},
                            ),
                        ],
                        className="control-row",
                        style={"margin": "4px 0"},
                    ),
                            ],
                            id="save-clusters-container",
                            className="shaded-bordered",
                        ),
                    ],
                    lg=6,
                ),
            ]
        ),
    )


def afcluster_layout():
    return html.Div(
        [
            html.H1("AFCluster"),
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
    header = html.H4("Ward Centroid Merge")

    explain = dcc.Markdown(
        "After `AF-Cluster` assigns `cluster_id`, merge those existing clusters hierarchically using "
        "size-weighted Ward merging on cluster centroids. This is a centroid merge over AFCluster groups, "
        "not a fresh Ward clustering pass over every sequence. For an application to AF-based conformational ensembles, see "
        "[Piomponi et al., 2025](https://pubs.acs.org/doi/10.1021/acs.jcim.5c01090)."
    )

    n_clusters_tooltip = dbc.Tooltip(
        "How many groups to merge the existing AFCluster clusters into. Cannot exceed the number of clusters AFCluster found.",
        target="ward-centroid-n-clusters",
        placement="bottom",
    )
    top_controls = html.Div(
        [
            n_clusters_tooltip,
            html.Label("Final number of clusters"),
            dcc.Input(
                id="ward-centroid-n-clusters",
                type="number",
                placeholder="Number of clusters",
                value=3,
                min=2,
                max=1000,
                step=1,
                persistence=True,
                persistence_type="memory",
            ),
        ],
        className="control-row",
    )

    # big button below, full width (similar to Run AFCluster)
    bottom_button = html.Button(
        "Run Ward Centroid Merge",
        id="run-ward-centroid-merge-button",
        className="button-component button-primary button-block",
        n_clicks=0,
    )

    return html.Div([html.Hr(), header, explain, top_controls, bottom_button])


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
        value=10,
        min=0.01,
        max=1000.0,
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
    run_button = html.Button(
        "Run AFCluster",
        id="run-afcluster-button",
        className="button-component button-primary button-block",
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
                width=12,
            ),
        ],
        style={
            "margin": "16px 0",
            "align-items": "flex-end",
            "justify-content": "center",
            "display": "flex",
            "flex-direction": "row",
            "flex-wrap": "wrap",
        },
    )
    bottomrow = run_button
    return html.Div(
        [toprow, bottomrow],
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("afcluster-status", "children"),
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
        return dash.no_update, dash.no_update

    if not msa_data or not main_msa:
        return dash.no_update, dash.no_update

    try:
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
        return (
            msa_data,
            dbc.Alert(
                f"AFCluster completed: {len(msa)} sequences updated in {main_msa}.",
                color="success",
            ),
        )
    except Exception as e:
        import traceback

        log_message(f"Error running AFCluster: {e}")
        log_message(traceback.format_exc())
        return dash.no_update, dbc.Alert(f"AFCluster Error: {str(e)}", color="danger")


@callback(
    Output("cluster-visual-container", "children"),
    Input("msa-data", "data"),
    Input("main-msa", "data"),
)
def visualise_clusters(msa_data, main_msa, encoding=None):
    if not msa_data or not main_msa:
        return html.P(
            "Upload or select an MSA to see its clusters here.",
            className="text-muted",
            style={"margin": 0},
        )
    df = pd.DataFrame.from_dict(msa_data[main_msa])
    if "cluster_id" not in df.columns:
        return dbc.Alert("No clusters found. Please run clustering first.")

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
                title="PCA of Ward Centroid-Merged Clusters",
                color_col="ward_id",
                encoding=encoding,
            )
        )

    return html.Div(graphs)


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("run-ward-centroid-merge-button", "n_clicks"),
    State("ward-centroid-n-clusters", "value"),
    State("msa-data", "data"),
    State("main-msa", "data"),
    prevent_initial_call=True,
)
def run_ward_centroid_merge_callback(
    n_clicks, n_clusters, msa_data, main_msa, encoding=None
):
    if (
        (not (n_clicks or 0) > 0)
        or (not msa_data or not main_msa)
        or (n_clusters is None or n_clusters < 1)
    ):
        return dash.no_update
    df = pd.DataFrame.from_dict(msa_data[main_msa])

    linked = run_ward_centroid_merge(df, n_clusters, encoding)
    if linked is None:
        return dash.no_update
    msa_data[main_msa] = linked.to_dict("list")
    return msa_data


@callback(
    Output("ward-centroid-clusters-to-save-dropdown", "options"),
    Input("msa-data", "data"),
    State("main-msa", "data"),
)
def update_ward_centroid_clusters_to_save_options(msa_data, main_msa):
    if not msa_data or not main_msa:
        return dash.no_update
    df = pd.DataFrame.from_dict(msa_data[main_msa])
    options = cluster_dropdown_options(
        df, cluster_column="ward_id", label_prefix="Ward"
    )
    return options or dash.no_update


@callback(
    Output("kmeans-clusters-to-save-dropdown", "options"),
    Input("msa-data", "data"),
    State("main-msa", "data"),
)
def update_kmeans_clusters_to_save_options(msa_data, main_msa):
    if not msa_data or not main_msa:
        return dash.no_update
    df = pd.DataFrame.from_dict(msa_data[main_msa])
    options = cluster_dropdown_options(
        df, cluster_column="cluster_id", label_prefix="Cluster"
    )
    return options or dash.no_update


def pca_plot(
    msa,
    graph_id="pca-plot",
    title="PCA of Clusters",
    color_col="cluster_id",
    encoding=None,
):
    import plotly.express as px

    try:
        rest, query = cluster_pca_projection(msa, encoding)
    except Exception as e:
        return dbc.Alert(f"PCA failed: {e}", color="warning")

    if rest is None or len(rest) < 2:
        return dbc.Alert(
            "Not enough sequences to compute PCA (need at least 2 non-query rows).",
            color="warning",
        )

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


# DEAD CODE: no component with id "save-clusters-button" exists in any layout,
# so this callback never fires. Saving is handled by the save-*-button
# callbacks further below.
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
            "No clusters found. Please run clustering first."
        )

    msa_data = save_cluster_subsets(
        msa_data,
        main_msa,
        cluster_column="cluster_id",
        selected=["all"],
        name_template="{main}_cluster_{cluster}",
    )

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

    return numeric_column_options(msa)


def kmeans_layout():
    return html.Div(
        [
            html.H1("KMeans"),
            dcc.Markdown(
                "Cluster sequences using [KMeans](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html) of [one hot encoding](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html) or using [ESM3 C](https://github.com/evolutionaryscale/esm?tab=readme-ov-file#esm-c-)-embeddings, similar to [VC-MSA](https://pubmed.ncbi.nlm.nih.gov/37414576/)"
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
        className="button-component button-primary button-block",
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
                width=12,
            ),
        ],
        style={
            "margin": "16px 0",
            "align-items": "flex-end",
            "justify-content": "center",
            "display": "flex",
            "flex-direction": "row",
            "flex-wrap": "wrap",
        },
    )
    bottom_row = run_button
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

    return numeric_column_options(msa)


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("kmeans-status", "children"),
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
        return dash.no_update, dash.no_update

    if not msa_data or not main_msa:
        return dash.no_update, dash.no_update

    try:
        from frankenmsa.cluster import KMeans

        clusterer = KMeans()

        msa = msa_data[main_msa]
        msa = pd.DataFrame.from_dict(msa)
        log_message(
            f"Running KMeans with n_clusters={n_clusters}, columns_to_include={columns_to_include}, encoding={encoding} on MSA {main_msa} with {len(msa)} sequences."
        )
        msa = clusterer.cluster(
            msa,
            n_clusters=n_clusters,
            columns=(columns_to_include or None),
            encoding=encoding,
        )
        log_message(
            f"KMeans clustering completed. Cluster assignments added to MSA {main_msa}."
        )
        msa_data[main_msa] = msa.to_dict("list")
        return (
            msa_data,
            dbc.Alert(
                f"KMeans completed: {len(msa)} sequences updated in {main_msa}.",
                color="success",
            ),
        )
    except Exception as e:
        import traceback

        log_message(f"Error running KMeans: {e}")
        log_message(traceback.format_exc())
        return dash.no_update, dbc.Alert(f"KMeans Error: {str(e)}", color="danger")


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("save-kmeans-clusters-button", "n_clicks"),
    State("kmeans-clusters-to-save-dropdown", "value"),
    State("msa-data", "data"),
    State("main-msa", "data"),
    prevent_initial_call=True,
)
def save_kmeans_clusters(
    n_clicks,
    selected,
    msa_data,
    main_msa,
):
    if not (n_clicks or 0) > 0:
        return dash.no_update

    if not msa_data or not main_msa:
        return dash.no_update

    msa = msa_data[main_msa]
    msa = pd.DataFrame.from_dict(msa)

    if "cluster_id" not in msa.columns:
        return dash.no_update

    if not selected:
        return dash.no_update

    return save_cluster_subsets(
        msa_data,
        main_msa,
        cluster_column="cluster_id",
        selected=selected,
        name_template="{main}_kmeans_cluster_{cluster}",
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

    options = cluster_dropdown_options(
        msa, cluster_column="cluster_id", label_prefix="Cluster"
    )
    return options or dash.no_update


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("save-afcluster-button", "n_clicks"),
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

    return save_cluster_subsets(
        msa_data,
        main_msa,
        cluster_column="cluster_id",
        selected=selected_clusters,
        name_template="{main}_selected_cluster_{cluster}",
    )


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Input("save-ward-centroid-selected-clusters-button", "n_clicks"),
    State("ward-centroid-clusters-to-save-dropdown", "value"),
    State("main-msa", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def save_ward_centroid_selected_clusters(n_clicks, selected, main_msa, msa_data):
    if not (n_clicks or 0) > 0:
        return dash.no_update
    if not msa_data or not main_msa:
        return dash.no_update
    df = pd.DataFrame.from_dict(msa_data[main_msa])
    if "ward_id" not in df.columns:
        return dash.no_update
    if not selected:
        return dash.no_update
    return save_cluster_subsets(
        msa_data,
        main_msa,
        cluster_column="ward_id",
        selected=selected,
        name_template="{main}_ward_cluster_{cluster}",
    )


# The upper bound follows the data: you cannot merge AFCluster's clusters into
# more groups than it produced.
@callback(
    Output("ward-centroid-n-clusters", "max"),
    Output("ward-centroid-n-clusters", "value"),
    Input("msa-data", "data"),
    Input("main-msa", "data"),
    State("ward-centroid-n-clusters", "value"),
)
def update_ward_centroid_bounds(msa_data, main_msa, current_value):
    upper = 1000
    if msa_data and main_msa in (msa_data or {}):
        df = pd.DataFrame.from_dict(msa_data[main_msa])
        if "cluster_id" in df.columns:
            labels = [c for c in df["cluster_id"].dropna().unique() if c != -1]
            upper = max(2, len(labels))

    value = min(current_value or 3, upper)
    return upper, max(2, value)