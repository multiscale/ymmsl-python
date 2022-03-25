from collections import OrderedDict
from pathlib import Path

import pytest

from ymmsl import (
        Component, Conduit, Configuration, ExecutionModel, Implementation,
        Model, ModelReference, MPICoresResReq, MPINodesResReq,
        PartialConfiguration, Reference, Settings, ThreadedResReq)


@pytest.fixture
def test_yaml1() -> str:
    text = ('ymmsl_version: v0.1\n'
            'settings:\n'
            '  test_str: value\n'
            '  test_int: 13\n'
            '  test_list: [12.3, 1.3]\n'
            )
    return text


@pytest.fixture
def test_config1() -> PartialConfiguration:
    settings = Settings(OrderedDict([
        ('test_str', 'value'),
        ('test_int', 13),
        ('test_list', [12.3, 1.3])]))
    return PartialConfiguration(None, settings)


@pytest.fixture
def test_yaml2() -> str:
    text = ('ymmsl_version: v0.1\n'
            'model:\n'
            '  name: test_model\n'
            '  components:\n'
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
def test_config2() -> PartialConfiguration:
    model = Model(
            'test_model',
            [
                Component('ic', 'isr2d.initial_conditions'),
                Component('smc', 'isr2d.smc'),
                Component('bf', 'isr2d.blood_flow'),
                Component('smc2bf', 'isr2d.smc2bf'),
                Component('bf2smc', 'isr2d.bf2smc')],
            [
                Conduit('ic.out', 'smc.initial_state'),
                Conduit('smc.cell_positions', 'smc2bf.in'),
                Conduit('smc2bf.out', 'bf.initial_domain'),
                Conduit('bf.wss_out', 'bf2smc.in'),
                Conduit('bf2smc.out', 'smc.wss_in')])
    return PartialConfiguration(model)


@pytest.fixture
def test_yaml3() -> str:
    text = ('ymmsl_version: v0.1\n'
            'model:\n'
            '  name: test_model\n')
    return text


@pytest.fixture
def test_config3() -> PartialConfiguration:
    model = ModelReference('test_model')
    return PartialConfiguration(model)


@pytest.fixture
def test_yaml4() -> str:
    text = ('ymmsl_version: v0.1\n'
            'implementations:\n'
            '  isr2d.initial_conditions: isr2d/bin/ic\n'
            '  isr2d.smc: isr2d/bin/smc\n'
            '  isr2d.blood_flow: isr2d/bin/bf\n'
            '  isr2d.smc2bf: isr2d/bin/smc2bf.py\n'
            '  isr2d.bf2smc: isr2d/bin/bf2smc.py\n'
            'resources:\n'
            '  ic:\n'
            '    threads: 4\n'
            '  smc:\n'
            '    threads: 4\n'
            '  bf:\n'
            '    mpi_processes: 4\n'
            '  smc2bf:\n'
            '    threads: 1\n'
            '  bf2smc:\n'
            '    threads: 1\n')
    return text


@pytest.fixture
def test_config4() -> PartialConfiguration:
    implementations = [
            Implementation(
                Reference('isr2d.initial_conditions'), script='isr2d/bin/ic'),
            Implementation(
                Reference('isr2d.smc'), script='isr2d/bin/smc'),
            Implementation(
                Reference('isr2d.blood_flow'), script='isr2d/bin/bf'),
            Implementation(
                Reference('isr2d.smc2bf'), script='isr2d/bin/smc2bf.py'),
            Implementation(
                Reference('isr2d.bf2smc'), script='isr2d/bin/bf2smc.py')]
    resources = [
            ThreadedResReq(Reference('ic'), 4),
            ThreadedResReq(Reference('smc'), 4),
            MPICoresResReq(Reference('bf'), 4),
            ThreadedResReq(Reference('smc2bf'), 1),
            ThreadedResReq(Reference('bf2smc'), 1)]

    return PartialConfiguration(None, None, implementations, resources)


@pytest.fixture
def test_yaml5() -> str:
    text = ('ymmsl_version: v0.1\n'
            'model:\n'
            '  name: test_model\n'
            '  components:\n'
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
            '    bf2smc.out: smc.wss_in\n'
            'implementations:\n'
            '  isr2d.initial_conditions: isr2d/bin/ic\n'
            '  isr2d.smc: isr2d/bin/smc\n'
            '  isr2d.blood_flow: isr2d/bin/bf\n'
            '  isr2d.smc2bf: isr2d/bin/smc2bf.py\n'
            '  isr2d.bf2smc: isr2d/bin/bf2smc.py\n'
            'resources:\n'
            '  ic:\n'
            '    threads: 4\n'
            '  smc:\n'
            '    threads: 4\n'
            '  bf:\n'
            '    mpi_processes: 4\n'
            '  smc2bf:\n'
            '    threads: 1\n'
            '  bf2smc:\n'
            '    threads: 1\n')
    return text


@pytest.fixture
def test_config5() -> Configuration:
    model = Model(
            'test_model',
            [
                Component('ic', 'isr2d.initial_conditions'),
                Component('smc', 'isr2d.smc'),
                Component('bf', 'isr2d.blood_flow'),
                Component('smc2bf', 'isr2d.smc2bf'),
                Component('bf2smc', 'isr2d.bf2smc')],
            [
                Conduit('ic.out', 'smc.initial_state'),
                Conduit('smc.cell_positions', 'smc2bf.in'),
                Conduit('smc2bf.out', 'bf.initial_domain'),
                Conduit('bf.wss_out', 'bf2smc.in'),
                Conduit('bf2smc.out', 'smc.wss_in')])

    implementations = [
            Implementation(
                Reference('isr2d.initial_conditions'), script='isr2d/bin/ic'),
            Implementation(
                Reference('isr2d.smc'), script='isr2d/bin/smc'),
            Implementation(
                Reference('isr2d.blood_flow'), script='isr2d/bin/bf'),
            Implementation(
                Reference('isr2d.smc2bf'), script='isr2d/bin/smc2bf.py'),
            Implementation(
                Reference('isr2d.bf2smc'), script='isr2d/bin/bf2smc.py')]

    resources = [
            ThreadedResReq(Reference('ic'), 4),
            ThreadedResReq(Reference('smc'), 4),
            MPICoresResReq(Reference('bf'), 4),
            ThreadedResReq(Reference('smc2bf'), 1),
            ThreadedResReq(Reference('bf2smc'), 1)]

    return Configuration(model, None, implementations, resources)


@pytest.fixture
def test_yaml6() -> str:
    text = ('ymmsl_version: v0.1\n'
            'model:\n'
            '  name: resources_test\n'
            '  components:\n'
            '    singlethreaded: a\n'
            '    multithreaded: b\n'
            '    mpi_cores1: c\n'
            '    mpi_cores2: d\n'
            '    mpi_nodes1: e\n'
            '    mpi_nodes2: f\n'
            'implementations:\n'
            '  a: /home/user/models/bin/modela\n'
            '  c:\n'
            '    modules:\n'
            '    - gcc-6.3.0\n'
            '    - openmpi-1.10\n'
            '    execution_model: openmpi\n'
            '    executable: /home/user/models/bin/modelc\n'
            '  d:\n'
            '    modules:\n'
            '    - icc-18.0\n'
            '    - IntelMPI-2021-3\n'
            '    execution_model: intelmpi\n'
            '    executable: /home/user/models/bin/modeld\n'
            'resources:\n'
            '  singlethreaded:\n'
            '    threads: 1\n'
            '  multithreaded:\n'
            '    threads: 8\n'
            '  mpi_cores1:\n'
            '    mpi_processes: 16\n'
            '  mpi_cores2:\n'
            '    mpi_processes: 4\n'
            '    threads_per_mpi_process: 4\n'
            '  mpi_nodes1:\n'
            '    nodes: 10\n'
            '    mpi_processes_per_node: 16\n'
            '  mpi_nodes2:\n'
            '    nodes: 10\n'
            '    mpi_processes_per_node: 4\n'
            '    threads_per_mpi_process: 4\n')
    return text


@pytest.fixture
def test_config6() -> Configuration:
    model = Model(
            'resources_test',
            [
                Component('singlethreaded', 'a'),
                Component('multithreaded', 'b'),
                Component('mpi_cores1', 'c'),
                Component('mpi_cores2', 'd'),
                Component('mpi_nodes1', 'e'),
                Component('mpi_nodes2', 'f')],
            [])

    implementations = [
            Implementation(
                Reference('a'), script='/home/user/models/bin/modela'),
            Implementation(
                Reference('c'), ['gcc-6.3.0', 'openmpi-1.10'], None, None,
                ExecutionModel.OPENMPI, Path('/home/user/models/bin/modelc')),
            Implementation(
                Reference('d'), ['icc-18.0', 'IntelMPI-2021-3'], None, None,
                ExecutionModel.INTELMPI, Path('/home/user/models/bin/modeld'))]

    resources = [
            ThreadedResReq(Reference('singlethreaded'), 1),
            ThreadedResReq(Reference('multithreaded'), 8),
            MPICoresResReq(Reference('mpi_cores1'), 16),
            MPICoresResReq(Reference('mpi_cores2'), 4, 4),
            MPINodesResReq(Reference('mpi_nodes1'), 10, 16),
            MPINodesResReq(Reference('mpi_nodes2'), 10, 4, 4)]

    return Configuration(model, None, implementations, resources)
