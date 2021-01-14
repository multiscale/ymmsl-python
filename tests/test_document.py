from typing import Callable

import pytest
import yatiml

from ymmsl.document import Document


@pytest.fixture
def load_document() -> Callable:
    return yatiml.load_function(Document)


@pytest.fixture
def dump_document() -> Callable:
    return yatiml.dumps_function(Document)


def test_valid_document(load_document: Callable) -> None:
    text = 'ymmsl_version: v0.1'
    load_document(text)


def test_load_unknown_version(load_document: Callable) -> None:
    text = 'ymmsl_version: v0.2'
    with pytest.raises(yatiml.RecognitionError):
        load_document(text)


def test_dump_document(dump_document: Callable) -> None:
    text = dump_document(Document())
    assert text == 'ymmsl_version: v0.1\n'
