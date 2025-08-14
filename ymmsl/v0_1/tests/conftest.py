from pathlib import Path

import pytest

from ymmsl.v0_1 import (
        BaseEnv, Component, Conduit, Configuration, ExecutionModel, Implementation,
        CheckpointRangeRule, CheckpointAtRule, Checkpoints,
        Model, MPICoresResReq, MPINodesResReq,
        PartialConfiguration, Reference, ThreadedResReq)


Ref = Reference


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
    description = "Multiline description for\nthis workflow"
    checkpoints = Checkpoints(
            True,
            [CheckpointRangeRule(every=100),
             CheckpointAtRule([10, 20, 50])],
            [CheckpointRangeRule(start=0, stop=10, every=2),
             CheckpointRangeRule(start=10, every=5)])
    resume = {Ref('ic'): Path('/path/to/snapshots/ic.pack'),
              Ref('smc'): Path('/path/to/snapshots/smc.pack'),
              Ref('bf'): Path('/path/to/snapshots/bf.pack'),
              Ref('smc2bf'): Path('/path/to/snapshots/smc2bf.pack'),
              Ref('bf2smc'): Path('/path/to/snapshots/bf2smc.pack')}

    return PartialConfiguration(None, None, implementations, resources,
                                description, checkpoints, resume)


@pytest.fixture
def test_config6() -> Configuration:
    model = Model(
            'resources_test',
            [
                Component('singlethreaded', 'a'),
                Component('multithreaded', 'b'),
                Component('mpi_cores1', 'c'),
                Component('mpi_cores2', 'd'),
                Component('mpi_nodes1', 'c'),
                Component('mpi_nodes2', 'd')],
            [])

    implementations = [
            Implementation(
                Reference('a'), script='/home/user/models/bin/modela'),
            Implementation(
                Reference('b'), script='/home/user/models/bin/modelb'),
            Implementation(
                Reference('c'),
                base_env=BaseEnv.LOGIN,
                modules=['gcc-6.3.0', 'openmpi-1.10'],
                execution_model=ExecutionModel.OPENMPI,
                executable=Path('/home/user/models/bin/modelc')),
            Implementation(
                Reference('d'),
                base_env=BaseEnv.CLEAN,
                modules=['icc-18.0', 'IntelMPI-2021-3'],
                execution_model=ExecutionModel.INTELMPI,
                executable=Path('/home/user/models/bin/modeld'))]

    resources = [
            ThreadedResReq(Reference('singlethreaded'), 1),
            ThreadedResReq(Reference('multithreaded'), 8),
            MPICoresResReq(Reference('mpi_cores1'), 16),
            MPICoresResReq(Reference('mpi_cores2'), 4, 4),
            MPINodesResReq(Reference('mpi_nodes1'), 10, 16),
            MPINodesResReq(Reference('mpi_nodes2'), 10, 4, 4)]

    return Configuration(model, None, implementations, resources)
