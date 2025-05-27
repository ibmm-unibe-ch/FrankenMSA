import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from dash_bio import AlignmentChart
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd


dash.register_page(
    __name__,
)


def no_msa_yet():
    return dbc.Alert(
        "No MSA data is available to visualize. Please upload or generate MSA data to proceed.",
        color="warning",
        className="shaded-bordered",
        is_open=True,
    )


def layout():

    visualise_aignment_checkbox = dbc.Checkbox(
        id="visualise-alignment",
        label="Visualise Alignment",
        value=True,
        persistence=True,
        persistence_type="memory",
    )
    visualise_gaps_checkbox = dbc.Checkbox(
        id="visualise-gaps",
        label="Visualise Gaps",
        value=False,
        persistence=True,
        persistence_type="memory",
    )
    visualise_conservation_checkbox = dbc.Checkbox(
        id="visualise-conservation",
        label="Visualise Conservation",
        value=False,
        persistence=True,
        persistence_type="memory",
    )
    visualise_identity_checkbox = dbc.Checkbox(
        id="visualise-identity",
        label="Visualise Identity",
        value=False,
        persistence=True,
        persistence_type="memory",
    )

    visualise_controls = dbc.Row(
        [
            dbc.Col(visualise_aignment_checkbox),
            dbc.Col(visualise_gaps_checkbox),
            dbc.Col(visualise_conservation_checkbox),
            dbc.Col(visualise_identity_checkbox),
        ],
        className="shaded-bordered",
        style={"width": "100%"},
    )
    return html.Div(
        [
            # html.H1("Visualise the MSA", style={"padding-bottom": "20px"}),
            visualise_controls,
            dcc.Loading(
                id="loading",
                color="white",
                type="circle",
                children=[
                    html.Div(
                        [
                            dbc.Row(id="visual-gaps-container"),
                            dbc.Row(id="visual-conservation-container"),
                            dbc.Row(id="visual-identity-container"),
                            dbc.Row(id="visual-alignment-container"),
                        ],
                        id="plotly-visualisation",
                        className="shaded-bordered",
                        style={
                            "height": "100%",
                            "width": "100%",
                            "overflow": "hidden",
                            # "background-color": "transparent",
                            # "display": "flex",
                            # "flex-direction": "column",
                            # "justify-content": "center",
                            # "align-items": "stretch",
                        },
                    ),
                ],
            ),
        ],
        className="gradient-background",
        style={"width": "100%"},
    )


@callback(
    Output("visual-gaps-container", "children"),
    Input("visualise-gaps", "value"),
    Input("main-msa", "data"),
    State("msa-data", "data"),
)
def update_visual_gaps(visualise_gaps, main, data):

    if visualise_gaps == True:
        if not data:
            return no_msa_yet()
        msa = data[main]
        msa = pd.DataFrame.from_dict(msa)
        gaps = show_gaps(msa)
        return gaps
    else:
        return html.Div()


@callback(
    Output("visual-conservation-container", "children"),
    Input("visualise-conservation", "value"),
    Input("main-msa", "data"),
    State("msa-data", "data"),
)
def update_visual_conservation(visualise_conservation, main, data):
    if visualise_conservation == True:
        if not data:
            return no_msa_yet()
        msa = data[main]
        msa = pd.DataFrame.from_dict(msa)
        conservation = show_conservation(msa)
        return conservation
    else:
        return html.Div()


@callback(
    Output("visual-identity-container", "children"),
    Input("visualise-identity", "value"),
    Input("main-msa", "data"),
    State("msa-data", "data"),
)
def update_visual_identity(visualise_identity, main, data):
    if visualise_identity == True:
        if not data:
            return no_msa_yet()
        msa = data[main]
        msa = pd.DataFrame.from_dict(msa)
        identity = show_query_identity(msa)
        return identity
    else:
        return html.Div()


@callback(
    Output("visual-alignment-container", "children"),
    Input("visualise-alignment", "value"),
    Input("main-msa", "data"),
    State("msa-data", "data"),
)
def update_visual_alignment(visualise_alignment, main, data):
    if visualise_alignment == True:
        if not data:
            return no_msa_yet()
        msa = data[main]
        msa = pd.DataFrame.from_dict(msa)
        alignment = show_alignment(msa)
        return alignment
    else:
        return html.Div()


# @callback(
#     Output("plotly-visualisation", "children"),
#     Input("main-msa", "data"),
#     Input("msa-data", "data"),
# )
# def update_plotly_visualisation(main, data):
#     if not data:
#         return no_msa_yet()

#     import pandas as pd

#     msa = data[main]
#     msa = pd.DataFrame.from_dict(msa)

#     alignment = show_alignment(msa)
#     gaps = show_gaps(msa)
#     conservation = show_conservation(msa)
#     identity = show_query_identity(msa)

#     plotly_component = html.Div([gaps, conservation, identity, alignment])
#     if len(msa) > 150:
#         plotly_component = html.Div(
#             [
#                 plotly_component,
#                 html.P(
#                     "Note: The MSA is too large to visualize fully, it was subsampled evenly to 150 entries.",
#                     style={"color": "red"},
#                 ),
#             ],
#         )
#     return plotly_component


def show_alignment(msa):
    from frankenmsa.utils import unify_length, encode_a3m

    df = msa.copy()
    if len(df) > 150:
        print(
            f"Warning: The MSA has more than {150} sequences which will cause the plot to crash! Downsampling uniformly to 150 sequences."
        )
        df = df.iloc[:: len(df) // 150]

    a3m_string = encode_a3m(unify_length(df, "first"))
    chart = AlignmentChart(
        id="alignment-chart",
        data=a3m_string,
        showlabel=True,
        showid=True,
        showconservation=False,
        showconsensus=False,
        showgap=False,
        width="100%",
    )
    return chart


def show_gaps(msa):
    from frankenmsa.utils import unify_length

    _df = unify_length(msa, "max")

    count_gaps = np.zeros(len(_df["sequence"].values[0]))
    for seq in _df["sequence"]:
        count_gaps += np.array([1 if aa == "-" else 0 for aa in seq])
    # count_gaps /= count_gaps.sum()
    count_gaps = pd.Series(count_gaps, name="gap_count")
    gaps_figure = px.line(
        count_gaps,
        x=count_gaps.index,
        y=count_gaps.values,
        title="Gaps per Position",
        labels={"x": "Position", "y": "Gap Count"},
        color_discrete_sequence=["#00BC74"],
        template="plotly_white",
    )
    return dash.dcc.Graph(
        id="gap-count-figure",
        figure=gaps_figure,
        config={"displayModeBar": False},
        style={"width": "100%"},
    )


def show_conservation(msa):
    from frankenmsa.utils import unify_length

    _df = unify_length(msa, "max")

    count_conservation = np.zeros(len(_df["sequence"].values[0]))
    for i in range(len(_df["sequence"].values[0])):
        aas_at_i = _df["sequence"].str.get(i)
        aas_at_i_counts = aas_at_i.value_counts()
        most_common_aa = aas_at_i_counts.idxmax()
        conservation = aas_at_i_counts[most_common_aa] / len(aas_at_i)
        count_conservation[i] = conservation

    count_conservation = pd.Series(count_conservation, name="conservation")
    conservation_figure = px.line(
        count_conservation,
        x=count_conservation.index,
        y=count_conservation.values,
        title="Conservation per Position",
        labels={"x": "Position", "y": "Conservation"},
        color_discrete_sequence=["#00BC74"],
        template="plotly_white",
    )
    return dash.dcc.Graph(
        id="conservation-figure",
        figure=conservation_figure,
        config={"displayModeBar": False},
        style={"width": "100%"},
    )


def show_query_identity(msa):
    from frankenmsa.utils import unify_length

    _df = unify_length(msa, "max")

    count_identity = np.zeros(len(_df["sequence"].values[0]))
    query, _df = _df.iloc[0], _df.iloc[1:]
    query = query["sequence"]
    for i in range(len(_df["sequence"].values[0])):
        aas_at_i = _df["sequence"].str.get(i)
        aas_at_i_counts = aas_at_i.value_counts()
        aa_in_query_at_i = query[i]
        if not aa_in_query_at_i in aas_at_i_counts:
            count_identity[i] = 0
        else:
            count_identity[i] = aas_at_i_counts[aa_in_query_at_i] / len(aas_at_i)

    count_identity = pd.Series(count_identity, name="identity")
    identity_figure = px.line(
        count_identity,
        x=count_identity.index,
        y=count_identity.values,
        title="Identity to Query per Position",
        labels={"x": "Position", "y": "Identity"},
        color_discrete_sequence=["#00BC74"],
        template="plotly_white",
    )
    return dash.dcc.Graph(
        id="identity-figure",
        figure=identity_figure,
        config={"displayModeBar": False},
        style={"width": "100%"},
    )
