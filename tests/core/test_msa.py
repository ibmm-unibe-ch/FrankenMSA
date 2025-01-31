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


def test_msa_from_seqs_and_dict():
    import frankenfold as ff

    seqs = [
        "SVLQVLHIPDERLRKVAKPVEEVNAEIQRIVDDMFETMYAEEGIGLAATQVDIHQRIIVIDVSENRDERLVLINPELLEKSGETGIEEGCLSIPEQRALVPRAEKVKIRALDRDGKPFELEADGLLAICIQHEMDHLVGKLFMDYLSPLKQQRIRQKVEKLDRLKARA",
    ] * 3
    extra = {"name": ["test1", "test2", "test3"], "score": [1, 2, 3], "tag": [1, 2, 3]}
    alignment = ff.A3MAlignment.from_sequences(seqs, extra)

    assert alignment is not None
    assert len(alignment) == 3
    assert alignment.sequences[0] == seqs[0]
    assert alignment.extra_df.shape == (3, 3)
    assert alignment.extra.shape == (3,)
    assert len(alignment.extra[0]) == 4

    alignment = ff.A3MAlignment.from_sequences(seqs, extra, headers_key="name")

    assert alignment is not None
    assert len(alignment) == 3
    assert alignment.sequences[0] == seqs[0]
    assert alignment.extra_df.shape == (3, 3)
    assert len(alignment.extra[0]) == 3
