def test_import():
    from frankenfold.core import sequence_generators

    assert hasattr(sequence_generators, "SequenceGenerator")


def test_setup_protein_mpnn():
    from frankenfold.core.sequence_generators import ProteinMPNN

    generator = ProteinMPNN()

    assert generator.model is not None


def test_protein_mpnn_generate():
    import os
    import torch

    if torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        device = "cuda:0"
    else:
        device = "cpu"
    from frankenfold.core.sequence_generators import ProteinMPNN

    generator = ProteinMPNN()
    generator.init()
    generator.model = generator.model.to(device)

    assert generator.model is not None
    assert generator._is_loaded
    assert generator.device is not None

    pdb = "tests/data/test_1.pdb"
    n = 10
    sequences, extra = generator.generate(pdb, n)
    assert len(sequences) == n
    assert all(isinstance(seq, str) for seq in sequences)
    assert len(extra["score"]) == n
    assert len(extra.keys()) == 5


def test_functional_api():

    import frankenfold as ff

    pdb = "tests/data/test_1.pdb"
    n = 3
    sequences, extra = ff.inverse_fold(pdb, n)
    assert len(sequences) == n
    assert all(isinstance(seq, str) for seq in sequences)
    assert len(extra["score"]) == n
    assert len(extra.keys()) == 5
