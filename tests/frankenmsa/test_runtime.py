from pathlib import Path

from frankenmsa.runtime import build_app_launch_env
from frankenmsa.runtime import collect_download_roots
from frankenmsa.runtime import detect_runtime
from frankenmsa.runtime import get_log_path
from frankenmsa.runtime import normalize_runtime_environment


def test_detect_runtime_prefers_canonical_runtime():
    env = {"FRANKEN_RUNTIME": "colab", "ON_COLAB": "0"}

    assert detect_runtime(env) == "colab"


def test_normalize_runtime_environment_sets_compat_flags():
    env = {}

    normalize_runtime_environment(env, runtime="local")

    assert env["FRANKEN_RUNTIME"] == "local"
    assert env["ON_COLAB"] == "0"
    assert env["FRANKEN_COLAB"] == "0"
    assert env["FRANKEN_LOCAL"] == "1"


def test_build_app_launch_env_sets_runtime_and_public_url():
    env = build_app_launch_env(
        port=8050,
        host="0.0.0.0",
        render_mode="external",
        runtime="colab",
        use_ngrok=True,
        public_url="https://example.ngrok.app",
        base_env={"PYTHONPATH": "existing"},
        pythonpath_prefix="/content",
    )

    assert env["FRANKEN_RUNTIME"] == "colab"
    assert env["ON_COLAB"] == "1"
    assert env["PORT"] == "8050"
    assert env["FRANKEN_USE_NGROK"] == "1"
    assert env["COLAB_TUNNEL_URL"] == "https://example.ngrok.app"
    assert env["PYTHONPATH"] == "/content:existing"


def test_get_log_path_uses_override():
    path = get_log_path({"FRANKEN_LOG_FILE": "~/custom-franken.log"})

    assert path == Path("~/custom-franken.log").expanduser()


def test_collect_download_roots_includes_override_without_duplicates(tmp_path):
    roots = collect_download_roots(
        project_root=tmp_path,
        env={
            "FRANKEN_RUNTIME": "local",
            "PROTEINMPNN_OUT_DIR": str(tmp_path / "ProteinMPNN" / "outputs_local"),
        },
    )

    assert roots.count(str(tmp_path / "ProteinMPNN" / "outputs_local")) == 1
