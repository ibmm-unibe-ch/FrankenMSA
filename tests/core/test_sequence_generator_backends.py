def test_import():
    from frankenfold.core import sequence_generators

    assert sequence_generators.backend_dir_exists
    assert sequence_generators.get_backend_dir

    assert len(sequence_generators.AVAILABLE_BACKENDS) > 0
    assert "ProteinMPNN" in sequence_generators.AVAILABLE_BACKENDS


def test_setup_protein_mpnn():
    from frankenfold.core.sequence_generators import set_backend

    set_backend("ProteinMPNN")
