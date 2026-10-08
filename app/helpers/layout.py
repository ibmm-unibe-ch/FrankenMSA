"""Shared building blocks so every page follows the same structure."""

import math

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


def slider_marks(low, high, target=6):
    """Evenly spaced, round-numbered marks spanning a slider's range.

    Marks written by hand drift out of range whenever the slider's bounds are
    set from the data, which leaves a slider labelled with numbers it cannot
    reach. Deriving them from the current bounds keeps the two in step.

    The step is rounded to a 1/2/2.5/5 multiple of a power of ten so the labels
    land on readable values, and both ends are always labelled.
    """
    low, high = float(low), float(high)
    if not math.isfinite(low) or not math.isfinite(high) or high <= low:
        return {_mark_key(low): _mark_label(low)}

    raw_step = (high - low) / max(1, target - 1)
    magnitude = 10 ** math.floor(math.log10(raw_step))
    for multiple in (1, 2, 2.5, 5, 10):
        step = multiple * magnitude
        if step >= raw_step:
            break

    # Whole-numbered bounds mean a whole-numbered slider (cluster counts,
    # sequence indices), where a label of 2.4 is not a position you can pick.
    if low == int(low) and high == int(high):
        step = max(1, round(step))

    marks = {}
    value = math.ceil(low / step) * step
    while value <= high + step * 1e-6:
        marks[_mark_key(value)] = _mark_label(value)
        value += step

    # The ends matter most, so label them even when the step misses them.
    marks[_mark_key(low)] = _mark_label(low)
    marks[_mark_key(high)] = _mark_label(high)
    return marks


def _mark_key(value):
    """Dash wants int keys for whole numbers, floats otherwise."""
    value = round(float(value), 6)
    return int(value) if value == int(value) else value


def _mark_label(value):
    return f"{_mark_key(value):g}"
