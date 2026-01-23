import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    path="/",
)

import os

ON_COLAB = os.environ.get("ON_COLAB", False) == "1"

try:
    import torch

    HAS_TORCH = True
    HAS_GPU = torch.cuda.is_available()
except Exception:
    HAS_GPU = False
    HAS_TORCH = False


def _runtime_badge_config():
    base = "colab" if ON_COLAB else "local"
    gpu_state = "gpu" if HAS_GPU else "no_gpu"
    icon_src = f"assets/icon_{base}_{gpu_state}.png"
    runtime_label = "on Google Colab" if ON_COLAB else "in a Local Environment"
    gpu_label = "with GPU available" if HAS_GPU else "but no GPU was detected"
    if not HAS_TORCH:
        gpu_label = "but GPU status is unknown as PyTorch is not installed"
    tooltip = f"The app is running {runtime_label} {gpu_label}."
    return icon_src, tooltip


def layout():

    main_text = """

Protein Folding Models like AlphaFold and RoseTTAFold have revolutionized the field of protein structure prediction.
They rely on Multiple Sequence Alignments (MSAs) to generate accurate predictions of protein structures from sequences.
Research has shown that the MSA input greatly influences the results of these predictions; in fact, so much so, that through 
deliberate manipulation of the MSA, the folding models can be steered to produce structures with specific features.

This is why we have created frankenMSA, a Python package and web application that allows you to manipulate MSAs in a variety of ways.
frankenMSA allows users to generate new MSAs using sequence alignment or inverse folding, as well as editing existing MSAs by cropping,
clustering, or filtering them. Of course, as is often the case with GUI applications, the underlying software library is much more powerful than the GUI itself.
So if you have some basic Python knowledge, you can also use the frankenMSA library directly in your own scripts to perform more complex operations.
The frankenMSA library is available on PyPI and can be freely installed.
"""

    icon_src, tooltip_text = _runtime_badge_config()
    runtime_indicator = html.Div(
        [
            html.Img(
                id="runtime-indicator-home",
                src=icon_src,
                style={
                    "width": "54px",
                    "height": "54px",
                    "cursor": "pointer",
                    "maxWidth": "100%",
                    "maxHeight": "100%",
                    "objectFit": "contain",
                    "display": "block",
                },
                title=tooltip_text,
                alt="Runtime indicator",
            ),
            dbc.Tooltip(
                tooltip_text,
                target="runtime-indicator-home",
                placement="left",
            ),
        ],
        style={
            "position": "absolute",
            "top": "24px",
            "right": "30px",
            "zIndex": 10,
        },
    )

    # Add a class to the Div to apply the animated background
    return html.Div(
        className="gradient-background",
        style={"position": "relative"},
        children=[
            runtime_indicator,
            html.Img(
                src="assets/frankenmsa_colored_v1.png",
                className="logo-main",
            ),
            html.P(main_text, style={"margin-top": "4%"}),
            html.H5(
                "To get started, check out the icons at the top of the page to navigate to the different parts of the application.",
                style={"margin-top": "3%"},
            ),
        ],
    )
