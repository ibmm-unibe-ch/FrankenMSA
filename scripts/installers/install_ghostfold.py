from __future__ import annotations

import argparse

from common import install_python_packages


DEFAULT_PACKAGE = "ghostfold"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install or upgrade the GhostFold Python package."
    )
    parser.add_argument(
        "--package",
        default=DEFAULT_PACKAGE,
        help="GhostFold package spec passed to pip install.",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Pass --upgrade to pip when installing GhostFold.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    package_spec = args.package.strip()
    if not package_spec:
        raise SystemExit("--package must not be empty")

    packages = [package_spec]
    if args.upgrade:
        packages.insert(0, "--upgrade")

    install_python_packages(packages)
    print(package_spec)


if __name__ == "__main__":
    main()
