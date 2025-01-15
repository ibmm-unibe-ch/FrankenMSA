"""
ProteinMPNN sequence generator backend.


"""

from pathlib import Path
import frankenfold.core.sequence_generators.backend as backend


class ProteinMPNN(backend.SequenceGenerator):
    """
    The ProteinMPNN sequence generator backend.
    """

    def __init__(self):
        super().__init__()

        self.remote_url = "https://github.com/dauparas/ProteinMPNN.git"
        self.checkpoint_path = "vanilla_model_weights/v_48_020.pt"

        self.setup_parameters = dict(
            hidden_dim=128,
            num_encoder_layers=3,
            num_decoder_layers=3,
            num_letters=21,
            node_features=128,
            edge_features=128,
            augment_eps=0.0,
        )

        self.local_path = "ProteinMPNN"

        # immediately initialize the backend
        self.init()

    def setup_model(self) -> "torch.Model":
        """
        Create the ProteinMPNN model.

        Returns
        -------
        torch.Model
            The ProteinMPNN model
        """
        import torch
        import protein_mpnn_utils

        checkpoint_path = Path(self.local_path) / self.checkpoint_path
        checkpoint = torch.load(str(checkpoint_path), weights_only=False)
        model = protein_mpnn_utils.ProteinMPNN(
            k_neighbors=checkpoint["num_edges"],
            **self.setup_parameters,
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        return model
