"""
ProteinMPNN sequence generator backend.


"""

from pathlib import Path
import frankenfold.core.sequence_generators.backend as backend

GIT_URL = "https://github.com/dauparas/ProteinMPNN.git"
"""
The git URL to download the ProteinMPNN sequence generator backend from.
To download a custom fork, set this to the git URL of the fork.
"""

CHECKPOINT_PATH = "vanilla_model_weights/v_48_020.pt"
"""
The path within the ProteinMPNN repository to the model checkpoint.
"""

LOCAL_PATH = "ProteinMPNN"
"""
The local path to the ProteinMPNN sequence generator backend.
"""

SETUP_PARAMETERS = dict(
    hidden_dim=128,
    num_encoder_layers=3,
    num_decoder_layers=3,
    num_letters=21,
    node_features=128,
    edge_features=128,
    augment_eps=0.0,
)
"""
Parameters to pass to the ProteinMPNN setup function.
"""


def download(overwrite: bool = False):
    """
    Download the ProteinMPNN sequence generator backend.

    Note
    ----
    To download a custom fork, set the `GIT_URL` constant to the git URL of the fork.
    To change the download location, set the `LOCAL_PATH` constant to the desired directory.

    Parameters
    ----------
    dir : str
        The directory to download the ProteinMPNN sequence generator backend to
    overwrite : bool, optional
        Whether to overwrite the directory if it already exists, by default False
    """
    import shutil
    from git import Repo

    if not GIT_URL.endswith(".git"):
        raise ValueError(f"Invalid git URL: {GIT_URL}")

    dest = Path(LOCAL_PATH)
    if dest.exists() and dest.is_dir():
        if overwrite:
            shutil.rmtree(LOCAL_PATH)
        else:
            raise FileExistsError(
                f"Directory {LOCAL_PATH} already exists. Set `overwrite=True` to overwrite."
            )
    try:
        Repo.clone_from(GIT_URL, LOCAL_PATH)
    except Exception as e:
        if dest.exists() and dest.is_dir():
            shutil.rmtree(LOCAL_PATH)
        raise e


def load() -> "torch.Model":
    """
    Load the ProteinMPNN model.

    Returns
    -------
    torch.Model
        The ProteinMPNN model
    """
    import torch
    from protein_mpnn_utils import (
        tied_featurize,
        parse_PDB,
        ProteinMPNN,
        StructureDataset,
        StructureDatasetPDB,
        _scores,
        _S_to_seq,
    )

    CHECKPOINT_PATH = Path(LOCAL_PATH) / CHECKPOINT_PATH
    checkpoint = torch.load(str(CHECKPOINT_PATH), weights_only=False)
    model = ProteinMPNN(k_neighbors=checkpoint["num_edges"], **SETUP_PARAMETERS)
    model.load_state_dict(checkpoint["model_state_dict"])
    return model
