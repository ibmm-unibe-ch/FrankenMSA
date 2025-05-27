import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State
import os


app = Dash(
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.MINTY, dbc.icons.FONT_AWESOME],
    prevent_initial_callbacks=True,
)
app.config["prevent_initial_callbacks"] = True


def icon_link(icon, href, tooltip_text):
    return html.Div(
        [
            dcc.Link(
                html.Div(
                    html.Img(
                        src=f"assets/{icon}.png",
                        className="header-icon",
                    ),
                ),
                href=href,
            ),
            dbc.Tooltip(
                tooltip_text,
                target=f"{icon}-tooltip",
                placement="bottom",
            ),
        ],
        id=f"{icon}-tooltip",
    )


def make_header():
    home_icon = icon_link("icon_main_white_transparent", "/", "Go to the home page")
    files_icon = icon_link(
        "icon_files_white_transparent", "/file", "Upload and download MSA files"
    )
    edit_icon = icon_link(
        "icon_edit_white_transparent",
        "/edit",
        "Perform basic operations to edit the MSA",
    )
    combine_icon = icon_link(
        "icon_combine_white_transparent",
        "/combine",
        "Combine multiple MSAs into a single MSA",
    )
    align_icon = icon_link(
        "icon_align_white_transparent",
        "/align",
        "Perform sequence alignment to generate an MSA",
    )
    inverse_fold_icon = icon_link(
        "icon_inverse_fold_white_transparent",
        "/inversefold",
        "Perform inverse folding to generate sequences from a given protein structure",
    )
    cluster_icon = icon_link(
        "icon_cluster_white_transparent", "/cluster", "Cluster the MSA"
    )
    visualize_icon = icon_link(
        "icon_visual_white_transparent", "/visualize", "Visualize the MSA"
    )

    unibe_icon = icon_link(
        "unibe_white_transparent",
        "https://www.unibe.ch",
        "Developed by the friendly folks at the Institute of Biochemistry and Molecular Medicine of the University of Bern, Switzerland",
    )

    select_main_msa_tooltip = dbc.Tooltip(
        "Select the MSA to work with",
        target="select-main-msa",
    )
    select_main_msa = dbc.Select(
        id="select-main-msa",
        persistence=True,
        persistence_type="memory",
        style={"width": "20%"},
    )

    header = html.Div(
        [
            home_icon,
            files_icon,
            edit_icon,
            combine_icon,
            align_icon,
            inverse_fold_icon,
            cluster_icon,
            visualize_icon,
            select_main_msa,
            unibe_icon,
            select_main_msa_tooltip,
        ],
        className="header",
    )

    return header


@callback(
    Output("select-main-msa", "options"),
    Output("select-main-msa", "value"),
    Input("msa-data", "data"),
    Input("main-msa", "data"),
)
def update_select_main_msa_options(msa_data, main_msa_data):
    if msa_data is None:
        return [], dash.no_update

    # Create options for the dropdown
    options = [{"label": col, "value": col} for col in list(msa_data.keys())]
    return options, main_msa_data


@callback(
    Output("main-msa", "data", allow_duplicate=True),
    Input("select-main-msa", "value"),
    prevent_initial_call=True,
)
def select_new_main_msa(new_main_msa):
    if new_main_msa is not None:
        return new_main_msa
    else:
        return dash.no_update


def make_footer():
    footer = html.Div(
        [
            html.A(
                "About",
                href="https://www.ibmm.unibe.ch/research/group_lemmin/index_eng.html",
                className="footer-link",
                style={"margin-right": "20px"},
            ),
            html.A(
                "GitHub Repository",
                href="https://github.com/ibmm-unibe-ch/FrankenMSA",
                className="footer-link",
                style={"margin-right": "20px"},
            ),
            html.A(
                "Found an issue?",
                href="https://github.com/ibmm-unibe-ch/FrankenMSA/issues/new",
                className="footer-link",
                style={"margin-right": "20px"},
            ),
            html.A(
                "Contact Us",
                href="mailto:jannik.gut@unibe.ch",
                className="footer-link",
                style={"margin-right": "20px"},
            ),
        ],
        className="footer",
        style={"display": "flex", "align-items": "center", "height": "50px"},
    )
    return footer


def make_notification():
    return dbc.Toast(
        "This is a notification",
        id="notification",
        header="Notification",
        is_open=False,
        dismissable=True,
        icon="info",
        duration=3000,
        style={"position": "fixed", "top": 50, "right": 20, "width": "300px"},
    )


app.layout = html.Div(
    [
        make_notification(),
        make_header(),
        dash.page_container,
        make_footer(),
        # empty stuff for the state
        dcc.Store(id="main-msa", data=None, storage_type="memory"),
        dcc.Store(id="msa-data", data={}, storage_type="memory"),
        dcc.Store(id="afcluster-last-settings", data={}, storage_type="memory"),
    ],
)


def launch(**kwargs):
    """Main function to run the Dash app.
    Add any keyword arguments to the app.run() method.
    """
    app.run(**kwargs)


main = launch  # alias
if __name__ == "__main__":
    # Increase memory quota if running on a platform that supports it
    os.environ["DASH_MAX_MEMORY"] = "1024"  # Set memory quota to 1024MB (1GB)

    app.run(debug=True)
