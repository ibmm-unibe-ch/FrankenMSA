import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
from pandas import DataFrame
from dash.dependencies import MATCH

dash.register_page(
    __name__,
)


def layout():
    return html.Div(
        [
            dbc.Tooltip(
                "Add a new operation for combining MSAs.",
                target="add-combine-msa-block-button",
            ),
            dbc.Tooltip(
                "Combine the selected MSAs into a single MSA.",
                target="combine-msas-button",
            ),
            dbc.Tooltip(
                "Remove the last added operation for combining MSAs.",
                target="remove-combine-msa-block-button",
            ),
            html.H1("Combine multiple MSAs"),
            html.P(
                "MSAs can be combined by either concatenating them vertically or horizontally."
            ),
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Button(
                                        "Add",
                                        id="add-combine-msa-block-button",
                                        className="button-component",
                                    ),
                                    html.Button(
                                        "Remove",
                                        id="remove-combine-msa-block-button",
                                        className="button-component",
                                    ),
                                ]
                            ),
                            dbc.Col(
                                dbc.Input(
                                    id="combine-msa-name",
                                    placeholder="Name of the combined MSA",
                                    type="text",
                                ),
                            ),
                            dbc.Col(
                                [
                                    html.Button(
                                        "Combine",
                                        id="combine-msas-button",
                                        className="button-component",
                                    ),
                                ]
                            ),
                        ],
                        style={"margin": "10px", "align-items": "center"},
                    ),
                    dbc.Row(
                        [],
                        id="combine-msa-blocks-container",
                        style={
                            "margin": "10px",
                            "align-items": "center",
                            "width": "95%",
                        },
                    ),
                ],
                id="combine-msa-main",
                className="shaded-bordered",
            ),
        ],
        className="gradient-background",
    )


def nothing_to_combine():
    return dbc.Alert(
        "No MSAs have been added to combine. Please add MSAs to combine.",
        color="warning",
        className="shaded-bordered",
        is_open=True,
    )


def combine_msa_block(msa_data, index):

    target = dcc.Dropdown(
        id={"type": "combine-msa-dropdown", "index": index},
        options=[{"label": name, "value": name} for name in msa_data.keys()],
        placeholder="Select a source MSA",
        className="dropdown-component",
    )

    add_direction = dcc.RadioItems(
        id={"type": "combine-msa-direction", "index": index},
        options=[
            {"label": "Add Horizontally (merge right)", "value": "horizontal"},
            {"label": "Add Vertically (concat)", "value": "vertical"},
        ],
        value="horizontal",
        labelStyle={"display": "block"},
        className="radio-component",
    )

    horizontal_index_tooltip = html.P(
        "Optionally select a specific range of sequence indices to add a slice of the MSA horizontally.",
        # target={"type": "combine-msa-horizontal-index", "index": index},
    )
    horizontal_index_slider = dcc.RangeSlider(
        id={"type": "combine-msa-horizontal-index", "index": index},
        min=0,
        max=100,
        step=1,
        value=(0, 100),
        marks={i: str(i) for i in range(0, 101, 10)},
    )
    horizontal_index_start = dcc.Input(
        id={"type": "combine-msa-horizontal-index-start", "index": index},
        type="number",
        value=0,
        min=0,
        max=100,
        step=1,
        style={"width": "50px"},
    )
    horizontal_index_end = dcc.Input(
        id={"type": "combine-msa-horizontal-index-end", "index": index},
        type="number",
        value=100,
        min=0,
        max=100,
        step=1,
        style={"width": "50px"},
    )
    vertical_index_tooltip = html.P(
        "Optionally select a specific range of row indices to add a slice of the MSA vertically.",
        # target={"type": "combine-msa-vertical-index", "index": index},
    )
    vertical_index_slider = dcc.RangeSlider(
        id={"type": "combine-msa-vertical-index", "index": index},
        min=0,
        max=100,
        step=1,
        value=(0, 100),
        marks={i: str(i) for i in range(0, 101, 10)},
    )

    vertical_index_start = dcc.Input(
        id={"type": "combine-msa-vertical-index-start", "index": index},
        type="number",
        value=0,
        min=0,
        step=1,
        style={"width": "50px"},
    )
    vertical_index_end = dcc.Input(
        id={"type": "combine-msa-vertical-index-end", "index": index},
        type="number",
        value=100,
        min=0,
        step=1,
        style={"width": "50px"},
    )

    block = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Row(target),
                            dbc.Row(
                                [
                                    horizontal_index_tooltip,
                                    dbc.Col(horizontal_index_start, width="auto"),
                                    dbc.Col(horizontal_index_slider),
                                    dbc.Col(horizontal_index_end, width="auto"),
                                ],
                            ),
                            dbc.Row(
                                [
                                    vertical_index_tooltip,
                                    dbc.Col(vertical_index_start, width="auto"),
                                    dbc.Col(vertical_index_slider),
                                    dbc.Col(vertical_index_end, width="auto"),
                                ],
                                align="stretch",
                            ),
                        ],
                        style={
                            "margin-bottom": "20px",
                            "line-height": "1.5",
                        },
                    ),
                    dbc.Col(
                        [add_direction], width="auto", style={"align-items": "left"}
                    ),
                ],
                style={"margin": "10px"},
            ),
        ],
        className="shaded-bordered",
        style={"margin": "10px", "align-items": "center", "width": "95%"},
    )
    return block


@callback(
    Output("combine-msa-blocks-container", "children", allow_duplicate=True),
    Input("add-combine-msa-block-button", "n_clicks"),
    State("combine-msa-blocks-container", "children"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def add_combine_msa_block(n_clicks, children, msa_data):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    new_block = combine_msa_block(msa_data, len(children))
    if not children:
        children = [new_block]
        return children
    children = [i for i in children if i["type"] != "Alert"]
    children = children + [new_block]
    return children


@callback(
    Output("combine-msa-blocks-container", "children", allow_duplicate=True),
    Input("remove-combine-msa-block-button", "n_clicks"),
    State("combine-msa-blocks-container", "children"),
    prevent_initial_call=True,
)
def remove_combine_msa_block(n_clicks, children):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    if len(children) >= 1:
        children = children[:-1]
    return children


@callback(
    Output({"type": "combine-msa-vertical-index", "index": MATCH}, "value"),
    Output({"type": "combine-msa-vertical-index", "index": MATCH}, "max"),
    Output({"type": "combine-msa-vertical-index", "index": MATCH}, "marks"),
    Output({"type": "combine-msa-vertical-index-start", "index": MATCH}, "value"),
    Output({"type": "combine-msa-vertical-index-end", "index": MATCH}, "value"),
    Input({"type": "combine-msa-dropdown", "index": MATCH}, "value"),
    State(
        "msa-data",
        "data",
    ),
    prevent_initial_call=True,
)
def update_vertical_sliders(selected_msa, msa_data):
    msa = msa_data[selected_msa]
    msa = DataFrame.from_dict(msa)

    _max = len(msa)
    marks = {i: str(i) for i in range(0, int(_max + 1), max(1, int(_max // 10)))}
    return (0, _max), _max, marks, 0, _max


@callback(
    Output({"type": "combine-msa-horizontal-index", "index": MATCH}, "value"),
    Output({"type": "combine-msa-horizontal-index", "index": MATCH}, "max"),
    Output({"type": "combine-msa-horizontal-index", "index": MATCH}, "marks"),
    Output({"type": "combine-msa-horizontal-index-start", "index": MATCH}, "value"),
    Output({"type": "combine-msa-horizontal-index-end", "index": MATCH}, "value"),
    Input({"type": "combine-msa-dropdown", "index": MATCH}, "value"),
    State(
        "msa-data",
        "data",
    ),
    prevent_initial_call=True,
)
def update_horizontal_sliders(selected_msa, msa_data):
    msa = msa_data[selected_msa]
    msa = DataFrame.from_dict(msa)

    sequence_length = msa["sequence"].str.len().max()
    _max = sequence_length
    marks = {i: str(i) for i in range(0, int(_max + 1), max(1, int(_max // 10)))}
    return (0, _max), _max, marks, 0, _max


@callback(
    Output(
        {"type": "combine-msa-horizontal-index", "index": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Input({"type": "combine-msa-horizontal-index-start", "index": MATCH}, "value"),
    Input({"type": "combine-msa-horizontal-index-end", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def update_horizontal_index_range(min_value, max_value):
    return (min_value, max_value)


@callback(
    Output(
        {"type": "combine-msa-vertical-index", "index": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Input({"type": "combine-msa-vertical-index-start", "index": MATCH}, "value"),
    Input({"type": "combine-msa-vertical-index-end", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def update_vertical_index_range(min_value, max_value):
    return (min_value, max_value)


@callback(
    Output(
        {"type": "combine-msa-vertical-index-start", "index": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Output(
        {"type": "combine-msa-vertical-index-end", "index": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Input({"type": "combine-msa-vertical-index", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def update_vertical_index_range(range_value):
    return range_value


@callback(
    Output(
        {"type": "combine-msa-horizontal-index-start", "index": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Output(
        {"type": "combine-msa-horizontal-index-end", "index": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Input({"type": "combine-msa-horizontal-index", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def update_horizontal_index_range(range_value):
    return range_value


@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("main-msa", "data", allow_duplicate=True),
    Output("combine-msa-blocks-container", "children", allow_duplicate=True),
    Input("combine-msas-button", "n_clicks"),
    State("combine-msa-blocks-container", "children"),
    State("combine-msa-name", "value"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def combine_msas(n_clicks, children, name, msa_data):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    if not name:
        count_combined = sum(1 for i in msa_data.keys() if i.startswith("combined"))
        name = f"combined_{count_combined + 1}"

    _children = [i for i in children if i["type"] != "Alert"]

    if not len(_children):
        return (dash.no_update, dash.no_update, children + [nothing_to_combine()])

    import pandas as pd
    from frankenmsa.utils import slice_sequences, adjust_depth, unify_length

    combined_msa = None
    for block in _children:
        components = extract_block_components(block)

        selected_msa = components["dropdown"]["props"]["children"]["props"]["value"]
        msa = msa_data[selected_msa]
        msa = DataFrame.from_dict(msa)

        add_horizontal = components["add_direction"]["props"]["value"] == "horizontal"

        horizontal_index = components["horizontal_index"]["props"]["children"][1][
            "props"
        ]
        min_value, max_value = horizontal_index["value"]
        _min, _max = horizontal_index["min"], horizontal_index["max"]
        if not (_min == min_value and _max == max_value):
            msa = slice_sequences(msa, min_value, max_value)

        vertical_index = components["vertical_index"]["props"]["children"][1]["props"]
        min_index, max_index = vertical_index["value"]
        _min, _max = vertical_index["min"], vertical_index["max"]
        if not (_min == min_index and _max == max_index):
            msa = msa.iloc[min_index:max_index]

        if combined_msa is None:
            combined_msa = msa
        else:
            if add_horizontal:
                if len(msa) != len(combined_msa):
                    msa = adjust_depth(msa, len(combined_msa))
                    # print(msa.head())
                    # print(combined_msa.head())
                    break
                    combined_sequences = combined_msa["sequence"].str.cat(
                        msa["sequence"], sep=""
                    )
                    # print(combined_sequences)
                combined_msa["sequence"] = combined_msa["sequence"].str.cat(
                    msa["sequence"], sep=""
                )
                # print(combined_msa)
            else:
                msa = unify_length(msa, int(combined_msa["sequence"].str.len()[0]))
                combined_msa = pd.concat([combined_msa, msa], axis=0)
                combined_msa = combined_msa.reset_index(drop=True)

    msa_data[name] = combined_msa.to_dict("list")
    return msa_data, name, dash.no_update


def extract_block_components(block):
    raw_components = block["props"]["children"][0]["props"]["children"]
    components = []
    for component in raw_components:
        if isinstance(component, list):
            components.extend(component)
        elif component["type"] in ("Row", "Col"):
            components.extend(component["props"]["children"])
        else:
            components.append(component)

    dropdown = None
    add_direction = None
    add_vertical = None
    horizontal_index = None
    vertical_index = None
    for c in components:
        if has_path_ending_in(
            c, ["props", "children", "props", "id", "type"], "combine-msa-dropdown"
        ):
            dropdown = c
        if has_path_ending_in(c, ["props", "id", "type"], "combine-msa-direction"):
            add_direction = c
        if has_path_ending_in(
            c,
            ["props", "children", 1, "props", "id", "type"],
            "combine-msa-horizontal-index",
        ):
            horizontal_index = c
        if has_path_ending_in(
            c,
            ["props", "children", 3, "props", "id", "type"],
            "combine-msa-vertical-index",
        ):
            vertical_index = c

    out = {
        "dropdown": dropdown,
        "add_direction": add_direction,
        "horizontal_index": horizontal_index,
        "vertical_index": vertical_index,
    }
    return out


def has_path_ending_in(obj, path, ending):
    try:
        for i in path:
            obj = obj[i]
        return obj == ending
    except:
        return False
