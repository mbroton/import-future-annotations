from __future__ import annotations

import argparse
import os
import re
import sys


IMPORT_LINE = "from __future__ import annotations\n"
REGEXP = r"^from __future__ import annotations\s*"


def _fix_file(filename: str, args: argparse.Namespace) -> int:
    if args.skip_empty and os.stat(filename).st_size <= 0:
        return 0

    with open(filename, "r+") as f:
        content = f.read()
        is_match = bool(re.search(REGEXP, content))
        if not is_match:
            if not args.check_only:
                print(f"Rewriting {filename}")
                f.seek(0)
                f.write(IMPORT_LINE)
                f.write(content)
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="import-future-annotations",
        description=(
            "Add import responsible for postponed evaluation "
            "of annotations to python files"
        ),
    )
    parser.add_argument("--check-only", action="store_true", help="Doesn't modify files, only checks.")
    parser.add_argument("--skip-empty", action="store_false", help="Skip files of size 0.")
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(sys.argv)

    status = 0
    for filename in args.filenames[1:]:
        status |= _fix_file(filename, args)

    return status
