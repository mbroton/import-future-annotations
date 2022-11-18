import argparse
import uuid

import pytest

from import_future_annotations import _fix_file
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
    with pytest.raises(SyntaxError):
        _fix_file(temp_file.resolve(), ns)


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
