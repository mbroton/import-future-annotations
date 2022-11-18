from __future__ import annotations

import argparse
import ast
import os
import sys


def _is_annotations_import(source: str) -> bool:
    root = ast.parse(source)
    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.ImportFrom):
            if (
                node.module == "__future__"
                and node.names[0].name == "annotations"
            ):
                return True
    return False


def _fix_file(filename: str, args: argparse.Namespace) -> int:
    if not args.allow_empty and os.stat(filename).st_size <= 0:
        return 0

    with open(filename, "r+") as f:
        content = f.read()
        if not _is_annotations_import(content):
            if not args.check_only:
                print(
                    f"Adding annotations import to {filename}", file=sys.stderr
                )
                f.seek(0)
                f.write("from __future__ import annotations\n")
                f.write(content)
            return 1
    return 0


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="import-future-annotations",
        description=(
            "Add import responsible for postponed evaluation "
            "of annotations to python files"
        ),
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Don't modify files, only check.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Don't skip files of size 0.",
    )
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)

    status = 0
    for filename in args.filenames:
        status |= _fix_file(filename, args)

    return status
