test_sequences = [
    "SVLQVLHIPDERLRKVAKPVEEVNAEIQRIVDDMFETMYAEEGIGLAATQVDIHQRIIVIDVSENRDERLVLINPELLEKSGETGIEEGCLSIPEQRALVPRAEKVKIRALDRDGKPFELEADGLLAICIQHEMDHLVGKLFMDYLSPLKQQRIRQKVEKLDRLKARA",
    "SVLQVLHIPDERLRKVAKPVEEVNAEIQRIVDDMFETMYAEEGIGLAATQVDIHQRIIVIDVSENRDERLVLINPELLEKSGETGIEEGCLSIPEQRALVPRAEKVKIRALDRDGKPFELEADGLLAICIQHEMDHLVGKLFMDYLSPLKQQRIRQKVEKLDRLKARA",
]


def test_import():
    from frankenfold.core import msa

    assert msa.MMSeqs2Colab


def test_mmseqs2colab():

    from frankenfold.core.msa import MMSeqs2Colab

    msa = MMSeqs2Colab(user_agent="frankenfold/noah.kleinschmidt@unibe.ch")
    test_seq = (
        "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"
    )
    msa.submit([test_seq], pairing=None, env=True, filter=True)
    msa.wait()
    if msa.has_failed:
        raise Exception("MSA failed")
    result = msa.fetch_data()
    assert result.m8_raw_data is not None
    assert result.a3m_raw_data is not None
    assert result.template_raw_data is not None


def test_run_mmseqs2colab():
    import frankenfold.core as ff

    test_seq = (
        "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"
    )
    mmseqs = ff.MMSeqs2Colab(user_agent="frankenfold/noah.kleinschmidt@unibe.ch")
    msa = mmseqs.align(test_seq)
    assert msa.metadata is not None
    assert msa.alignment is not None

    a3m = msa.alignment

    lenght_before = len(a3m)
    msa.drop_insertions()
    lenght_after = len(a3m)
    assert lenght_after <= lenght_before
    msa.to_depth(128)
    assert len(a3m) == 128

    msa.export("tests/test_msa")


def test_mmseqs2colab_align_method():

    from frankenfold.core.msa import MMSeqs2Colab

    msa = MMSeqs2Colab(user_agent="frankenfold/noah.kleinschmidt@unibe.ch")
    test_seq = (
        "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"
    )
    result = msa(test_seq)
    assert result.m8_data is not None
    assert result.a3m_data is not None
    assert result.template_data is not None


def test_mmseqs2remote():

    from frankenfold.core.msa import MMSeqs2Remote

    msa = MMSeqs2Remote()
    msa.submit(test_sequences)
    assert msa.job_id != "", "Job ID not set"
    msa.wait()
    assert not msa.has_failed, "MSA failed"
    result = msa.get_result()
    assert len(result) != 0, "No result returned"
