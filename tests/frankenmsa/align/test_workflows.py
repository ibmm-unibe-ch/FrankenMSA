import pandas as pd
import pytest

from frankenmsa.align.workflows import (
    attach_alignment_result,
    attach_plm_search_results,
    build_result_key,
    normalize_mmseqs_input,
    parse_plm_input,
    sanitize_result_token,
    validate_mmseqs_request,
    validate_similarity_cutoff,
)


def test_normalize_mmseqs_input_strips_headers_whitespace_and_uppercases():
    raw = ">seq1\n aa aa : bb\ncc \n"

    result = normalize_mmseqs_input(raw)

    assert result == "AAAA:BBCC"


def test_validate_mmseqs_request_detects_multimer_and_errors_on_invalid_pairing():
    assert validate_mmseqs_request("AAAA:BBBB", "complete") is True
    assert validate_mmseqs_request("AAAA", "none") is False

    with pytest.raises(ValueError, match="Please select 'Greedy' or 'All'"):
        validate_mmseqs_request("AAAA:BBBB", "none")

    with pytest.raises(ValueError, match="Please select 'None'"):
        validate_mmseqs_request("AAAA", "greedy")


def test_build_result_key_counts_existing_matches():
    msa_data = {"mmseqs_1": {}, "mmseqs_chainA": {}, "mmseqs_2": {}}

    assert build_result_key(msa_data, "mmseqs") == "mmseqs_3"


def test_attach_alignment_result_preserves_multimer_header():
    df = pd.DataFrame({"header": ["q1"], "sequence": ["AAAA"]})

    result = attach_alignment_result({}, "mmseqs_1", df, "#4\t1")

    assert result["mmseqs_1"]["_multimer_header"] == ["#4\t1"]


def test_parse_plm_input_reads_fasta_records():
    sequences, descriptions = parse_plm_input(">q1\nAAAA\n>q2\nBBBB\n")

    assert sequences == ["AAAA", "BBBB"]
    assert descriptions == ["q1", "q2"]


def test_validate_similarity_cutoff_bounds():
    validate_similarity_cutoff(0.0)
    validate_similarity_cutoff(1.0)

    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        validate_similarity_cutoff(1.2)


def test_attach_plm_search_results_sanitizes_query_names():
    df = pd.DataFrame(
        {
            "query": ["query one", "query/two"],
            "header": ["h1", "h2"],
            "sequence": ["AAAA", "BBBB"],
        }
    )

    msa_data, main_key, new_keys = attach_plm_search_results({}, df)

    assert main_key == "plm_search_query_one_1"
    assert new_keys == ["plm_search_query_one_1", "plm_search_query_two_2"]
    assert msa_data["plm_search_query_two_2"]["sequence"] == ["BBBB"]


def test_sanitize_result_token_falls_back_for_empty_values():
    assert sanitize_result_token("a/b c") == "a_b_c"
    assert sanitize_result_token("!!!") == "query"
