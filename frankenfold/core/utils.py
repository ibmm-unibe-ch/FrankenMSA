"""
General utility functions.
"""

import tempfile


def tmpfile(data: str, suffix: str = ".tmp", dir: str = ".") -> str:
    """
    Write data to a temporary file

    Parameters
    ----------
    data : str
        The data to write to the temporary file
    suffix : str, optional
        The file suffix, by default ".tmp"
    dir : str, optional
        The directory to write the temporary file to, by default "."

    Returns
    -------
    str
        The temporary file path
    """
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, dir=dir, suffix=suffix
    ) as f:
        f.write(data)
        return f.name
