from collections import OrderedDict
from pathlib import Path
from typing import Any, IO

import pytest

from ymmsl import (ComputeElement, Conduit, dump, Experiment, Identifier,
                   load, save, Model, ModelReference, YmmslDocument)


@pytest.fixture
def tmpdir_path(tmpdir: Any) -> Path:
    return Path(str(tmpdir))


def test_load_string1(test_yaml1: str) -> None:
    document = load(test_yaml1)
    experiment = document.experiment
    assert experiment is not None
    assert str(experiment.model) == 'test_model'
    assert len(experiment.parameter_values) == 3
    assert isinstance(experiment.parameter_values[2].value, list)
    assert experiment.parameter_values[2].value[1] == 1.3

    text = 'version: v0.1\n'
    document = load(text)
    assert document.version == 'v0.1'


def test_load_string2(test_yaml2: str) -> None:
    document = load(test_yaml2)
    model = document.model
    assert isinstance(model, Model)
    assert str(model.name) == 'test_model'
    assert len(model.compute_elements) == 5
    assert str(model.compute_elements[4].name) == 'bf2smc'
    assert str(model.compute_elements[2].implementation) == 'isr2d.blood_flow'
    assert len(model.conduits) == 5
    assert str(model.conduits[0].sender) == 'ic.out'
    assert str(model.conduits[1].sending_port()) == 'cell_positions'
    assert str(model.conduits[3].receiving_compute_element()) == 'bf2smc'


def test_load_string3(test_yaml3: str) -> None:
    document = load(test_yaml3)
    assert isinstance(document.model, ModelReference)
    assert str(document.model.name) == 'test_model'


def test_load_file(test_yaml1: str, tmpdir_path: Path) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'
    with test_file.open('w') as f:
        f.write(test_yaml1)

    with test_file.open('r') as f:
        document = load(f)

    assert document.experiment is not None
    assert str(document.experiment.model) == 'test_model'


def test_load_path(test_yaml1: str, tmpdir_path: Path) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'
    with test_file.open('w') as f:
        f.write(test_yaml1)

    document = load(test_file)
    assert document.experiment is not None
    assert str(document.experiment.model) == 'test_model'


def test_dump1(test_yaml1: str, test_doc1: YmmslDocument) -> None:
    text = dump(test_doc1)
    assert text == test_yaml1


def test_dump2(test_yaml2: str, test_doc2: YmmslDocument) -> None:
    text = dump(test_doc2)
    assert text == test_yaml2


def test_dump3(test_yaml3: str, test_doc3: YmmslDocument) -> None:
    text = dump(test_doc3)
    assert text == test_yaml3


def test_save_str(test_doc1: YmmslDocument, test_yaml1: str, tmpdir_path: Path
                  ) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'

    save(test_doc1, str(test_file))

    with test_file.open('r') as f:
        yaml_out = f.read()

    assert yaml_out == test_yaml1


def test_save_path(test_doc2: YmmslDocument, test_yaml2: str, tmpdir_path: Path
                   ) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'

    save(test_doc2, test_file)

    with test_file.open('r') as f:
        yaml_out = f.read()

    assert yaml_out == test_yaml2


def test_save_file(test_doc2: YmmslDocument, test_yaml2: str, tmpdir_path: Path
                   ) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'

    with test_file.open('w') as f:
        save(test_doc2, f)

    with test_file.open('r') as f:
        yaml_out = f.read()

    assert yaml_out == test_yaml2
