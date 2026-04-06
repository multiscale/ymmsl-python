from pathlib import Path

import pytest

from ymmsl.v0_2 import (
        BaseEnv, Component, Conduit, Configuration, CheckpointRangeRule,
        CheckpointAtRule, Checkpoints, KeepsStateForNextUse, ExecutionModel, Model,
        MPICoresResReq, MPINodesResReq, Ports, Program, Reference, Settings,
        SupportedSettings, ThreadedResReq)


Ref = Reference


@pytest.fixture
def model() -> Model:
    return Model(
            'test_model',
            Ports('in', o_f='out'),
            'Test model for loading/dumping',
            SupportedSettings({'eta': 'float'}),
            [
                Component(
                    'ic', Ports(o_f='out'), 'Creates initial state',
                    'initial_conditions'),
                Component(
                    'smc', Ports('initial_state', 'cell_positions', 'wss_in'),
                    'Simulates smooth muscle cells', 'smc'),
                Component(
                    'bf', Ports('initial_domain', o_f='wss_out'),
                    'Simulates blood flow', 'blood_flow'),
                Component(
                    'smc2bf', Ports('in', o_f='out'), 'Grids domain', 'smc2bf'),
                Component(
                    'bf2smc', Ports('in', o_f='out'), 'Interpolates wss', 'bf2smc')],
            [
                Conduit('ic.out', 'smc.initial_state'),
                Conduit('smc.cell_positions', 'smc2bf.in'),
                Conduit('smc2bf.out', 'bf.initial_domain'),
                Conduit('bf.wss_out', 'bf2smc.in'),
                Conduit('bf2smc.out', 'smc.wss_in')])


@pytest.fixture
def model_text() -> str:
    return (
            'name: test_model\n'
            'ports:\n'
            '  f_init: in\n'
            '  o_f: out\n'
            'description: |\n'
            '  Test model for loading/dumping\n'
            'supported_settings:\n'
            '  eta: float\n'
            'components:\n'
            '  ic:\n'
            '    ports:\n'
            '      o_f: out\n'
            '    description: |\n'
            '      Creates initial state\n'
            '    implementation: initial_conditions\n'
            '  smc:\n'
            '    ports:\n'
            '      f_init: initial_state\n'
            '      o_i: cell_positions\n'
            '      s: wss_in\n'
            '    description: |\n'
            '      Simulates smooth muscle cells\n'
            '    implementation: smc\n'
            '  bf:\n'
            '    ports:\n'
            '      f_init: initial_domain\n'
            '      o_f: wss_out\n'
            '    description: |\n'
            '      Simulates blood flow\n'
            '    implementation: blood_flow\n'
            '  smc2bf:\n'
            '    ports:\n'
            '      f_init: in\n'
            '      o_f: out\n'
            '    description: |\n'
            '      Grids domain\n'
            '    implementation: smc2bf\n'
            '  bf2smc:\n'
            '    ports:\n'
            '      f_init: in\n'
            '      o_f: out\n'
            '    description: |\n'
            '      Interpolates wss\n'
            '    implementation: bf2smc\n'
            'conduits:\n'
            '  ic.out: smc.initial_state\n'
            '  smc.cell_positions: smc2bf.in\n'
            '  smc2bf.out: bf.initial_domain\n'
            '  bf.wss_out: bf2smc.in\n'
            '  bf2smc.out: smc.wss_in\n'
            )


@pytest.fixture
def model_multicast() -> Model:
    return Model(
            'test_model', None, 'Test model for multicast conduits', None,
            [
                Component('a', Ports(o_f='out'), 'Creates data', 'a'),
                Component('b', Ports('in'), 'Receives data', 'b'),
                Component('c', Ports('in'), 'Receives data', 'b'),
                ],
            [
                Conduit('a.out', 'b.in'),
                Conduit('a.out', 'c.in'),
                ]
            )


@pytest.fixture
def model_multicast_text() -> str:
    return (
            'name: test_model\n'
            'description: |\n'
            '  Test model for multicast conduits\n'
            'components:\n'
            '  a:\n'
            '    ports:\n'
            '      o_f: out\n'
            '    description: |\n'
            '      Creates data\n'
            '    implementation: a\n'
            '  b:\n'
            '    ports:\n'
            '      f_init: in\n'
            '    description: |\n'
            '      Receives data\n'
            '    implementation: b\n'
            '  c:\n'
            '    ports:\n'
            '      f_init: in\n'
            '    description: |\n'
            '      Receives data\n'
            '    implementation: b\n'
            'conduits:\n'
            '  a.out:\n'
            '  - b.in\n'
            '  - c.in\n'
            )


@pytest.fixture
def model_with_filters() -> Model:
    return Model(
            'test_model_conduit_filters',
            Ports(),
            'Test model for loading/dumping conduit filters',
            SupportedSettings(),
            [
                Component(
                    'init', Ports(o_f='macro_out micro_out'), 'Creates initial states',
                    'init'),
                Component(
                    'macro1', Ports('init', 'bc_out', 'bc_in', 'final'),
                    'First macro model', 'macro1'),
                Component(
                    'micro1', Ports('init_state init_bc', o_f='final_bc final_state'),
                    'First micro model', 'micro1'),
                Component(
                    'macro2', Ports('init_state', 'bc_out', 'bc_in'),
                    'Second macro model', 'macro2'),
                Component(
                    'micro2', Ports('init_state init_bc', o_f='final_bc'),
                    'Second micro model', 'micro2'),
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
def model_with_filters_text() -> str:
    return (
            'name: test_model_conduit_filters\n'
            'description: |\n'
            '  Test model for loading/dumping conduit filters\n'
            'components:\n'
            '  init:\n'
            '    ports:\n'
            '      o_f: macro_out micro_out\n'
            '    description: |\n'
            '      Creates initial states\n'
            '    implementation: init\n'
            '  macro1:\n'
            '    ports:\n'
            '      f_init: init\n'
            '      o_i: bc_out\n'
            '      s: bc_in\n'
            '      o_f: final\n'
            '    description: |\n'
            '      First macro model\n'
            '    implementation: macro1\n'
            '  micro1:\n'
            '    ports:\n'
            '      f_init: init_state init_bc\n'
            '      o_f: final_bc final_state\n'
            '    description: |\n'
            '      First micro model\n'
            '    implementation: micro1\n'
            '  macro2:\n'
            '    ports:\n'
            '      f_init: init_state\n'
            '      o_i: bc_out\n'
            '      s: bc_in\n'
            '    description: |\n'
            '      Second macro model\n'
            '    implementation: macro2\n'
            '  micro2:\n'
            '    ports:\n'
            '      f_init: init_state init_bc\n'
            '      o_f: final_bc\n'
            '    description: |\n'
            '      Second micro model\n'
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
def test_program() -> Program:
    return Program(
            'macro', Ports(['init'], ['out1', 'out2'], ['in1', 'in2'], ['final']),
            'description', SupportedSettings({'alpha': 'float'}), BaseEnv.LOGIN,
            ['gcc/13.3.0', 'FFTW/3.2.1'], Path('/home/user/.venv'),
            {'SETTING': 'something', 'VARIABLE': '42'}, ExecutionModel.INTELMPI,
            Path('python3'), ['/home/user/script.py'], None, False,
            KeepsStateForNextUse.HELPFUL)


@pytest.fixture
def test_program_text() -> str:
    return (
            'name: macro\n'
            'ports:\n'
            '  f_init: init\n'
            '  o_i: out1 out2\n'
            '  s: in1 in2\n'
            '  o_f: final\n'
            'description: |\n'
            '  description\n'
            'supported_settings:\n'
            '  alpha: float\n'
            'base_env: login\n'
            'modules:\n'
            '- gcc/13.3.0\n'
            '- FFTW/3.2.1\n'
            'virtual_env: /home/user/.venv\n'
            'env:\n'
            '  SETTING: something\n'
            '  VARIABLE: \'42\'\n'
            'execution_model: intelmpi\n'
            'executable: python3\n'
            'args:\n'
            '- /home/user/script.py\n'
            'can_share_resources: false\n'
            'keeps_state_for_next_use: helpful\n'
            )


@pytest.fixture
def config_custom_implementations() -> Configuration:
    return Configuration(
            'testing io of custom implementations', None, None, {
                Reference('c1'): Reference('program1'),
                Reference('c2.init_model'): Reference('initer2')})


@pytest.fixture
def config_custom_implementations_text() -> str:
    return (
            'ymmsl_version: v0.2\n'
            'description: |\n'
            '  testing io of custom implementations\n'
            'custom_implementations:\n'
            '  c1: program1\n'
            '  c2.init_model: initer2\n'
            )


@pytest.fixture
def config_update_checkpoint() -> Configuration:
    description = "Multiline description for\nthis workflow"
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
def config_duplicate_implementations() -> Configuration:
    model1 = Model('impl1', None, 'description')
    model2 = Model('impl2', None, 'description')
    program1 = Program('impl2', script='impl2')
    program2 = Program('impl3', script='impl3')

    return Configuration(
            'testing duplicate implementation names', None,
            [model1, model2], None, None, [program1, program2])


@pytest.fixture
def config_consistent_impl_ports() -> Configuration:
    model1 = Model(
            'implementations_test',
            None, 'description', None,
            [
                Component(
                    'no_implementation', Ports(o_i=['out'], s=['in']), 'description',
                    None),
                Component(
                    'impl_no_ports', Ports(f_init=['in'], o_f=['out']), 'description',
                    'no_ports'),
            ])

    model2 = Model(
            'implementations_test2',
            None, 'description', None,
            [
                Component(
                    'impl_with_ports', Ports(f_init=['in'], o_f=['out']), 'description',
                    'with_ports'),
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
            'impl_ports', None, [model1, model2], None, None, programs, resources)


@pytest.fixture
def config_inconsistent_impl_ports() -> Configuration:
    model1 = Model(
            'implementations_test_broken',
            None, 'description', None,
            [
                Component(
                    'no_implementation', Ports(o_i=['out'], s=['in']), 'description',
                    None),
                Component(
                    'missing_implementation', Ports(), 'description',
                    'implementation_does_not_exist'),
                Component(
                    'impl_ports_mismatch', Ports(f_init=['in'], o_f=['out']),
                    'description', 'ports1'),
                Component(
                    'model_as_impl', Ports(f_init=['inm'], o_f=['outm', 'out']),
                    'description', 'implementations_test2'),
            ])

    model2 = Model(
            'implementations_test2',
            Ports(f_init=['inm1'], o_i=['outm'], o_f=['out']),
            'description', None,
            [
                Component(
                    'impl_also_wrong', Ports(o_i=['out'], s=['in']), 'description',
                    'ports2'),
                Component(
                    'impl_extra_ports', Ports(f_init=['in']), 'description', 'ports3'),
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
            'impl_ports', None, [model1, model2], None, None, programs, resources)


@pytest.fixture
def config_consistent_custom_impls() -> Configuration:
    model1 = Model(
            'test_model', None, 'Testing consistent (custom) implementations', None,
            [
                Component('c1', Ports(), 'description', None),
                Component('c2', Ports(), 'description', 'submodel')])

    model2 = Model(
            'submodel', None, 'description', None,
            [
                Component('init_model', Ports(), 'description', 'initer1'),
                Component('optional', Ports(), 'description', None, True),
                Component('optional2', Ports(), 'description', 'program1', True)])

    programs = [
            Program('program1', executable=Path('program1')),
            Program('initer2', executable=Path('initer2'))]

    resources = [
            ThreadedResReq(Reference('c1'), 1),
            ThreadedResReq(Reference('c2.init_model'), 1),
            ThreadedResReq(Reference('c2.optional2'), 1),
            ]

    return Configuration(
            'testing consistency of custom implementations', None, [model1, model2], {
                Reference('c1'): Reference('program1'),
                Reference('c2.init_model'): Reference('initer2')},
            None, programs, resources)


@pytest.fixture
def config_inconsistent_custom_impls() -> Configuration:
    model1 = Model(
            'test_model', None, 'description', None,
            [
                Component('c1', Ports(), 'description', None),
                Component('c2', Ports(), 'description', 'submodel')])

    model2 = Model(
            'submodel', None, 'description', None,
            [Component('init_model', Ports(), 'description', 'initer1')])

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
def config_consistent_settings() -> Configuration:
    model1 = Model(
            'supported_settings_test',
            None,
            'description',
            None,
            [
                Component('c1', Ports(), 'description', 'a'),
                Component(
                    'submodel', Ports(), 'description', 'supported_settings_test2'),
            ])

    model2 = Model(
            'supported_settings_test2',
            None,
            'description',
            SupportedSettings({'delta': 'bool'}),
            [
                Component('c1', Ports(), 'description', 'b'),
                Component('c2', Ports(), 'description', 'c', False, 10)],
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
def config_consistent_resources() -> Configuration:
    model1 = Model(
            'resources_test',
            None,
            'description',
            None,
            [
                Component('singlethreaded', Ports(), 'description', 'a'),
                Component('multithreaded', Ports(), 'description', 'b'),
                Component('submodel', Ports(), 'description', 'resources_test2'),
            ])

    model2 = Model(
            'resources_test2',
            None,
            'description',
            None,
            [
                Component('mpi_cores1', Ports(), 'description', 'c'),
                Component('mpi_cores2', Ports(), 'description', 'd'),
                Component('mpi_nodes1', Ports(), 'description', 'c'),
                Component('mpi_nodes2', Ports(), 'description', 'd')],
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
            'consistent_resources', None, [model1, model2], None, None, programs,
            resources)


@pytest.fixture
def config_inconsistent_resources() -> Configuration:
    model1 = Model(
            'got_resources', None, 'description', None,
            [
                Component('singlethreaded', Ports(), 'description', 'a'),
                Component('with_mpi', Ports(), 'description', 'b'),
                Component('without_mpi', Ports(), 'description', 'a'),
            ])

    model2 = Model(
            'missing_resources', None, 'description', None,
            [Component('singlethreaded2', Ports(), 'description', 'a')])

    programs = [
            Program('a', script='a', execution_model=ExecutionModel.DIRECT),
            Program('b', script='b', execution_model=ExecutionModel.INTELMPI)]

    resources = [
            ThreadedResReq(Ref('singlethreaded'), 1),
            ThreadedResReq(Ref('with_mpi'), 2),
            MPICoresResReq(Ref('without_mpi'), 10)]

    return Configuration(
            'test_config', None, [model1, model2], None, None, programs, resources)


@pytest.fixture
def config_component_loop() -> Configuration:
    main = Model(
            'main',
            Ports(),
            'Test model with a nested model loop',
            None,
            [
                Component(
                    'init', Ports(o_f='final'),
                    'Calculates initial conditions', 'submodel1'),
                Component(
                    'macro', Ports(f_init='init', o_i='out', s='in'), 'Macro model',
                    'submodel1'),
                Component(
                    'micro', Ports('init', o_f='final'),
                    'Micro model', 'micro'),
            ], [
                Conduit('init.final', 'macro.init'),
                Conduit('macro.out', 'micro.init'),
                Conduit('micro.out', 'macro.init'),
            ])

    submodel1 = Model(
            'submodel1',
            Ports(f_init='init', o_i='out', s='in'),
            'Implements the macro model',
            None,
            [
                Component(
                    'first', Ports(f_init='init', o_f='final'), 'First model',
                    'submodel2'),
                Component(
                    'second', Ports(f_init='init', o_i='out', s='in'), 'Second model',
                    'second')
            ], [
                Conduit('init', 'first.init'),
                Conduit('first.final', 'second.init'),
                Conduit('second.out', 'out'),
                Conduit('second.in', 'in')
            ])

    submodel2 = Model(
            'submodel2',
            Ports(f_init='init', o_f='final'),
            'Processes the input a bit',
            None,
            [Component('micro', Ports('init', o_f='final'), 'Ooops...', 'submodel1')],
            [
                Conduit('init', 'micro.init'),
                Conduit('micro.final', 'final')
            ])

    programs = [
            Program('micro', script='micro', execution_model=ExecutionModel.DIRECT),
            Program('second', script='second', execution_model=ExecutionModel.INTELMPI)]

    resources = [
            ThreadedResReq(Ref('micro'), 1),
            ThreadedResReq(Ref('second'), 2),]

    return Configuration(
            'config_Component_loop', None, [main, submodel1, submodel2], None, None,
            programs, resources)
