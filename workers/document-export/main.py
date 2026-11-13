"""Local entry point for the document-export worker skeleton."""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Acadence document-export worker")
    parser.add_argument(
        "--smoke-check",
        action="store_true",
        help="check worker startup without running an export job",
    )
    args = parser.parse_args()

    if args.smoke_check:
        print("Document-export worker startup check passed; no export job was run.")
        return 0

    print("Export execution is not implemented; no export job was run.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
