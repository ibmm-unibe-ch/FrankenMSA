import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    path="/",
)


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

    # Add a class to the Div to apply the animated background
    return html.Div(
        className="gradient-background",
        children=[
            html.Img(
                src="assets/logo_white_transparent_large.png",
                className="logo-main",
            ),
            html.P(main_text, style={"margin-top": "4%"}),
            html.H5(
                "To get started, check out the icons at the top of the page to navigate to the different parts of the application.",
                style={"margin-top": "3%"},
            ),
        ],
    )
