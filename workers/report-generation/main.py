"""Local entry point for the report-generation worker skeleton."""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Acadence report-generation worker")
    parser.add_argument(
        "--smoke-check",
        action="store_true",
        help="check worker startup without running a report job",
    )
    args = parser.parse_args()

    if args.smoke_check:
        print("Report-generation worker startup check passed; no report job was run.")
        return 0

    print("Report generation is not implemented; no report job was run.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
