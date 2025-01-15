"""
Backends for generating protein sequences
"""

from pathlib import Path
import sys

__backend_data__ = {
    "name": None,
    "git_url": None,
    "local_path": None,
    "checkpoint": None,
    "setup_parameters": None,
    "model": None,
    "module": None,
}

AVAILABLE_BACKENDS = ["ProteinMPNN"]

__backend_module_names__ = {"ProteinMPNN": "protein_mpnn"}

# Check that all backends are configured
# properly
for backend_name in AVAILABLE_BACKENDS:
    if not backend_name in __backend_module_names__:
        raise ModuleNotFoundError(
            f"Backend name {backend_name} not configured in __backend_module_names__"
        )


def get_backend() -> str:
    """
    Get the current backend name
    """
    return __backend_data__["name"]


def backend_is_set() -> bool:
    """
    Check if a backend is set
    """
    return __backend_data__["name"] is not None


def set_backend(name: str):
    """
    Set the current backend for generating protein sequences

    Parameters
    ----------
    name : str
        The name of the backend. This can be any of the following:
        - "ProteinMPNN"
    """
    if name not in __backend_module_names__:
        raise ValueError(
            f"Invalid backend name: {name}. Available backends: {list(__backend_module_names__.keys())}"
        )
    backend_module = __import__(
        f"frankenfold.core.sequence_generators",
        globals(),
        locals(),
        [__backend_module_names__[name]],
    )
    backend_module = getattr(backend_module, __backend_module_names__[name])
    __backend_data__["module"] = backend_module

    _check_backend_module_is_valid()

    __backend_data__["name"] = name
    __backend_data__["git_url"] = backend_module.GIT_URL
    __backend_data__["checkpoint"] = backend_module.CHECKPOINT_PATH
    __backend_data__["setup_parameters"] = backend_module.SETUP_PARAMETERS
    __backend_data__["local_path"] = backend_module.LOCAL_PATH
    __backend_data__["model"] = None

    _setup_backend()


def backend_dir_exists():
    """
    Check if the backend directory exists

    Returns
    -------
    bool
        Whether the backend directory exists
    """
    if __backend_data__["name"] is None:
        raise ValueError("No backend set")

    path = get_backend_dir()
    return Path(path).exists()


def get_backend_dir() -> str:
    """
    Get the local backend directory

    Returns
    -------
    str
        The backend directory
    """
    if __backend_data__["name"] is None:
        raise ValueError("No backend set")

    if __backend_data__["local_path"] is not None:
        return __backend_data__["local_path"]

    git_directory_name = Path(__backend_data__["GIT_URL"]).name.replace(".git", "")
    __backend_data__["local_path"] = git_directory_name
    return git_directory_name


def _setup_backend():
    """
    Setup the backend
    """
    if __backend_data__["name"] is None:
        raise ValueError("No backend set")

    backend = __backend_data__["module"]
    if not backend_dir_exists():
        backend.download()

    _add_backend_to_path()

    __backend_data__["model"] = backend.load()


def _check_backend_module_is_valid():
    """
    Check if the backend module is valid
    """
    if __backend_data__["module"] is None:
        raise ValueError("No backend module set")

    for i in ["GIT_URL", "CHECKPOINT_PATH", "SETUP_PARAMETERS", "LOCAL_PATH"]:
        if not hasattr(__backend_data__["module"], i):
            raise AttributeError(f"Backend module missing constant attribute: {i}")

    for i in ["download", "load", "generate"]:
        if not hasattr(__backend_data__["module"], i):
            raise AttributeError(f"Backend module missing function: {i}")


def _add_backend_to_path():
    """
    Add the backend to the system path
    """
    if __backend_data__["name"] is None:
        raise ValueError("No backend set")

    if __backend_data__["local_path"] is not None:
        sys.path.append(str(Path(__backend_data__["local_path"]).absolute()))
    else:
        git_directory_name = get_backend_dir()
        sys.path.append(
            str(
                Path(
                    f"{__backend_data__['local_path']}/{git_directory_name}"
                ).absolute()
            )
        )
