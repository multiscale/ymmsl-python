from pathlib import Path
from typing import Any, cast

import pytest

from yatiml import RecognitionError
from ymmsl import (
        Configuration, dump, load, save, Model, ModelReference,
        MPICoresResReq, MPINodesResReq, PartialConfiguration, Reference,
        ThreadedResReq, CheckpointRangeRule)


@pytest.fixture
def tmpdir_path(tmpdir: Any) -> Path:
    return Path(str(tmpdir))


def test_load_string1(test_yaml1: str) -> None:
    configuration = load(test_yaml1)
    assert isinstance(configuration, PartialConfiguration)
    assert not isinstance(configuration, Configuration)
    settings = configuration.settings
    assert settings is not None
    assert len(settings) == 4
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
    ic_res = configuration.resources[Reference('ic')]
    assert isinstance(ic_res, ThreadedResReq)
    assert ic_res.threads == 4

    bf2smc_res = configuration.resources[Reference('bf2smc')]
    assert isinstance(bf2smc_res, ThreadedResReq)
    assert bf2smc_res.threads == 1


def test_load_string5(test_yaml5: str) -> None:
    configuration = load(test_yaml5)
    assert isinstance(configuration, Configuration)
    assert len(configuration.model.components) == 5
    assert len(configuration.model.conduits) == 5
    assert len(configuration.implementations) == 5
    assert len(configuration.resources) == 5


def test_load_string6(test_yaml6: str) -> None:
    configuration = load(test_yaml6)
    assert isinstance(configuration, PartialConfiguration)
    res = configuration.resources
    assert len(res) == 6

    singlethreaded = res[Reference('singlethreaded')]
    assert isinstance(singlethreaded, ThreadedResReq)
    assert singlethreaded.threads == 1

    multithreaded = res[Reference('multithreaded')]
    assert isinstance(multithreaded, ThreadedResReq)
    assert multithreaded.threads == 8

    mpi_cores1 = res[Reference('mpi_cores1')]
    assert isinstance(mpi_cores1, MPICoresResReq)
    assert mpi_cores1.mpi_processes == 16

    mpi_cores2 = res[Reference('mpi_cores2')]
    assert isinstance(mpi_cores2, MPICoresResReq)
    assert mpi_cores2.mpi_processes == 4
    assert mpi_cores2.threads_per_mpi_process == 4

    mpi_nodes1 = res[Reference('mpi_nodes1')]
    assert isinstance(mpi_nodes1, MPINodesResReq)
    assert mpi_nodes1.nodes == 10
    assert mpi_nodes1.mpi_processes_per_node == 16
    assert mpi_nodes1.threads_per_mpi_process == 1

    mpi_nodes2 = res[Reference('mpi_nodes2')]
    assert isinstance(mpi_nodes2, MPINodesResReq)
    assert mpi_nodes2.nodes == 10
    assert mpi_nodes2.mpi_processes_per_node == 4
    assert mpi_nodes2.threads_per_mpi_process == 4


def test_load_string7(test_yaml7: str) -> None:
    configuration = load(test_yaml7)
    assert isinstance(configuration, PartialConfiguration)

    assert isinstance(configuration.model, Model)
    components = configuration.model.components
    assert components is not None
    assert components[0].name == 'macro'
    assert components[0].implementation == 'macro_python'
    assert components[0].ports is not None
    assert components[0].ports.f_init == []
    assert components[0].ports.o_i == ['state_out']
    assert components[0].ports.s == ['x_in']
    assert components[0].ports.o_f == []
    assert components[1].ports is not None
    assert components[1].ports.f_init == ['init_in']
    assert components[1].ports.o_i == []
    assert components[1].ports.s == []
    assert components[1].ports.o_f == ['final_output', 'extra_output']


def test_load_string8(test_yaml8: str) -> None:
    configuration = load(test_yaml8)
    assert isinstance(configuration, PartialConfiguration)

    checkpoints = configuration.checkpoints
    assert checkpoints.simulation_time == []
    assert len(checkpoints.wallclock_time) == 1
    rule = checkpoints.wallclock_time[0]
    assert isinstance(rule, CheckpointRangeRule)
    assert cast(CheckpointRangeRule, rule).every == 600

    assert len(configuration.resume) == 2

    assert len(configuration.description.splitlines()) == 3


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


def test_dump6(test_yaml6: str, test_config6: Configuration) -> None:
    text = dump(test_config6)
    assert text == test_yaml6


def test_dump7(test_yaml7: str, test_config7: Configuration) -> None:
    text = dump(test_config7)
    assert text == test_yaml7


def test_dump8(test_yaml8: str, test_config8: Configuration) -> None:
    text = dump(test_config8)
    assert text == test_yaml8


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


def test_resource_requirements() -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  - name: submodel\n')

    with pytest.raises(RecognitionError):
        load(text)
