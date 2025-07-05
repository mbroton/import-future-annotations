import argparse
import uuid

import pytest

from import_future_annotations import _fix_file
from import_future_annotations import _insert_future_import
from import_future_annotations import _is_annotations_import
from import_future_annotations import main

IMPORT_ANNOTATIONS = "from __future__ import annotations"
TEMP_DIR_NAME = "import_future_annotations_test"


file_without_import = """import os
import dataclasses
from collections import defaultdict
from enum import Enum
from pathlib import PurePath
from types import GeneratorType
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel


def generate_encoders_by_class_tuples(
    type_encoder_map: Dict[Any, Callable[[Any], Any]]
) -> Dict[Callable[[Any], Any], Tuple[Any, ...]]:
    encoders_by_class_tuples: Dict[Callable[[Any], Any], Tuple[Any, ...]] = defaultdict(
        tuple
    )
    for type_, encoder in type_encoder_map.items():
        encoders_by_class_tuples[encoder] += (type_,)
    return encoders_by_class_tuples"""  # noqa: E501

file_with_import = """from __future__ import annotations
import sys
import typing
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import typing_extensions

from ._internal import _repr, _typing_extra, _utils
from .main import BaseModel, create_model

GenericModelT = TypeVar('GenericModelT', bound='GenericModel')
TypeVarType = Any  # since mypy doesn't allow the use of TypeVar as a type

Parametrization = Mapping[TypeVarType, Type[Any]]
"""

file_syntax_error = """from __future__
import os


prin t
"""

file_with_single_line_docstring = '''"""This is a single line docstring."""
import os
import sys

def hello():
    return "world"
'''

file_with_multiline_docstring = '''"""
This is a multiline docstring.
It spans multiple lines.
"""
import os
import sys

def hello():
    return "world"
'''

file_with_triple_single_quotes = """'''
This is a docstring with triple single quotes.
'''
import os
import sys
"""

file_with_docstring_and_future_import = '''"""This is a docstring."""
from __future__ import annotations
import os
import sys
'''

file_with_only_docstring = '''"""This is just a docstring."""
'''


@pytest.fixture
def temp_file(tmp_path):
    d = tmp_path / TEMP_DIR_NAME
    d.mkdir(exist_ok=True)
    f = d / str(uuid.uuid4().hex)
    return f


def test_func_is_annotations_import_on_file_without_it():
    assert _is_annotations_import(file_without_import) is False


def test_func_is_annotations_import_on_file_with_it():
    assert _is_annotations_import(file_with_import) is True


def test_func_is_annotations_import_on_file_with_invalid_syntax():
    with pytest.raises(SyntaxError):
        _is_annotations_import(file_syntax_error)


_common_data_set = pytest.mark.parametrize(
    (
        "check_only",
        "allow_empty",
        "source",
        "expected_content",
        "expected_exit_code",
    ),
    (
        (
            False,
            False,
            file_without_import,
            f"{IMPORT_ANNOTATIONS}\n{file_without_import}",
            1,
        ),
        (True, False, file_without_import, file_without_import, 1),
        (False, False, file_with_import, file_with_import, 0),
        (True, False, file_with_import, file_with_import, 0),
        (False, False, "", "", 0),
        (True, False, "", "", 0),
        (True, True, "", "", 1),
        (False, True, "", f"{IMPORT_ANNOTATIONS}\n", 1),
    ),
)


@_common_data_set
def test_fix_file_valid(
    temp_file,
    check_only,
    allow_empty,
    source,
    expected_content,
    expected_exit_code,
):
    temp_file.write_text(source)
    ns = argparse.Namespace(check_only=check_only, allow_empty=allow_empty)
    exit_code = _fix_file(temp_file.resolve(), args=ns)
    assert exit_code == expected_exit_code
    assert temp_file.read_text() == expected_content


def test_fix_file_invalid_syntax(temp_file):
    temp_file.write_text(file_syntax_error)
    ns = argparse.Namespace(check_only=False, allow_empty=True)
    exit_code = _fix_file(temp_file.resolve(), ns)
    assert exit_code == 0  # Should skip files with syntax errors
    assert temp_file.read_text() == file_syntax_error  # File should be unchanged


@_common_data_set
def test_main(
    temp_file,
    check_only,
    allow_empty,
    source,
    expected_content,
    expected_exit_code,
):
    temp_file.write_text(source)
    args = [str(temp_file.resolve())]
    if check_only:
        args.append("--check-only")
    if allow_empty:
        args.append("--allow-empty")

    exit_code = main(args)
    assert exit_code == expected_exit_code
    assert temp_file.read_text() == expected_content


def test_main_multiple_files(tmp_path):
    files = [tmp_path / str(uuid.uuid4().hex) for _ in range(3)]
    sources = [file_without_import, file_with_import, ""]
    for file, source in zip(files, sources):
        file.write_text(source)

    paths = [str(f.resolve()) for f in files]
    args = [*paths]

    exit_code = main(args)
    assert exit_code == 1
    assert files[0].read_text() == f"{IMPORT_ANNOTATIONS}\n{sources[0]}"
    assert [f.read_text() for f in files[1:]] == sources[1:]


def test_main_no_files():
    args = []
    exit_code = main(args)
    assert exit_code == 0


def test_insert_future_import_with_single_line_docstring():
    expected = '''"""This is a single line docstring."""
from __future__ import annotations
import os
import sys

def hello():
    return "world"
'''
    result = _insert_future_import(file_with_single_line_docstring)
    assert result == expected


def test_insert_future_import_with_multiline_docstring():
    expected = '''"""
This is a multiline docstring.
It spans multiple lines.
"""
from __future__ import annotations
import os
import sys

def hello():
    return "world"
'''
    result = _insert_future_import(file_with_multiline_docstring)
    assert result == expected


def test_insert_future_import_with_triple_single_quotes():
    expected = """'''
This is a docstring with triple single quotes.
'''
from __future__ import annotations
import os
import sys
"""
    result = _insert_future_import(file_with_triple_single_quotes)
    assert result == expected


def test_insert_future_import_with_only_docstring():
    expected = '''"""This is just a docstring."""
from __future__ import annotations
'''
    result = _insert_future_import(file_with_only_docstring)
    assert result == expected


def test_insert_future_import_with_empty_file():
    result = _insert_future_import("")
    assert result == "from __future__ import annotations\n"


def test_insert_future_import_with_whitespace_only():
    result = _insert_future_import("   \n  \n")
    assert result == "from __future__ import annotations\n"


def test_insert_future_import_with_syntax_error():
    with pytest.raises(SyntaxError):
        _insert_future_import(file_syntax_error)


def test_insert_future_import_no_docstring():
    result = _insert_future_import(file_without_import)
    expected = f"from __future__ import annotations\n{file_without_import}"
    assert result == expected


@pytest.mark.parametrize(
    ("source", "expected_content", "expected_exit_code"),
    [
        (
            file_with_single_line_docstring,
            '''"""This is a single line docstring."""
from __future__ import annotations
import os
import sys

def hello():
    return "world"
''',
            1,
        ),
        (
            file_with_multiline_docstring,
            '''"""
This is a multiline docstring.
It spans multiple lines.
"""
from __future__ import annotations
import os
import sys

def hello():
    return "world"
''',
            1,
        ),
        (
            file_with_triple_single_quotes,
            """'''
This is a docstring with triple single quotes.
'''
from __future__ import annotations
import os
import sys
""",
            1,
        ),
        (
            file_with_docstring_and_future_import,
            file_with_docstring_and_future_import,
            0,
        ),
        (
            file_with_only_docstring,
            '''"""This is just a docstring."""
from __future__ import annotations
''',
            1,
        ),
    ],
)
def test_fix_file_with_docstrings(
    temp_file, source, expected_content, expected_exit_code
):
    temp_file.write_text(source)
    ns = argparse.Namespace(check_only=False, allow_empty=False)
    exit_code = _fix_file(temp_file.resolve(), args=ns)
    assert exit_code == expected_exit_code
    assert temp_file.read_text() == expected_content


@pytest.mark.parametrize(
    ("source", "expected_content", "expected_exit_code"),
    [
        (
            file_with_single_line_docstring,
            file_with_single_line_docstring,
            1,
        ),
        (
            file_with_multiline_docstring,
            file_with_multiline_docstring,
            1,
        ),
        (
            file_with_docstring_and_future_import,
            file_with_docstring_and_future_import,
            0,
        ),
    ],
)
def test_fix_file_with_docstrings_check_only(
    temp_file, source, expected_content, expected_exit_code
):
    temp_file.write_text(source)
    ns = argparse.Namespace(check_only=True, allow_empty=False)
    exit_code = _fix_file(temp_file.resolve(), args=ns)
    assert exit_code == expected_exit_code
    assert temp_file.read_text() == expected_content


def test_is_annotations_import_with_docstring_files():
    assert _is_annotations_import(file_with_single_line_docstring) is False
    assert _is_annotations_import(file_with_multiline_docstring) is False
    assert _is_annotations_import(file_with_triple_single_quotes) is False
    assert _is_annotations_import(file_with_docstring_and_future_import) is True
    assert _is_annotations_import(file_with_only_docstring) is False


def test_main_with_syntax_error_file(tmp_path):
    files = [tmp_path / str(uuid.uuid4().hex) for _ in range(3)]
    sources = [file_without_import, file_syntax_error, file_with_import]
    for file, source in zip(files, sources):
        file.write_text(source)

    paths = [str(f.resolve()) for f in files]
    args = [*paths]

    exit_code = main(args)
    # Should return 1 because one file was modified
    assert exit_code == 1
    # First file should be modified
    assert files[0].read_text() == f"{IMPORT_ANNOTATIONS}\n{sources[0]}"
    # Second file (syntax error) should be unchanged
    assert files[1].read_text() == sources[1]
    # Third file already has import, should be unchanged
    assert files[2].read_text() == sources[2]


def test_main_check_only_with_syntax_error(tmp_path):
    files = [tmp_path / str(uuid.uuid4().hex) for _ in range(2)]
    sources = [file_without_import, file_syntax_error]
    for file, source in zip(files, sources):
        file.write_text(source)

    paths = [str(f.resolve()) for f in files]
    args = [*paths, "--check-only"]

    exit_code = main(args)
    # Should return 1 because one file needs import
    assert exit_code == 1
    # Both files should be unchanged in check-only mode
    assert files[0].read_text() == sources[0]
    assert files[1].read_text() == sources[1]
