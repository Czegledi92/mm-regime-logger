"""CLI entry point for the paper regime logger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from regime_logger.config import config_schema_description, load_config
from regime_logger.runner import run_paper_harness


def main() -> None:
    parser = argparse.ArgumentParser(
        description="JOB-20260917-MM-001 offline regime logger (research only)",
    )
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Run paper harness on stub data")
    run_parser.add_argument("--data", required=True, help="Path to CSV or Parquet stub")
    run_parser.add_argument(
        "--config",
        default="config/regime_logger.default.yaml",
        help="Path to YAML config",
    )
    run_parser.add_argument("--output-dir", default="output", help="Output directory")

    sub.add_parser("schema", help="Print config schema description")

    args = parser.parse_args()

    if args.command == "run":
        result = run_paper_harness(args.data, args.config, args.output_dir)
        print(json.dumps(result, indent=2))
    elif args.command == "schema":
        print(json.dumps(config_schema_description(), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
