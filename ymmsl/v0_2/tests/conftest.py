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
            description, None, None, None, None, resources, checkpoints, resume)


@pytest.fixture
def test_config5() -> Configuration:
    config = Configuration('Testing loading of programs')
    config.programs = {
            Reference('macro'): Program(
                'macro', Ports(
                    f_init='init', o_i=['out1', 'out2'], s=['in1', 'in2'],
                    o_f=['final']),
                'description',
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
            '    description: description\n'
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
            'description',
            [
                Component('singlethreaded', Ports(), 'description', False, 'a'),
                Component('multithreaded', Ports(), 'description', False, 'b'),
                Component('submodel', Ports(), 'description', False, 'resources_test2'),
            ])

    model2 = Model(
            'resources_test2',
            None,
            'description',
            [
                Component('mpi_cores1', Ports(), 'description', False, 'c'),
                Component('mpi_cores2', Ports(), 'description', False, 'd'),
                Component('mpi_nodes1', Ports(), 'description', False, 'c'),
                Component('mpi_nodes2', Ports(), 'description', False, 'd')],
            [])

    resources = [
            ThreadedResReq(Reference('singlethreaded'), 1),
            ThreadedResReq(Reference('multithreaded'), 8),
            MPICoresResReq(Reference('submodel.mpi_cores1'), 16),
            MPICoresResReq(Reference('submodel.mpi_cores2'), 4, 4),
            MPINodesResReq(Reference('submodel.mpi_nodes1'), 10, 16),
            MPINodesResReq(Reference('submodel.mpi_nodes2'), 10, 4, 4)]

    return Configuration('config6', None, [model1, model2], None, None, resources)


@pytest.fixture
def test_config7() -> Configuration:
    model1 = Model(
            'got_resources', None, 'description',
            [Component('singlethreaded', Ports(), 'description', False, 'a')])
    model2 = Model(
            'missing_resources', None, 'description',
            [Component('singlethreaded', Ports(), 'description', False, 'b')])
    resources = [ThreadedResReq(Ref('got_resources.singlethreaded'), 1)]

    return Configuration('test_config7', None, [model1, model2], None, None, resources)


@pytest.fixture
def test_config8() -> Configuration:
    model1 = Model(
            'implementations_test',
            None, 'description',
            [
                Component(
                    'no_implementation', Ports(o_i=['out'], s=['in']), 'description',
                    False, None),
                Component(
                    'impl_no_ports', Ports(f_init=['in'], o_f=['out']), 'description',
                    False, 'no_ports'),
            ])

    model2 = Model(
            'implementations_test2',
            None, 'description',
            [
                Component(
                    'impl_with_ports', Ports(f_init=['in'], o_f=['out']), 'description',
                    False, 'with_ports'),
            ])

    programs = [
            Program(
                'no_ports', None, 'description',
                script='/home/user/models/bin/modela'),
            Program(
                'with_ports',
                base_env=BaseEnv.LOGIN,
                modules=['gcc-6.3.0', 'openmpi-1.10'],
                execution_model=ExecutionModel.OPENMPI,
                executable=Path('/home/user/models/bin/modelc')),
            ]

    resources = [
            ThreadedResReq(Reference('impl_no_ports'), 1),
            MPICoresResReq(Reference('impl_with_ports'), 4, 4),
            ]

    return Configuration('config8', None, [model1, model2], None, programs, resources)


@pytest.fixture
def test_config9() -> Configuration:
    model1 = Model(
            'implementations_test_broken',
            None, 'description',
            [
                Component(
                    'no_implementation', Ports(o_i=['out'], s=['in']), 'description',
                    False, None),
                Component(
                    'impl_ports_mismatch', Ports(f_init=['in'], o_f=['out']),
                    'description', False, 'ports1'),
            ])

    model2 = Model(
            'implementations_test2',
            None, 'description',
            [
                Component(
                    'impl_also_wrong', Ports(o_i=['out'], s=['in']), 'description',
                    False, 'ports2'),
                Component(
                    'impl_extra_ports', Ports(f_init=['in']), 'description', False,
                    'ports3'),
            ])

    programs = [
            Program(
                'ports1', Ports(s=['test']),
                script='/home/user/models/bin/modela'),
            Program(
                'ports2', Ports(f_init=['in'], o_f=['out'], s=['wrong']),
                base_env=BaseEnv.LOGIN,
                modules=['gcc-6.3.0', 'openmpi-1.10'],
                execution_model=ExecutionModel.OPENMPI,
                executable=Path('/home/user/models/bin/modelb')),
            Program(
                'ports3', Ports(f_init=['in'], s=['test']),
                script='/home/user/models/bin/modelc'),
             ]

    resources = [
            ThreadedResReq(Reference('impl_ports_mismatch'), 1),
            MPICoresResReq(Reference('impl_also_wrong'), 4, 4),
            ThreadedResReq(Reference('impl_extra_ports'), 1),
            ]

    return Configuration('config9', None, [model1, model2], None, programs, resources)
