def get_chain_ids(pdbfile) -> list:
    """
    Get chain IDs from a PDB file.

    Parameters
    ----------
    pdbfile : str
        Path to the PDB file.

    Returns
    -------
    list
        List of chain IDs.
    """
    with open(pdbfile, "r") as f:
        lines = f.readlines()
    chain_ids = set()
    for line in lines:
        if line.startswith("ATOM") or line.startswith("HETATM"):
            chain_ids.add(line[21])
    return list(chain_ids)
