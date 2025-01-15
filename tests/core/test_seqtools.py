

def test_is_valid():
    from frankenfold.core import seqtools

    seq1 = "ACDEFGHIKLMNPQRSTVWY"
    seq2 = "acdefghiklmnpqrstvwyx"
    seq3 = "ACDEFGHIKLMNPQRSTVWYXZ"
    assert seqtools.is_valid_peptide_sequence(seq1)
    assert seqtools.is_valid_peptide_sequence(seq2)
    assert not seqtools.is_valid_peptide_sequence(seq3)

def test_vet_sequence():
    from frankenfold.core import seqtools

    seq1 = "ACDEFGHIKLMNPQRSTVWY"
    seq2 = "acdefghiklmnpqrstvwyx"
    seq3 = "ACDEFGHIKLMNPQRSTVWYXZ"
    assert seqtools.vet_sequence(seq1) == seq1
    assert seqtools.vet_sequence(seq2) == seq2.upper()
    assert seqtools.vet_sequence(seq3) == seq1 + "X" * 2

