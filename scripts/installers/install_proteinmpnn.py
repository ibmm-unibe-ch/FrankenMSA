from __future__ import annotations

import argparse
from pathlib import Path

from common import best_effort_git_lfs_pull
from common import download_file
from common import ensure_git_checkout
from common import install_python_packages
from common import is_colab_runtime


DEFAULT_ROOT = (
    Path("/content/ProteinMPNN")
    if is_colab_runtime()
    else Path.cwd() / "external" / "ProteinMPNN"
)
DEFAULT_REF = "main"
REPOSITORY_URL = "https://github.com/dauparas/ProteinMPNN.git"
WEIGHT_CATEGORIES = ("vanilla", "soluble", "ca")
WEIGHT_FILENAME = "v_48_020.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install or refresh a ProteinMPNN checkout."
    )
    parser.add_argument(
        "--root", default=str(DEFAULT_ROOT), help="Installation target directory."
    )
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git ref to check out.")
    parser.add_argument(
        "--install-python-deps",
        action="store_true",
        help="Install lightweight Python dependencies required by ProteinMPNN wrappers.",
    )
    parser.add_argument(
        "--skip-weight-check",
        action="store_true",
        help="Skip the fallback weight validation and direct-download step.",
    )
    return parser.parse_args()


def ensure_weights(root: Path) -> None:
    best_effort_git_lfs_pull(root)

    for category in WEIGHT_CATEGORIES:
        weight_dir = root / f"{category}_model_weights"
        weight_path = weight_dir / WEIGHT_FILENAME
        if weight_path.is_file() and weight_path.stat().st_size > 1000:
            continue

        url = f"https://github.com/dauparas/ProteinMPNN/raw/main/{category}_model_weights/{WEIGHT_FILENAME}?download="
        download_file(url, weight_path)


def main() -> None:
    args = parse_args()
    root = ensure_git_checkout(REPOSITORY_URL, Path(args.root), ref=args.ref)

    if args.install_python_deps:
        install_python_packages(["biopython==1.83", "einops==0.7.0"])

    if not args.skip_weight_check:
        ensure_weights(root)

    print(root)


if __name__ == "__main__":
    main()
