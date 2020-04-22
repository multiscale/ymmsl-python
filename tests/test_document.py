from typing import Type

import pytest
from ruamel import yaml
import yatiml

from ymmsl.document import Document


@pytest.fixture
def document_loader() -> Type:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [Document])
    yatiml.set_document_type(Loader, Document)
    return Loader


@pytest.fixture
def document_dumper() -> Type:
    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [Document])
    return Dumper


def test_valid_document(document_loader: Type) -> None:
    text = 'ymmsl_version: v0.1'
    yaml.load(text, Loader=document_loader)


def test_load_unknown_version(document_loader: Type) -> None:
    text = 'ymmsl_version: v0.2'
    with pytest.raises(yatiml.RecognitionError):
        yaml.load(text, Loader=document_loader)


def test_dump_document(document_dumper: Type) -> None:
    text = yaml.dump(Document(), Dumper=document_dumper)
    assert text == 'ymmsl_version: v0.1\n'
