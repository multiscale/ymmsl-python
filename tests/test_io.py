from pathlib import Path
from typing import Any

import pytest

from ymmsl import (
        Configuration, dump, load, save, Model, ModelReference,
        PartialConfiguration, Reference)


@pytest.fixture
def tmpdir_path(tmpdir: Any) -> Path:
    return Path(str(tmpdir))


def test_load_string1(test_yaml1: str) -> None:
    configuration = load(test_yaml1)
    assert isinstance(configuration, PartialConfiguration)
    assert not isinstance(configuration, Configuration)
    settings = configuration.settings
    assert settings is not None
    assert len(settings) == 3
    assert isinstance(settings['test_list'], list)
    assert settings['test_list'][1] == 1.3

    configuration = load(test_yaml1)
    assert configuration.settings is not None
    assert configuration.settings['test_str'] == 'value'
    assert configuration.settings['test_int'] == 13
    assert configuration.settings['test_list'] == [12.3, 1.3]


def test_load_string2(test_yaml2: str) -> None:
    configuration = load(test_yaml2)
    assert isinstance(configuration, PartialConfiguration)
    assert not isinstance(configuration, Configuration)
    model = configuration.model
    assert isinstance(model, Model)
    assert str(model.name) == 'test_model'
    assert len(model.components) == 5
    assert str(model.components[4].name) == 'bf2smc'
    assert str(model.components[2].implementation) == 'isr2d.blood_flow'
    assert len(model.conduits) == 5
    assert str(model.conduits[0].sender) == 'ic.out'
    assert str(model.conduits[1].sending_port()) == 'cell_positions'
    assert str(model.conduits[3].receiving_component()) == 'bf2smc'


def test_load_string3(test_yaml3: str) -> None:
    configuration = load(test_yaml3)
    assert isinstance(configuration, PartialConfiguration)
    assert not isinstance(configuration, Configuration)
    assert isinstance(configuration.model, ModelReference)
    assert str(configuration.model.name) == 'test_model'


def test_load_string4(test_yaml4: str) -> None:
    configuration = load(test_yaml4)
    assert isinstance(configuration, PartialConfiguration)
    assert not isinstance(configuration, Configuration)
    assert len(configuration.implementations) == 5
    impls = configuration.implementations
    ic = Reference('isr2d.initial_conditions')
    bf2smc = Reference('isr2d.bf2smc')
    assert impls[ic].name == 'isr2d.initial_conditions'
    assert impls[bf2smc].script == 'isr2d/bin/bf2smc.py'

    assert len(configuration.resources) == 5
    assert configuration.resources[ic].num_cores == 4
    assert configuration.resources[bf2smc].num_cores == 1


def test_load_string5(test_yaml5: str) -> None:
    configuration = load(test_yaml5)
    assert isinstance(configuration, Configuration)
    assert len(configuration.model.components) == 5
    assert len(configuration.model.conduits) == 5
    assert len(configuration.implementations) == 5
    assert len(configuration.resources) == 5


def test_load_file(test_yaml1: str, tmpdir_path: Path) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'
    with test_file.open('w') as f:
        f.write(test_yaml1)

    with test_file.open('r') as f:
        configuration = load(f)

    assert configuration.settings is not None


def test_load_path(test_yaml1: str, tmpdir_path: Path) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'
    with test_file.open('w') as f:
        f.write(test_yaml1)

    configuration = load(test_file)
    assert configuration.settings is not None


def test_dump1(test_yaml1: str, test_config1: PartialConfiguration) -> None:
    text = dump(test_config1)
    assert text == test_yaml1


def test_dump2(test_yaml2: str, test_config2: PartialConfiguration) -> None:
    text = dump(test_config2)
    assert text == test_yaml2


def test_dump3(test_yaml3: str, test_config3: PartialConfiguration) -> None:
    text = dump(test_config3)
    assert text == test_yaml3


def test_dump4(test_yaml4: str, test_config4: PartialConfiguration) -> None:
    text = dump(test_config4)
    assert text == test_yaml4


def test_dump5(test_yaml5: str, test_config5: Configuration) -> None:
    text = dump(test_config5)
    assert text == test_yaml5


def test_save_str(test_config1: PartialConfiguration, test_yaml1: str,
                  tmpdir_path: Path) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'

    save(test_config1, str(test_file))

    with test_file.open('r') as f:
        yaml_out = f.read()

    assert yaml_out == test_yaml1


def test_save_path(test_config2: PartialConfiguration, test_yaml2: str,
                   tmpdir_path: Path) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'

    save(test_config2, test_file)

    with test_file.open('r') as f:
        yaml_out = f.read()

    assert yaml_out == test_yaml2


def test_save_file(test_config2: PartialConfiguration, test_yaml2: str,
                   tmpdir_path: Path) -> None:
    test_file = tmpdir_path / 'test_yaml1.ymmsl'

    with test_file.open('w') as f:
        save(test_config2, f)

    with test_file.open('r') as f:
        yaml_out = f.read()

    assert yaml_out == test_yaml2
