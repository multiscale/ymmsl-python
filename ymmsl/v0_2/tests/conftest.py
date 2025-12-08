from pathlib import Path

import pytest

from ymmsl.v0_2 import (
        BaseEnv, Component, Configuration, CheckpointRangeRule, CheckpointAtRule,
        Checkpoints, KeepsStateForNextUse, ExecutionModel, Model, MPICoresResReq,
        MPINodesResReq, Ports, Program, Reference, ThreadedResReq)


Ref = Reference


'''
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
'''


@pytest.fixture
def test_config4() -> Configuration:
    description = "Multiline description for\nthis workflow"
    '''
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
    '''
    resources = [
            ThreadedResReq(Reference('ic'), 4),
            ThreadedResReq(Reference('smc'), 4),
            MPICoresResReq(Reference('bf'), 4),
            ThreadedResReq(Reference('smc2bf'), 1),
            ThreadedResReq(Reference('bf2smc'), 1)]
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

    return Configuration(
            description, None, None, None, resources, checkpoints, resume)


@pytest.fixture
def test_config5() -> Configuration:
    config = Configuration('Testing loading of programs')
    config.programs = {
            Reference('macro'): Program(
                'macro', Ports(
                    f_init='init', o_i=['out1', 'out2'], s=['in1', 'in2'],
                    o_f=['final']),
                BaseEnv.LOGIN,
                ['gcc/13.3.0', 'FFTW/3.2.1'],
                Path('/home/user/.venv'),
                {'SETTING': 'something', 'VARIABLE': '42'},
                ExecutionModel.INTELMPI,
                Path('python3'),
                ['/home/user/script.py'],
                None,
                False,
                KeepsStateForNextUse.HELPFUL)}

    return config


@pytest.fixture
def test_config5_text() -> str:
    return (
            'ymmsl_version: v0.2\n'
            'description: Testing loading of programs\n'
            'programs:\n'
            '  macro:\n'
            '    ports:\n'
            '      f_init:\n'
            '      - init\n'
            '      o_i:\n'
            '      - out1\n'
            '      - out2\n'
            '      s:\n'
            '      - in1\n'
            '      - in2\n'
            '      o_f:\n'
            '      - final\n'
            '    base_env: login\n'
            '    modules:\n'
            '    - gcc/13.3.0\n'
            '    - FFTW/3.2.1\n'
            '    virtual_env: /home/user/.venv\n'
            '    env:\n'
            '      SETTING: something\n'
            '      VARIABLE: \'42\'\n'
            '    execution_model: intelmpi\n'
            '    executable: python3\n'
            '    args:\n'
            '    - /home/user/script.py\n'
            '    can_share_resources: false\n'
            '    keeps_state_for_next_use: helpful\n'
            )


@pytest.fixture
def test_config6() -> Configuration:
    model1 = Model(
            'resources_test',
            None,
            [
                Component('singlethreaded', Ports(), 'a'),
                Component('multithreaded', Ports(), 'b'),
                Component('submodel', Ports(), 'resources_test2'),
            ])

    model2 = Model(
            'resources_test2',
            None,
            [
                Component('mpi_cores1', Ports(), 'c'),
                Component('mpi_cores2', Ports(), 'd'),
                Component('mpi_nodes1', Ports(), 'c'),
                Component('mpi_nodes2', Ports(), 'd')],
            [])

    '''
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
    '''

    resources = [
            ThreadedResReq(Reference('singlethreaded'), 1),
            ThreadedResReq(Reference('multithreaded'), 8),
            MPICoresResReq(Reference('submodel.mpi_cores1'), 16),
            MPICoresResReq(Reference('submodel.mpi_cores2'), 4, 4),
            MPINodesResReq(Reference('submodel.mpi_nodes1'), 10, 16),
            MPINodesResReq(Reference('submodel.mpi_nodes2'), 10, 4, 4)]

    return Configuration('config6', [model1, model2], None, None, resources)


@pytest.fixture
def test_config7() -> Configuration:
    model1 = Model('got_resources', None, [Component('singlethreaded', Ports(), 'a')])
    model2 = Model(
            'missing_resources', None, [Component('singlethreaded', Ports(), 'b')])
    resources = [ThreadedResReq(Ref('got_resources.singlethreaded'), 1)]

    return Configuration('test_config7', [model1, model2], None, None, resources)
