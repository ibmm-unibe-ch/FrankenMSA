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
    result = msa.get_result()
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
