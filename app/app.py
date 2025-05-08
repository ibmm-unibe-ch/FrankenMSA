import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash import callback, Input, Output, State


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
    upload_icon = icon_link(
        "icon_upload_white_transparent", "/upload", "Upload an existing MSA File"
    )
    download_icon = icon_link(
        "icon_download_white_transparent", "/download", "Download the generated MSA"
    )
    edit_icon = icon_link(
        "icon_edit_white_transparent",
        "/edit",
        "Perform basic operations to edit the MSA",
    )
    align_icon = icon_link(
        "icon_align_white_transparent",
        "/align",
        "Perform sequence alignment to generate an MSA",
    )
    inverse_fold_icon = icon_link(
        "icon_inverse_fold_white_transparent",
        "/inverse_fold",
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
    header = html.Div(
        [
            home_icon,
            upload_icon,
            download_icon,
            edit_icon,
            align_icon,
            inverse_fold_icon,
            cluster_icon,
            visualize_icon,
            unibe_icon,
        ],
        className="header",
    )

    return header


app.layout = html.Div(
    [
        make_header(),
        dash.page_container,
        # empty stuff for the state
        dcc.Store(id="main-msa", data=None, storage_type="session"),
    ],
)


if __name__ == "__main__":
    app.run(debug=True)
