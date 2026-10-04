"""Shared building blocks so every page follows the same structure."""

from dash import html


def page_header(title, lead=None):
    """Page title with an optional one-line description below it."""
    children = [html.H1(title, className="page-title")]
    if lead:
        children.append(html.P(lead, className="page-lead"))
    return html.Div(children, className="page-header")


def page(title, lead, *children, narrow=False, **kwargs):
    """Standard page container: header followed by the page content."""
    class_name = "page-container page-narrow" if narrow else "page-container"
    return html.Div(
        [page_header(title, lead), *children], className=class_name, **kwargs
    )
