from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import MutableMapping, Optional

RUNTIME_ENV_VAR = "FRANKEN_RUNTIME"
RUNTIME_LOCAL = "local"
RUNTIME_COLAB = "colab"
LEGACY_COLAB_ENV_VARS = ("FRANKEN_COLAB", "ON_COLAB", "IN_COLAB")


def _env(env: Optional[MutableMapping[str, str]] = None) -> MutableMapping[str, str]:
    return os.environ if env is None else env


def detect_runtime(env: Optional[MutableMapping[str, str]] = None) -> str:
    env = _env(env)
    runtime = str(env.get(RUNTIME_ENV_VAR, "")).strip().lower()
    if runtime in {RUNTIME_LOCAL, RUNTIME_COLAB}:
        return runtime

    if any(str(env.get(name, "")).strip() == "1" for name in LEGACY_COLAB_ENV_VARS):
        return RUNTIME_COLAB

    if "google.colab" in sys.modules:
        return RUNTIME_COLAB

    if env.get("COLAB_RELEASE_TAG") or env.get("COLAB_GPU"):
        return RUNTIME_COLAB

    return RUNTIME_LOCAL


def is_colab_runtime(env: Optional[MutableMapping[str, str]] = None) -> bool:
    return detect_runtime(env) == RUNTIME_COLAB


def normalize_runtime_environment(
    env: Optional[MutableMapping[str, str]] = None,
    runtime: Optional[str] = None,
) -> MutableMapping[str, str]:
    env = _env(env)
    resolved_runtime = runtime or detect_runtime(env)
    if resolved_runtime not in {RUNTIME_LOCAL, RUNTIME_COLAB}:
        raise ValueError(f"Unsupported runtime: {resolved_runtime}")

    env[RUNTIME_ENV_VAR] = resolved_runtime
    colab_flag = "1" if resolved_runtime == RUNTIME_COLAB else "0"
    local_flag = "0" if resolved_runtime == RUNTIME_COLAB else "1"
    env["FRANKEN_COLAB"] = colab_flag
    env["ON_COLAB"] = colab_flag
    env["IN_COLAB"] = colab_flag
    env["FRANKEN_LOCAL"] = local_flag
    return env


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_log_path(env: Optional[MutableMapping[str, str]] = None) -> Path:
    env = _env(env)
    override = str(env.get("FRANKEN_LOG_FILE", "")).strip()
    if override:
        return Path(override).expanduser()

    if is_colab_runtime(env):
        return Path("/content/app/log.txt")

    return get_repo_root() / "log.txt"


def log_message(message: str, env: Optional[MutableMapping[str, str]] = None) -> None:
    log_path = get_log_path(env)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{message}\n")


def get_upload_dir(env: Optional[MutableMapping[str, str]] = None) -> str:
    env = _env(env)
    override = str(env.get("FRANKENMSA_UPLOAD_DIR", "")).strip()
    if override:
        base = Path(override).expanduser()
    elif is_colab_runtime(env):
        base = Path("/content/ProteinMPNN/uploads")
    else:
        base = Path.home() / ".frankenmsa" / "uploads"

    try:
        base.mkdir(parents=True, exist_ok=True)
    except Exception:
        base = Path(tempfile.gettempdir()) / "frankenmsa_uploads"
        base.mkdir(parents=True, exist_ok=True)
    return str(base)


def collect_download_roots(
    project_root: Optional[Path] = None,
    env: Optional[MutableMapping[str, str]] = None,
) -> list[str]:
    env = _env(env)
    project_root = project_root or get_repo_root()
    roots: list[str] = []

    if is_colab_runtime(env):
        roots.extend(["/content", "/content/ProteinMPNN/outputs_run"])

    local_repo = project_root / "ProteinMPNN"
    roots.append(str(local_repo / "outputs_run"))
    roots.append(str(local_repo / "outputs_local"))

    out_override = str(env.get("PROTEINMPNN_OUT_DIR", "")).strip()
    if out_override:
        roots.append(out_override)

    deduped: list[str] = []
    seen = set()
    for root in roots:
        if not root:
            continue
        normalized = str(Path(root).expanduser())
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def build_app_launch_env(
    port: int,
    host: str,
    render_mode: str,
    runtime: str,
    use_ngrok: bool = False,
    public_url: Optional[str] = None,
    base_env: Optional[MutableMapping[str, str]] = None,
    pythonpath_prefix: Optional[str] = None,
) -> dict[str, str]:
    env = dict(_env(base_env))
    normalize_runtime_environment(env, runtime=runtime)
    env["PORT"] = str(port)
    env["HOST"] = host
    env["FRANKEN_RENDER_MODE"] = render_mode
    env["FRANKEN_USE_NGROK"] = "1" if use_ngrok else "0"
    if pythonpath_prefix:
        env["PYTHONPATH"] = f"{pythonpath_prefix}:{env.get('PYTHONPATH', '')}"
    if public_url:
        env["COLAB_TUNNEL_URL"] = public_url
    else:
        env.pop("COLAB_TUNNEL_URL", None)
    return env