"""
Local ProteinMPNN sequence generator backend.
"""

from pathlib import Path
from collections import namedtuple
from copy import deepcopy
import os
import sys
import pandas as pd

from . import backend
from .protein_mpnn_support import resolve_proteinmpnn_root
from .protein_mpnn_support import resolve_proteinmpnn_weights
from ..utils.pdbtools import get_chain_ids

MAX_LENGTH = 20000
"""
The maximal length for a generated sequence.
"""

N_ALPHABET = 21
"""
The number of letters in the amino acid alphabet.
"""


def has_local_protein_mpnn(directory=None):
    """
    Check if the local ProteinMPNN repository is available.

    Parameters
    ----------
    directory : str, optional
        The path to the local directory containing the ProteinMPNN repository, by default None

    Returns
    -------
    bool
        True if the local ProteinMPNN repository is available, False otherwise
    """
    try:
        resolve_proteinmpnn_root(directory)
        return True
    except Exception:
        return False


class LocalProteinMPNN(backend.BaseSequenceGenerator):
    """
    Use ProteinMPNN to generate sequences from structures.

    Using an existing ProteinMPNN installation
    ------------------------------------------

        If you already have a local copy of the ProteinMPNN repository, set
        ``ProteinMPNN_DIR=/path/to/ProteinMPNN`` in the environment to make it
        automatically detectable.

        Alternatively, set ``protein_mpnn_instance.local_path`` after
        initialization or create the backend with :meth:`from_directory`.
    """

    module = "protein_mpnn_utils"
    remote_url = "https://github.com/dauparas/ProteinMPNN.git"
    checkpoint_path = "vanilla_model_weights/v_48_020.pt"
    needs_init = True

    def __init__(self):
        self._is_loaded = False
        self.model = None

        self.setup_parameters = dict(
            hidden_dim=128,
            num_encoder_layers=3,
            num_decoder_layers=3,
            num_letters=N_ALPHABET,
            node_features=128,
            edge_features=128,
            augment_eps=0.0,
        )

        self.local_path = None

        self.pssm = {}
        self.pssm_settings()

    @property
    def device(self):
        global torch

        import torch

        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")

    def init(self):
        if self._is_loaded:
            return self
        self.local_path = resolve_proteinmpnn_root(self.local_path)
        self.load()
        self._is_loaded = True
        return self

    def load(self):
        local_path = str(Path(self.local_path).resolve())
        if local_path not in sys.path:
            sys.path.insert(0, local_path)
        self.model = self.setup_model().to(self.device)
        return self.model

    @classmethod
    def from_directory(cls, directory: str):
        """
        Create a ProteinMPNN sequence generator backend from a local directory that was already downloaded.

        Parameters
        ----------
        directory : str
            The path to the local directory containing the ProteinMPNN model

        Returns
        -------
        ProteinMPNN
            The ProteinMPNN sequence generator backend
        """
        generator = cls()
        generator.local_path = Path(directory).expanduser()
        return generator

    def pssm_settings(
        self, pssm_threshold=0, pssm_multi=0, pssm_log_odds_flag=0, pssm_bias_flag=0
    ):
        """
        Set the PSSM settings for the model.

        Parameters
        ----------
        pssm_threshold : float, optional
            The PSSM threshold, by default 0
        pssm_multi : int, optional
            The PSSM multiplier, by default 0
        pssm_log_odds_flag : int, optional
            The PSSM log-odds flag, by default 0
        pssm_bias_flag : int, optional
            The PSSM bias flag, by default 0
        """
        self.pssm["pssm_threshold"] = pssm_threshold
        self.pssm["pssm_multi"] = pssm_multi
        self.pssm["pssm_log_odds_flag"] = bool(pssm_log_odds_flag)
        self.pssm["pssm_bias_flag"] = bool(pssm_bias_flag)

    def setup_model(self) -> "torch.Model":
        """
        Create the ProteinMPNN model.

        Returns
        -------
        torch.Model
            The ProteinMPNN model
        """
        global torch
        global np
        global protein_mpnn_utils
        import torch
        import numpy as np
        import protein_mpnn_utils

        checkpoint_path = (
            resolve_proteinmpnn_weights(Path(self.local_path)) / "v_48_020.pt"
        )
        checkpoint = torch.load(str(checkpoint_path), weights_only=False)
        model = protein_mpnn_utils.ProteinMPNN(
            k_neighbors=checkpoint["num_edges"],
            **self.setup_parameters,
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        return model

    def generate(
        self,
        pdbfile: str,
        n: int = 128,
        chains: list = None,  # Legacy argument, kept for compatibility
        design_chains: list = None,  # New argument
        fixed_chains: list = None,  # New argument
        temperature: float = 1.0,
        copies: int = 1,
        homomer: bool = False,  # Controlled by UI
    ):
        """
        Generate protein sequences from a PDB file.
        Updated to support Heteromer design (Fixed/Design chains).
        """
        device = self.device

        # Compatibility handling
        target_design = []
        target_fixed = []

        if design_chains or fixed_chains:
            if design_chains:
                target_design = (
                    design_chains
                    if isinstance(design_chains, list)
                    else str(design_chains).split(",")
                )
            if fixed_chains:
                target_fixed = (
                    fixed_chains
                    if isinstance(fixed_chains, list)
                    else str(fixed_chains).split(",")
                )

            target_design = [c.strip() for c in target_design if c.strip()]
            target_fixed = [c.strip() for c in target_fixed if c.strip()]
        else:
            if chains:
                target_design = chains
            else:
                target_design = None

        inputs = _prepare_model_input(
            pdbfile=pdbfile,
            n=n,
            design_chains=target_design,
            fixed_chains=target_fixed,
            homomer=homomer,
            copies=copies,
        )

        self._out = TempOutputs()
        self._out.extra = {
            "protein_name": [],
            "batch": [],
            "copy": [],
            "sequence_recovery_rate": [],
            "score": [],
        }

        if copies > 1:
            clone_factory = lambda protein: [deepcopy(protein) for _ in range(copies)]
        else:
            clone_factory = lambda protein: [protein]

        _sampler, _sampler_arguments = self._prepare_sampler(inputs)

        for idx, protein in enumerate(inputs.dataset):
            self._out.protein_name = protein["name"]
            clones = clone_factory(protein)
            features = _featurize(clones, inputs, device)
            self._out.pssm_log_odds_mask = (
                features.pssm_log_odds_all > self.pssm["pssm_threshold"]
            ).float()
            self._out.loss_mask = (
                features.mask * features.chain_mask * features.chain_mask_pos
            )
            sampler_kwargs = _sampler_arguments(features, inputs)

            for batch in range(inputs.n_batches):

                random_prompt = torch.randn(features.chain_mask.shape, device=device)
                kwargs = dict(
                    randn=random_prompt,
                    temperature=temperature,
                    **sampler_kwargs,
                )
                sample_dict = _sampler(**kwargs)
                scores = self._generate_scores(
                    sample_dict["S"],
                    features,
                    random_prompt,
                    use_decoding_order=True,
                    decoding_order=sample_dict["decoding_order"],
                )

                for cdx in range(copies):
                    seq, sequence_recovery_rate = self._generate_sequence(
                        features,
                        sample_dict,
                        cdx,
                    )

                    self._out.extra["protein_name"].append(self._out.protein_name)
                    self._out.extra["batch"].append(batch)
                    self._out.extra["copy"].append(cdx)
                    self._out.extra["sequence_recovery_rate"].append(
                        sequence_recovery_rate.item()
                    )
                    self._out.extra["score"].append(scores[cdx].item())
                    self._out.sequences.append(seq)

        final = {
            "header": [f"seq{i}" for i in range(len(self._out.sequences))],
            "sequence": self._out.sequences,
            "recovery_rate": self._out.extra["sequence_recovery_rate"],
            "score": self._out.extra["score"],
        }
        final = pd.DataFrame(final)
        return final, {}

    def _generate_sequence(self, features, sample_dict, cdx):
        _features = _slice_namespace(features, cdx)

        sample_s = sample_dict["S"][cdx]
        onehot_feature_s = torch.nn.functional.one_hot(_features.S, 21)
        onehot_sample_s = torch.nn.functional.one_hot(sample_s, 21)

        loss_mask = self._out.loss_mask[cdx]

        upper = torch.sum(
            torch.sum(onehot_feature_s * onehot_sample_s, axis=-1) * loss_mask,
        )
        lower = torch.sum(loss_mask)
        sequence_recovery_rate = upper / lower

        seq_initial = protein_mpnn_utils._S_to_seq(sample_s, _features.chain_mask)

        start = 0
        end = 0
        list_of_AAs = [None] * len(_features.masked_list_list)
        for mdx, mask_l in enumerate(_features.masked_chain_length_list_list):
            end += mask_l
            list_of_AAs[mdx] = seq_initial[start:end]
            start = end
        sorted_indices = np.argsort(_features.masked_list_list)
        seq_initial = list(np.array(list_of_AAs)[sorted_indices])

        l0 = 0
        for mc_length in np.array(_features.masked_chain_length_list_list)[
            sorted_indices
        ][:-1]:
            l0 += mc_length
            seq_initial.insert(l0, "/")
            l0 += 1

        seq_final = "".join(seq_initial)
        return seq_final, sequence_recovery_rate

    def _generate_scores(
        self,
        S_sample,
        features,
        random_prompt,
        use_decoding_order=False,
        decoding_order=None,
    ):
        # run the model to get the log probabilities
        log_probs = self.model(
            features.X,
            S_sample,  # features.S,
            features.mask,
            features.chain_mask * features.chain_mask_pos,
            features.residue_idx,
            features.chain_encoding_all,
            random_prompt,
            use_input_decoding_order=use_decoding_order,
            decoding_order=decoding_order,
        )
        self._out.log_probabilities = log_probs

        # then calculate the scores based on the log probabilities
        scores = protein_mpnn_utils._scores(S_sample, log_probs, self._out.loss_mask)
        self._out.scores = scores
        return scores

    def _prepare_sampler(self, inputs):
        if inputs.tied_positions is not None:
            _sampler = self.model.tied_sample

            def _sampler_arguments(features, inputs):
                kwargs = features._asdict()
                kwargs["S_true"] = kwargs.pop("S")
                kwargs["chain_M_pos"] = kwargs.pop("chain_mask_pos")
                kwargs["bias_by_res"] = kwargs.pop("bias_by_res_all")
                kwargs["omit_AAs_np"] = inputs.omit
                kwargs["bias_AAs_np"] = inputs.bias
                for i in list(kwargs.keys()):
                    if i not in _sampler_kwargs_keys:
                        kwargs.pop(i, None)
                kwargs.update(self.pssm)
                kwargs.pop("pssm_threshold")
                return kwargs

        else:
            _sampler = self.model.sample

            def _sampler_arguments(features, inputs):
                kwargs = features._asdict()
                kwargs["S_true"] = kwargs.pop("S")
                kwargs["chain_M_pos"] = kwargs.pop("chain_mask_pos")
                kwargs["bias_by_res"] = kwargs.pop("bias_by_res_all")
                kwargs["omit_AAs_np"] = inputs.omit
                kwargs["bias_AAs_np"] = inputs.bias
                for i in list(kwargs.keys()):
                    if i not in _sampler_kwargs_keys:
                        kwargs.pop(i, None)
                kwargs.update(self.pssm)
                kwargs.pop("pssm_threshold")
                for i in ("tied_pos", "tied_beta"):
                    kwargs.pop(i, None)
                return kwargs

        return _sampler, _sampler_arguments


class TempOutputs:
    def __init__(self):
        self.log_probabilities = None
        self.loss_mask = None
        self.sequences = []
        self.extra = {}
        self.protein_name = None
        self.scores = None


protein_mpnn_input_data = namedtuple(
    "ProteinMPNNInputData",
    [
        "dataset",
        "bias",
        "omit",
        "n_batches",
        "chain_dict",
        "tied_positions",
    ],
)

featurize_namespace = namedtuple(
    "ProteinFeaturizeNamespace",
    [
        "X",
        "S",
        "mask",
        "lengths",
        "chain_mask",
        "chain_encoding_all",
        "chain_list_list",
        "visible_list_list",
        "masked_list_list",
        "masked_chain_length_list_list",
        "chain_mask_pos",
        "omit_AA_mask",
        "residue_idx",
        "dihedral_mask",
        "tied_pos_list_of_lists_list",
        "pssm_coef",
        "pssm_bias",
        "pssm_log_odds_all",
        "bias_by_res_all",
        "tied_beta",
    ],
)


_sampler_kwargs_keys = (
    "X",
    "randn",
    "S_true",
    "chain_mask",
    "chain_encoding_all",
    "residue_idx",
    "mask",
    "temperature",
    "omit_AAs_np",
    "bias_AAs_np",
    "chain_M_pos",
    "omit_AA_mask",
    "pssm_coef",
    "pssm_bias",
    "pssm_multi",
    "pssm_log_odds_flag",
    "pssm_log_odds_mask",
    "pssm_bias_flag",
    "tied_pos",
    "tied_beta",
    "bias_by_res",
)
"""
Those are the keys that are passed to the sampler function (with tied - since that's the 'bigger' one)
"""


def _slice_namespace(namespace, index: int):
    out_class = type(namespace)
    out = out_class(*[i[index] for i in namespace])
    return out


def _prepare_model_input(
    pdbfile: str,
    n: int,
    design_chains: list = None,
    fixed_chains: list = None,
    homomer: bool = False,
    copies: int = 1,
):
    """
    Prepare the input for the ProteinMPNN model.
    Supports heteromer design via chain_dict logic.
    """
    all_chains_in_pdb = None

    if design_chains is None:
        all_chains_in_pdb = get_chain_ids(pdbfile)

        if fixed_chains:
            design_chains = [c for c in all_chains_in_pdb if c not in fixed_chains]
        else:
            design_chains = all_chains_in_pdb

    if fixed_chains is None:
        fixed_chains = []

    load_chains = list(set(design_chains + fixed_chains))

    n_batches = n // copies

    bias_array = np.zeros(N_ALPHABET)
    omit_array = np.zeros(N_ALPHABET, dtype=np.float32)
    omit_array[-1] = 1.0

    pdb_dict_list = protein_mpnn_utils.parse_PDB(pdbfile, input_chain_list=load_chains)
    dataset = protein_mpnn_utils.StructureDatasetPDB(
        pdb_dict_list, truncate=None, max_length=MAX_LENGTH
    )

    if not pdb_dict_list:
        raise ValueError(f"Could not parse chains {load_chains} from {pdbfile}")

    chain_dict = {pdb_dict_list[0]["name"]: (design_chains, fixed_chains)}

    if homomer:
        tied_positions = _make_tied_positions_for_homomers(pdb_dict_list)
    else:
        tied_positions = None

    final = protein_mpnn_input_data(
        dataset=dataset,
        bias=bias_array,
        omit=omit_array,
        n_batches=n_batches,
        chain_dict=chain_dict,
        tied_positions=tied_positions,
    )

    return final


def _featurize(proteins, inputs, device):
    """
    Featurize a protein.

    Parameters
    ----------
    proteins : list
        List of proteins.
    inputs : ProteinMPNNInputData
        The input data for the ProteinMPNN model.
    device : torch.device
        The device to use.

    Returns
    -------
    ProteinFeaturizeNamespace
        The featurized protein.
    """
    out = protein_mpnn_utils.tied_featurize(
        batch=proteins,
        device=device,
        chain_dict=inputs.chain_dict,
        tied_positions_dict=inputs.tied_positions,
    )
    return featurize_namespace(*out)


def _make_tied_positions_for_homomers(pdb_dict_list: list):
    """
    If using `homomer` mode, create a dictionary of tied positions for each homomer.
    """
    tied_positions = {}
    for pdb in pdb_dict_list:
        chain_list = [i[-1:] for i in list(pdb) if i[:9] == "seq_chain"]
        chain_list.sort()

        tied_positions_list = []
        chain_length = len(pdb[f"seq_chain_{chain_list[0]}"])
        for i in range(1, chain_length + 1):
            sub_dict = {}
            for chain in chain_list:
                sub_dict[chain] = [i]

            tied_positions_list.append(sub_dict)

        tied_positions[pdb["name"]] = tied_positions_list
    return tied_positions
