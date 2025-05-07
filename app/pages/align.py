import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
)


def layout():
    return html.Div(
        [
            html.H1("Align sequences to make an MSA"),
            html.P(
                "This is the home page of the application. You can navigate to different pages using the links below."
            ),
        ]
    )
