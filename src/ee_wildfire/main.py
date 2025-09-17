"""Minimal command line entry point for the refactored pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the wildfire dataset pipeline")
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the pipeline configuration YAML file",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_pipeline(args.config)


if __name__ == "__main__":  # pragma: no cover
    main()

