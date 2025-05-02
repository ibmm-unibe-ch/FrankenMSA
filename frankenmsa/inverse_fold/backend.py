"""
Backends for generating protein sequences
"""

from pathlib import Path
import pandas as pd
import sys
from typing import List, Dict, Tuple


class BackendNotSetError(Exception):
    pass


class BadBackendError(Exception):
    pass


class BaseSequenceGenerator:
    """
    The base class for sequence generator backends
    This class is used to define the interface for sequence generators.

    (you will probably want to use the DownloadableSequenceGenerator class instead of this one)
    """

    def generate(self, *args, **kwargs) -> Tuple[pd.DataFrame, Dict]:
        """
        Generate sequences

        Returns
        -------
        pd.DataFrame
            A DataFrame with the generated sequences which contains the columns "header" and "sequence"
        dict
            A dictionary of additional information
        """
        raise NotImplementedError()

    __call__ = generate

    def __repr__(self):
        """
        Return a string representation of the class
        """
        attrs = ", ".join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"


class DownloadableSequenceGenerator(BaseSequenceGenerator):
    """
    The base class for sequence generator backends that should either be cloned from a git repository or otherwise downloaded
    from a remote location and includes all the necessary scripts and other files to function properly.

    Attributes
    ----------
    remote_url : str
        The URL of the backend repository to download
    checkpoint_path : str
        The path to the model checkpoint within the repository
    setup_parameters : dict
        The parameters to pass to the setup function when initializing the model
    local_path : str
        The local path to the backend repository (i.e. download location) for importing the model and other functions
    model : Any
        The model object
    src : Any
        The backend module or packagem which contains the model and other functions
    """

    def __init__(self):
        self.remote_url = None
        self.checkpoint_path = None
        self.setup_parameters = None
        self.local_path = None
        self.model = None
        self.src = None
        self._is_loaded = False
        self.needs_init = True

        self.pip_requirements = []
        self.conda_requirements = []
        self.conda_channels = []

    @property
    def device(self):
        """
        Get the device of the model
        """
        if self.model is not None:
            return next(self.model.parameters()).device
        else:
            raise BackendNotSetError("Backend not loaded")

    def init(self):
        """
        Initialize the backend. This will download the backend (if necessary) and load the model
        """
        nsteps = 4
        if not self.needs_init:
            return
        if self._is_loaded:
            print("Backend already loaded")
            return
        print(f"[1/{nsteps}] Initializing backend")
        self._vet_backend()
        print(f"[1/{nsteps}] Backend validated")
        print(f"[2/{nsteps}] Downloading backend")
        self.download()
        print(f"[2/{nsteps}] Download complete")
        print(f"[3/{nsteps}] Installing dependencies")
        self.install_dependencies()
        print(f"[3/{nsteps}] Dependencies installed")
        print(f"[4/{nsteps}] Loading backend")
        self.load()
        print(f"[4/{nsteps}] Backend loaded")

    def download(self, force: bool = False):
        """
        Download the backend

        Parameters
        ----------
        force : bool
            Whether to force download in case the backend already exists
        """
        if self.remote_url is None:
            raise AttributeError("Remote URL not set")
        elif self.local_path is None:
            raise AttributeError("Local path not set")
        elif Path(self.local_path).exists() and not force:
            return
        elif self.remote_url.endswith(".git"):
            self.clone_from_git(overwrite=force)
        else:
            self.download_from_url(overwrite=force)

    def load(self):
        """
        Load the backend. This will add the backend to the system path, import the module, and setup the model
        """
        if self.local_path is None:
            raise AttributeError("Local path not set")
        elif not Path(self.local_path).exists():
            raise FileNotFoundError(f"Backend not downloaded: {self.local_path}")
        self.add_to_path()
        self.import_module()
        model = self.setup_model()
        if model is None:
            raise BadBackendError(
                "Model not loaded properly. Make sure that the setup_model function returns the model object"
            )
        self.model = model
        self._is_loaded = True

    def add_to_path(self):
        """
        Add the backend to the system path
        """
        if self.local_path is not None:
            path = Path(self.local_path).absolute()
            if not path.exists():
                raise FileNotFoundError(f"Backend not downloaded: {self.local_path}")
            sys.path.append(str(path))
        else:
            raise AttributeError("Local path not set")

    def setup_model(self):
        """
        Setup the model.

        Returns
        -------
        torch.Model or some other model object
        """
        raise NotImplementedError()

    def install_dependencies(self):
        """
        Install any dependencies for the backend
        """
        if len(self.pip_requirements) > 0:
            import subprocess
            from importlib.metadata import version

            for req in self.pip_requirements:
                try:
                    version(req)
                except:
                    subprocess.run(["pip", "install", req], check=True)
        if len(self.conda_requirements) > 0:
            import subprocess
            from importlib.metadata import version

            if len(self.conda_channels) > 0:
                channels = " ".join([f"-c {i}" for i in self.conda_channels])
            else:
                channels = ""
            for req in self.conda_requirements:
                try:
                    version(req)
                except:
                    subprocess.run(
                        f"conda install {channels} {req} -y", shell=True, check=True
                    )

    def import_module(self):
        """
        Import the backend module. This should be called after the backend is downloaded and added to the system path
        The module will be stored in the `src` attribute. Depending on the respective backend, this attribute will be useful or not.
        """
        if self.local_path is not None:
            sys.path.append(str(Path(self.local_path).absolute()))
        else:
            raise AttributeError("Local path not set")

        module = __import__(self.name, globals(), locals(), [], 0)
        self.src = module
        return module

    def clone_from_git(self, overwrite: bool = False):
        """
        Clone the backend from a git repository
        """
        import shutil
        from git import Repo

        if not self.remote_url.endswith(".git"):
            raise ValueError(f"Invalid git URL: {self.remote_url}")

        dest = Path(self.local_path)
        if dest.exists() and dest.is_dir():
            if overwrite:
                shutil.rmtree(self.local_path)
            else:
                raise FileExistsError(
                    f"Directory {self.local_path} already exists. Set `overwrite=True` to overwrite."
                )
        try:
            Repo.clone_from(self.remote_url, self.local_path)
        except Exception as e:
            if dest.exists() and dest.is_dir():
                shutil.rmtree(self.local_path)
            raise e

    def download_from_url(self, overwrite: bool = False):
        """
        Download the backend from a URL (not a git repository).
        If there are any issues with the download, the backend will not be saved.
        For more control, implement a custom download function in a subclass.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite the backend if it already exists
        """
        import requests

        if Path(self.local_path).exists() and not overwrite:
            raise FileExistsError(
                f"File {self.local_path} already exists. Set `overwrite=True` to overwrite."
            )
        elif Path(self.local_path).exists() and overwrite:
            import os

            os.remove(self.local_path)

        response = requests.get(self.remote_url)
        with open(self.local_path, "wb") as f:
            f.write(response.content)

        if not Path(self.local_path).exists():
            raise FileNotFoundError(f"Download failed: {self.local_path}")

        suffix = Path(self.local_path).suffix[1:]
        extractor = getattr(self, f"_after_download_from_url_extract_{suffix}", None)
        if extractor is not None:
            extractor()
        else:
            supported = [
                i.__name__[
                    33:
                ]  # 33 is the length of "_after_download_from_url_extract_"
                for i in dir(self)
                if i.startswith("_after_download_from_url_extract_")
            ]
            raise NotImplementedError(
                f"Downloaded file type not supported: {self.local_path} (suffix: {suffix}). Either use a different source format (supported are {supported}) or implement a custom extraction function '_after_download_from_url_extract_{suffix}'"
            )

    @property
    def name(self):
        """
        Get the local directory name
        """
        return Path(self.local_path).name

    def _vet_backend(self):
        """
        Check if the backend is valid
        """
        for i in ["remote_url", "checkpoint_path", "setup_parameters", "local_path"]:
            if getattr(self, i) is None:
                raise AttributeError(f"Backend attribute is not set: {i}")

    def _after_download_from_url_extract_zip(self):
        """
        Download a zip file and extract it
        """
        import zipfile, os

        with zipfile.ZipFile(self.local_path, "r") as zip_ref:
            zip_ref.extractall(Path(self.local_path).parent)
        os.remove(self.local_path)

    def _after_download_from_url_extract_tar(self, mode: str):
        """
        Download a tar file and extract it
        """
        import tarfile, os

        with tarfile.open(self.local_path, f"r:{mode}") as tar:
            tar.extractall(Path(self.local_path).parent)
        os.remove(self.local_path)

    def _after_download_from_url_extract_gz(self):
        """
        Download a gz file and extract it
        """
        import gzip, shutil, os

        with gzip.open(self.local_path, "rb") as f_in:
            with open(self.local_path.replace(".gz", ""), "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(self.local_path)
