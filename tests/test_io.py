from collections import OrderedDict
from pathlib import Path
from typing import Any, IO

import pytest

from ymmsl import (ComputeElement, Conduit, dump, Experiment, Identifier,
                   load, save, Simulation, YmmslDocument)


@pytest.fixture
def test_yaml1() -> str:
    text = ('version: v0.1\n'
            'experiment:\n'
            '  model: test_model\n'
            '  parameter_values:\n'
            '    test_str: value\n'
            '    test_int: 13\n'
            '    test_list: [12.3, 1.3]\n'
            )
    return text


@pytest.fixture
def test_doc1() -> YmmslDocument:
    experiment = Experiment('test_model', OrderedDict([
        ('test_str', 'value'),
        ('test_int', 13),
        ('test_list', [12.3, 1.3])]))
    return YmmslDocument('v0.1', experiment)


@pytest.fixture
def test_yaml2() -> str:
    text = ('version: v0.1\n'
            'simulation:\n'
            '  name: test_model\n'
            '  compute_elements:\n'
            '    ic: isr2d.initial_conditions\n'
            '    smc: isr2d.smc\n'
            '    bf: isr2d.blood_flow\n'
            '    smc2bf: isr2d.smc2bf\n'
            '    bf2smc: isr2d.bf2smc\n'
            '  conduits:\n'
            '    ic.out: smc.initial_state\n'
            '    smc.cell_positions: smc2bf.in\n'
            '    smc2bf.out: bf.initial_domain\n'
            '    bf.wss_out: bf2smc.in\n'
            '    bf2smc.out: smc.wss_in\n')
    return text


@pytest.fixture
def test_doc2() -> YmmslDocument:
    simulation = Simulation(
            Identifier('test_model'),
            [
                ComputeElement('ic', 'isr2d.initial_conditions'),
                ComputeElement('smc', 'isr2d.smc'),
                ComputeElement('bf', 'isr2d.blood_flow'),
                ComputeElement('smc2bf', 'isr2d.smc2bf'),
                ComputeElement('bf2smc', 'isr2d.bf2smc')],
            [
                Conduit('ic.out', 'smc.initial_state'),
                Conduit('smc.cell_positions', 'smc2bf.in'),
                Conduit('smc2bf.out', 'bf.initial_domain'),
                Conduit('bf.wss_out', 'bf2smc.in'),
                Conduit('bf2smc.out', 'smc.wss_in')])
    return YmmslDocument('v0.1', None, simulation)


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
    simulation = document.simulation
    assert isinstance(simulation, Simulation)
    assert str(simulation.name) == 'test_model'
    assert len(simulation.compute_elements) == 5
    assert str(simulation.compute_elements[4].name) == 'bf2smc'
    assert str(simulation.compute_elements[2].implementation) == 'isr2d.blood_flow'
    assert len(simulation.conduits) == 5
    assert str(simulation.conduits[0].sender) == 'ic.out'
    assert str(simulation.conduits[1].sending_port()) == 'cell_positions'
    assert str(simulation.conduits[3].receiving_compute_element()) == 'bf2smc'


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
