from pathlib import Path
from typing import Any, AnyStr, Callable, IO, Union
import yatiml

import pytest

from ymmsl.v0_2.identity import Identifier, Reference
from ymmsl.v0_2.imports import ImportKind, ImportStatement


LoadImport = Callable[[Union[str, Path, IO[AnyStr]]], Any]


@pytest.fixture
def load_import() -> LoadImport:
    return yatiml.load_function(ImportStatement, Identifier, ImportKind)


def test_load_import_statement1(load_import: LoadImport) -> None:
    imp = load_import('from nlesc.examples import implementation example')

    assert imp.module == 'nlesc.examples'
    assert imp.kind == ImportKind.IMPLEMENTATION
    assert imp.name == Identifier('example')


def test_load_import_statement2(load_import: LoadImport) -> None:
    imp = load_import('from nlesc import implementation example')

    assert imp.module == 'nlesc'
    assert imp.kind == ImportKind.IMPLEMENTATION
    assert imp.name == Identifier('example')


def test_save_import_statement() -> None:
    dumps_import = yatiml.dumps_function(
            Identifier, ImportKind, ImportStatement, Reference)
    imp = ImportStatement('nlesc.examples', 'implementation', 'example')
    text = dumps_import(imp)

    assert text == 'from nlesc.examples import implementation example\n...\n'


def test_load_invalid_import1(load_import: LoadImport) -> None:
    with pytest.raises(RuntimeError):
        load_import('frim nlesc.examples import implementation example')


def test_load_invalid_import2(load_import: LoadImport) -> None:
    with pytest.raises(RuntimeError):
        load_import('from nlesc,examples import implementation example')


def test_load_invalid_import3(load_import: LoadImport) -> None:
    with pytest.raises(RuntimeError):
        load_import('from nlesc.examples ompirt implementation example')


def test_load_invalid_import4(load_import: LoadImport) -> None:
    with pytest.raises(RuntimeError):
        load_import('from nlesc.examples import impelmentation example')


def test_load_invalid_import5(load_import: LoadImport) -> None:
    with pytest.raises(RuntimeError):
        load_import('from nlesc.examples import implementation 123example')


def test_load_invalid_import6(load_import: LoadImport) -> None:
    with pytest.raises(RuntimeError):
        load_import('from nlesc.examples[1] import implementation example')


def test_module_path() -> None:
    imp = ImportStatement('nlesc.examples', 'implementation', 'test')
    assert imp.module_path() == Path('nlesc/examples.ymmsl')

    imp = ImportStatement('nlesc', 'implementation', 'test')
    assert imp.module_path() == Path('nlesc.ymmsl')
