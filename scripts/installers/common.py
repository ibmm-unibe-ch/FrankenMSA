from __future__ import annotations

import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Iterable


def run_checked(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def ensure_git_checkout(
    repository_url: str, target_root: Path, ref: str = "main"
) -> Path:
    target_root = target_root.expanduser().resolve()
    parent = target_root.parent
    parent.mkdir(parents=True, exist_ok=True)

    if not target_root.exists():
        run_checked(["git", "clone", repository_url, str(target_root)])
    elif not (target_root / ".git").is_dir():
        raise RuntimeError(
            f"Target path exists but is not a git checkout: {target_root}"
        )

    run_checked(["git", "fetch", "--all", "--tags"], cwd=target_root)
    run_checked(["git", "checkout", ref], cwd=target_root)
    return target_root


def install_python_packages(packages: Iterable[str]) -> None:
    package_list = [package for package in packages if package]
    if not package_list:
        return
    run_checked([sys.executable, "-m", "pip", "install", *package_list])


def best_effort_git_lfs_pull(target_root: Path) -> None:
    subprocess.run(
        ["git", "lfs", "pull"],
        cwd=target_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response, destination.open(
        "wb"
    ) as handle:
        handle.write(response.read())


def is_colab_runtime() -> bool:
    return "COLAB_RELEASE_TAG" in os.environ or Path("/content").exists()
