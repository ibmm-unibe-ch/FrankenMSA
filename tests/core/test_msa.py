def test_msa_can_crop():
    from frankenfold import read_msa

    msa = read_msa("tests/test_msa.a3m")

    alignment = msa.alignment

    assert alignment is not None

    previous_length = len(alignment)
    alignment.crop(50, axis=0)
    assert len(alignment) == previous_length
    assert len(alignment.sequences[0]) == 50

    alignment.crop(50, axis=1)
    assert len(alignment) == 50


def test_msa_can_filter():
    from frankenfold import read_msa

    msa = read_msa("tests/test_msa.a3m")
    alignment = msa.alignment

    assert alignment is not None
    alignment.crop(50, axis=1)
    assert len(alignment) == 50
    alignment.filter(diff=10)
    assert 10 <= len(alignment) < 50
    alignment.to_depth(10, crop=True)
    assert len(alignment) == 10
