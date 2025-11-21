import os, sys

from pathlib import Path

helpers_dir = Path(__file__).parent
sys.path.append(str(helpers_dir.resolve()))

import dash
from dash import Dash, html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

RENDER_MODE = os.environ.get("FRANKEN_RENDER_MODE", "external").strip().lower()
if RENDER_MODE not in {"external", "inline"}:
    RENDER_MODE = "external"

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.MINTY, dbc.icons.FONT_AWESOME],
)

# --- Download route (serve result files like ZIP/FASTA/A3M) ---
from flask import send_file


def _collect_download_roots():
    roots = []

    if (
        os.environ.get("ON_COLAB") == "1"
        or os.environ.get("IN_COLAB") == "1"
        or os.environ.get("FRANKEN_COLAB") == "1"
    ):
        roots.extend(["/content", "/content/ProteinMPNN/outputs_run"])

    project_root = Path(__file__).resolve().parent.parent
    local_repo = project_root / "ProteinMPNN"
    roots.append(str(local_repo / "outputs_run"))
    roots.append(str(local_repo / "outputs_local"))

    out_override = os.environ.get("PROTEINMPNN_OUT_DIR")
    if out_override:
        roots.append(out_override)

    deduped = []
    seen = set()
    for root in roots:
        if not root:
            continue
        normalized = str(Path(root).expanduser())
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


DOWNLOAD_ROOTS = _collect_download_roots()


@app.server.route("/colab/download/<path:fname>")
def serve_proteinmpnn_download(fname):
    """Serve ProteinMPNN output artifacts produced by Colab or local runs."""
    for root in DOWNLOAD_ROOTS:
        path = os.path.join(root, fname)
        if os.path.isfile(path):
            return send_file(path, as_attachment=True)
    return ("File not found", 404)


# --- end download route ---


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
        dcc.Location(id="url"),
        make_notification(),
        make_header(),
        dash.page_container,
        make_footer(),
        # empty stuff for the state
        dcc.Store(id="inject-a3m", data=None, storage_type="session"),
        dcc.Store(id="main-msa", data=None, storage_type="memory"),
        dcc.Store(id="msa-data", data={}, storage_type="memory"),
        dcc.Store(id="afcluster-last-settings", data={}, storage_type="memory"),
    ],
)


# Callback to consume injected A3M data
@callback(
    Output("msa-data", "data", allow_duplicate=True),
    Output("main-msa", "data", allow_duplicate=True),
    Output("inject-a3m", "data", allow_duplicate=True),
    Input("inject-a3m", "data"),
    State("msa-data", "data"),
    prevent_initial_call=True,
)
def _consume_injected_a3m(injected, msa_data):
    # Nothing to do
    if not injected or not injected.get("text"):
        return no_update, no_update, no_update

    import tempfile
    import os
    from pathlib import Path

    try:
        from frankenmsa.utils import read_a3m
    except Exception:
        # Fallback: defer processing if utils unavailable
        return no_update, no_update, no_update

    raw_name = injected.get("name") or "mpnn.a3m"
    name = (Path(raw_name).stem or "mpnn").strip()

    # Ensure dict
    msa_data = {} if msa_data is None else dict(msa_data)

    # Drop duplicate name variants that include extensions
    ext_variants = {
        raw_name,
        f"{name}.a3m",
        f"{name}.fa",
        f"{name}.fasta",
        f"{name}.csv",
    }
    for k in list(msa_data.keys()):
        if k in ext_variants and k != name:
            msa_data.pop(k, None)

    # If already present, select it and clear the one-shot store
    if name in msa_data:
        return msa_data, name, None

    # Materialize text to a temp file and parse via existing reader
    tmp_path = os.path.join(tempfile.gettempdir(), f"{name}.a3m")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(injected["text"])

    try:
        msa = read_a3m(tmp_path)
    except Exception:
        return no_update, no_update, no_update

    msa_data[name] = msa.to_dict("list")

    # Update global stores and clear the one-shot injection store
    return msa_data, name, None


def launch(**kwargs):
    """Main function to run the Dash app.
    Stable, production-like settings; no hot-reload; explicit host/port.
    """
    # Honor HOST/PORT env if provided
    host = kwargs.get("host", None)
    if host is None:
        host = os.getenv("HOST", "0.0.0.0")
    port = kwargs.get("port", None)
    if port is None:
        port = int(os.getenv("PORT", "8050"))

    # Ensure production-ish mode
    os.environ["DASH_DEBUG_MODE"] = "0"
    os.environ["FLASK_ENV"] = "production"

    # Decide render mode (inline/external) again
    render_mode = (
        kwargs.get("render_mode", os.environ.get("FRANKEN_RENDER_MODE", RENDER_MODE))
        .strip()
        .lower()
    )
    if render_mode not in {"inline", "external"}:
        render_mode = "external"

    tunnel = os.environ.get("COLAB_TUNNEL_URL")

    # Inline custom embedding (no JupyterDash): start background thread and display iframe
    if render_mode == "inline":
        print(f"JupyterDash (inline) starting on http://{host}:{port}")
        if tunnel:
            print(f"🌐 Public tunnel (unused in inline mode): {tunnel}")
        return app.run(mode="inline", host=host, port=port, debug=False)

    # Fallback: plain Dash
    print(f"Dash starting on http://{host}:{port}")
    if tunnel:
        print(f"🌐 Public tunnel: {tunnel}")
    return app.run(host=host, port=port, debug=False)


main = launch  # alias
if __name__ == "__main__":
    launch()
