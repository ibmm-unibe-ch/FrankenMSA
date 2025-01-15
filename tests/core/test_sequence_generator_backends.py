def test_import():
    from frankenfold.core import sequence_generators

    assert hasattr(sequence_generators, "SequenceGenerator")


def test_setup_protein_mpnn():
    from frankenfold.core.sequence_generators import ProteinMPNN

    generator = ProteinMPNN()

    assert generator.model is not None
