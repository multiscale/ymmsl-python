from pathlib import Path

import pytest

from ymmsl.v0_2 import (
        BaseEnv, Component, Conduit, Configuration, CheckpointRangeRule,
        CheckpointAtRule, Checkpoints, KeepsStateForNextUse, ExecutionModel, Model,
        MPICoresResReq, MPINodesResReq, Ports, Program, Reference, Settings,
        SupportedSettings, ThreadedResReq)


Ref = Reference


@pytest.fixture
def test_model() -> Model:
    return Model(
            'test_model',
            Ports('in', o_f='out'),
            'Test model for loading/dumping',
            SupportedSettings({'eta': 'float'}),
            [
                Component(
                    'ic', Ports(o_f='out'), 'Creates initial state', False,
                    'initial_conditions'),
                Component(
                    'smc', Ports('initial_state', 'cell_positions', 'wss_in'),
                    'Simulates smooth muscle cells', False, 'smc'),
                Component(
                    'bf', Ports('initial_domain', o_f='wss_out'),
                    'Simulates blood flow', False, 'blood_flow'),
                Component(
                    'smc2bf', Ports('in', o_f='out'), 'Grids domain', False, 'smc2bf'),
                Component(
                    'bf2smc', Ports('in', o_f='out'), 'Interpolates wss', False,
                    'bf2smc')],
            [
                Conduit('ic.out', 'smc.initial_state'),
                Conduit('smc.cell_positions', 'smc2bf.in'),
                Conduit('smc2bf.out', 'bf.initial_domain'),
                Conduit('bf.wss_out', 'bf2smc.in'),
                Conduit('bf2smc.out', 'smc.wss_in')])


@pytest.fixture
def test_model_text() -> str:
    return (
            'name: test_model\n'
            'ports:\n'
            '  f_init: in\n'
            '  o_f: out\n'
            'description: Test model for loading/dumping\n'
            'supported_settings:\n'
            '  eta: float\n'
            'components:\n'
            '  ic:\n'
            '    ports:\n'
            '      o_f: out\n'
            '    description: Creates initial state\n'
            '    implementation: initial_conditions\n'
            '  smc:\n'
            '    ports:\n'
            '      f_init: initial_state\n'
            '      o_i: cell_positions\n'
            '      s: wss_in\n'
            '    description: Simulates smooth muscle cells\n'
            '    implementation: smc\n'
            '  bf:\n'
            '    ports:\n'
            '      f_init: initial_domain\n'
            '      o_f: wss_out\n'
            '    description: Simulates blood flow\n'
            '    implementation: blood_flow\n'
            '  smc2bf:\n'
            '    ports:\n'
            '      f_init: in\n'
            '      o_f: out\n'
            '    description: Grids domain\n'
            '    implementation: smc2bf\n'
            '  bf2smc:\n'
            '    ports:\n'
            '      f_init: in\n'
            '      o_f: out\n'
            '    description: Interpolates wss\n'
            '    implementation: bf2smc\n'
            'conduits:\n'
            '  ic.out: smc.initial_state\n'
            '  smc.cell_positions: smc2bf.in\n'
            '  smc2bf.out: bf.initial_domain\n'
            '  bf.wss_out: bf2smc.in\n'
            '  bf2smc.out: smc.wss_in\n'
            )


@pytest.fixture
def test_model2() -> Model:
    return Model(
            'test_model_conduit_filters',
            Ports(),
            'Test model for loading/dumping conduit filters',
            SupportedSettings(),
            [
                Component(
                    'init', Ports(o_f='macro_out micro_out'), 'Creates initial states',
                    False, 'init'),
                Component(
                    'macro1', Ports('init', 'bc_out', 'bc_in', 'final'),
                    'First macro model', False, 'macro1'),
                Component(
                    'micro1', Ports('init_state init_bc', o_f='final_bc final_state'),
                    'First micro model', False, 'micro1'),
                Component(
                    'macro2', Ports('init_state', 'bc_out', 'bc_in'),
                    'Second macro model', False, 'macro2'),
                Component(
                    'micro2', Ports('init_state init_bc', o_f='final_bc'),
                    'Second micro model', False, 'micro2'),
            ],
            [
                Conduit('init.macro_out', 'macro1.init'),
                Conduit('init.micro_out', 'micro1.init_state', 'pad'),
                Conduit('macro1.bc_out', 'micro1.init_bc'),
                Conduit('micro1.final_bc', 'macro1.bc_in'),
                Conduit('macro1.final', 'macro2.init_state'),
                Conduit('micro1.final_state', 'micro2.init_state', 'last pad'),
                Conduit('macro2.bc_out', 'micro2.init_bc'),
                Conduit('micro2.final_bc', 'macro2.bc_in'),
            ])


@pytest.fixture
def test_model2_text() -> str:
    return (
            'name: test_model_conduit_filters\n'
            'description: Test model for loading/dumping conduit filters\n'
            'components:\n'
            '  init:\n'
            '    ports:\n'
            '      o_f: macro_out micro_out\n'
            '    description: Creates initial states\n'
            '    implementation: init\n'
            '  macro1:\n'
            '    ports:\n'
            '      f_init: init\n'
            '      o_i: bc_out\n'
            '      s: bc_in\n'
            '      o_f: final\n'
            '    description: First macro model\n'
            '    implementation: macro1\n'
            '  micro1:\n'
            '    ports:\n'
            '      f_init: init_state init_bc\n'
            '      o_f: final_bc final_state\n'
            '    description: First micro model\n'
            '    implementation: micro1\n'
            '  macro2:\n'
            '    ports:\n'
            '      f_init: init_state\n'
            '      o_i: bc_out\n'
            '      s: bc_in\n'
            '    description: Second macro model\n'
            '    implementation: macro2\n'
            '  micro2:\n'
            '    ports:\n'
            '      f_init: init_state init_bc\n'
            '      o_f: final_bc\n'
            '    description: Second micro model\n'
            '    implementation: micro2\n'
            'conduits:\n'
            '  init.macro_out: macro1.init\n'
            '  init.micro_out: pad micro1.init_state\n'
            '  macro1.bc_out: micro1.init_bc\n'
            '  micro1.final_bc: macro1.bc_in\n'
            '  macro1.final: macro2.init_state\n'
            '  micro1.final_state: last pad micro2.init_state\n'
            '  macro2.bc_out: micro2.init_bc\n'
            '  micro2.final_bc: macro2.bc_in\n'
            )


@pytest.fixture
def test_config3() -> Configuration:
    model1 = Model(
            'supported_settings_test',
            None,
            'description',
            None,
            [
                Component('c1', Ports(), 'description', False, 'a'),
                Component(
                    'submodel', Ports(), 'description', False,
                    'supported_settings_test2'),
            ])

    model2 = Model(
            'supported_settings_test2',
            None,
            'description',
            SupportedSettings({'delta': 'bool'}),
            [
                Component('c1', Ports(), 'description', False, 'b'),
                Component('c2', Ports(), 'description', False, 'c', 10)],
            [])

    settings = Settings({
        'alpha': 3.2,
        'beta': 10,
        'gamma': 'text',
        'delta': 'text',
        'submodel.delta': False,
        'epsilon': [10, 11]})

    program_a = Program(
            'a', Ports(), 'a', SupportedSettings({'alpha': 'float', 'beta': 'int'}),
            execution_model=ExecutionModel.DIRECT, executable=Path('a'))

    program_b = Program(
            'b', Ports(), 'b', SupportedSettings({'gamma': 'str'}),
            execution_model=ExecutionModel.INTELMPI, executable=Path('b'))

    program_c = Program(
            'c', Ports(), 'c', SupportedSettings({'delta': 'bool'}),
            execution_model=ExecutionModel.OPENMPI, executable=Path('c'))

    programs = [program_a, program_b, program_c]

    resources = [
            ThreadedResReq(Reference('c1'), 1),
            MPICoresResReq(Reference('submodel.c1'), 16),
            MPICoresResReq(Reference('submodel.c2'), 4, 4)]

    return Configuration(
            'config3', None, [model1, model2], None, settings, programs, resources)


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
            description, None, None, None, None, None, resources, checkpoints, resume)


@pytest.fixture
def test_config5() -> Configuration:
    config = Configuration('Testing loading of programs')
    config.programs = {
            Reference('macro'): Program(
                'macro', Ports(
                    f_init='init', o_i=['out1', 'out2'], s=['in1', 'in2'],
                    o_f=['final']),
                'description',
                SupportedSettings({'alpha': 'float'}),
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
            '      f_init: init\n'
            '      o_i: out1 out2\n'
            '      s: in1 in2\n'
            '      o_f: final\n'
            '    description: description\n'
            '    supported_settings:\n'
            '      alpha: float\n'
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
            None,
            [
                Component('singlethreaded', Ports(), 'description', False, 'a'),
                Component('multithreaded', Ports(), 'description', False, 'b'),
                Component('submodel', Ports(), 'description', False, 'resources_test2'),
            ])

    model2 = Model(
            'resources_test2',
            None,
            'description',
            None,
            [
                Component('mpi_cores1', Ports(), 'description', False, 'c'),
                Component('mpi_cores2', Ports(), 'description', False, 'd'),
                Component('mpi_nodes1', Ports(), 'description', False, 'c'),
                Component('mpi_nodes2', Ports(), 'description', False, 'd')],
            [])

    em = {
            'a': ExecutionModel.DIRECT,
            'b': ExecutionModel.DIRECT,
            'c': ExecutionModel.OPENMPI,
            'd': ExecutionModel.OPENMPI}
    programs = [Program(x, script='script', execution_model=em[x]) for x in 'abcd']

    resources = [
            ThreadedResReq(Reference('singlethreaded'), 1),
            ThreadedResReq(Reference('multithreaded'), 8),
            MPICoresResReq(Reference('submodel.mpi_cores1'), 16),
            MPICoresResReq(Reference('submodel.mpi_cores2'), 4, 4),
            MPINodesResReq(Reference('submodel.mpi_nodes1'), 10, 16),
            MPINodesResReq(Reference('submodel.mpi_nodes2'), 10, 4, 4)]

    return Configuration(
            'config6', None, [model1, model2], None, None, programs, resources)


@pytest.fixture
def test_config7() -> Configuration:
    model1 = Model(
            'got_resources', None, 'description', None,
            [
                Component('singlethreaded', Ports(), 'description', False, 'a'),
                Component('with_mpi', Ports(), 'description', False, 'b'),
                Component('without_mpi', Ports(), 'description', False, 'a'),
            ])

    model2 = Model(
            'missing_resources', None, 'description', None,
            [Component('singlethreaded2', Ports(), 'description', False, 'a')])

    programs = [
            Program('a', script='a', execution_model=ExecutionModel.DIRECT),
            Program('b', script='b', execution_model=ExecutionModel.INTELMPI)]

    resources = [
            ThreadedResReq(Ref('singlethreaded'), 1),
            ThreadedResReq(Ref('with_mpi'), 2),
            MPICoresResReq(Ref('without_mpi'), 10)]

    return Configuration(
            'test_config7', None, [model1, model2], None, None, programs, resources)


@pytest.fixture
def test_config8() -> Configuration:
    model1 = Model(
            'implementations_test',
            None, 'description', None,
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
            None, 'description', None,
            [
                Component(
                    'impl_with_ports', Ports(f_init=['in'], o_f=['out']), 'description',
                    False, 'with_ports'),
            ])

    programs = [
            Program(
                'no_ports', None, 'description', None,
                script='/home/user/models/bin/modela'),
            Program(
                'with_ports', Ports(f_init=['in'], o_f=['out']),
                base_env=BaseEnv.LOGIN,
                modules=['gcc-6.3.0', 'openmpi-1.10'],
                execution_model=ExecutionModel.OPENMPI,
                executable=Path('/home/user/models/bin/modelc')),
            ]

    resources = [
            ThreadedResReq(Reference('impl_no_ports'), 1),
            MPICoresResReq(Reference('impl_with_ports'), 4, 4),
            ]

    return Configuration(
            'config8', None, [model1, model2], None, None, programs, resources)


@pytest.fixture
def test_config9() -> Configuration:
    model1 = Model(
            'implementations_test_broken',
            None, 'description', None,
            [
                Component(
                    'no_implementation', Ports(o_i=['out'], s=['in']), 'description',
                    False, None),
                Component(
                    'missing_implementation', Ports(), 'description', False,
                    'implementation_does_not_exist'),
                Component(
                    'impl_ports_mismatch', Ports(f_init=['in'], o_f=['out']),
                    'description', False, 'ports1'),
                Component(
                    'model_as_impl', Ports(f_init=['inm'], o_f=['outm', 'out']),
                    'description', False, 'implementations_test2'),
            ])

    model2 = Model(
            'implementations_test2',
            Ports(f_init=['inm1'], o_i=['outm'], o_f=['out']),
            'description', None,
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
            ThreadedResReq(Reference('missing_implementation'), 1),
            ThreadedResReq(Reference('impl_ports_mismatch'), 1),
            MPICoresResReq(Reference('model_as_impl.impl_also_wrong'), 4, 4),
            ThreadedResReq(Reference('model_as_impl.impl_extra_ports'), 1),
            ]

    return Configuration(
            'config9', None, [model1, model2], None, None, programs, resources)


@pytest.fixture
def test_config10() -> Configuration:
    return Configuration(
            'testing io of custom implementations', None, None, {
                Reference('c1'): Reference('program1'),
                Reference('c2.init_model'): Reference('initer2')})


@pytest.fixture
def test_config10_text() -> str:
    return (
            'ymmsl_version: v0.2\n'
            'description: testing io of custom implementations\n'
            'custom_implementations:\n'
            '  c1: program1\n'
            '  c2.init_model: initer2\n'
            )


@pytest.fixture
def test_config11() -> Configuration:
    model1 = Model(
            'test_model', None, 'description', None,
            [
                Component('c1', Ports(), 'description', False, None),
                Component('c2', Ports(), 'description', False, 'submodel')])

    model2 = Model(
            'submodel', None, 'description', None,
            [Component('init_model', Ports(), 'description', False, 'initer1')])

    programs = [
            Program('program1', executable=Path('program1')),
            Program('initer2', executable=Path('initer2'))]

    resources = [
            ThreadedResReq(Reference('c1'), 1),
            ThreadedResReq(Reference('c2.init_model'), 1),
            ]

    return Configuration(
            'testing consistency of custom implementations', None, [model1, model2], {
                Reference('c1'): Reference('program1'),
                Reference('c2.init_model'): Reference('initer2')},
            None, programs, resources)


@pytest.fixture
def test_config12() -> Configuration:
    model1 = Model(
            'test_model', None, 'description', None,
            [
                Component('c1', Ports(), 'description', False, None),
                Component('c2', Ports(), 'description', False, 'submodel')])

    model2 = Model(
            'submodel', None, 'description', None,
            [Component('init_model', Ports(), 'description', False, 'initer1')])

    resources = [
            ThreadedResReq(Reference('c1'), 1),
            ThreadedResReq(Reference('c2.init_model'), 1),
            ]

    return Configuration(
            'testing consistency of custom implementations', None, [model1, model2], {
                Reference('cl'): Reference('program1'),
                Reference('c2.init_model'): Reference('initer2')},
            None, None, resources)


@pytest.fixture
def test_config13() -> Configuration:
    model1 = Model('impl1', None, 'description')
    model2 = Model('impl2', None, 'description')
    program1 = Program('impl2', script='impl2')
    program2 = Program('impl3', script='impl3')

    return Configuration(
            'testing duplicate implementation names', None,
            [model1, model2], None, None, [program1, program2])
