from collections import OrderedDict
from pathlib import Path

import pytest

from ymmsl.io import load, dump
from ymmsl.v0_2 import (
        BaseEnv, Configuration, Checkpoints, Component, Conduit, ExecutionModel,
        Identifier, ImportStatement, KeepsStateForNextUse, Model, Operator, Port, Ports,
        Program, Reference, Settings, SettingType, ThreadedResReq, Timeline)
from ymmsl.v0_2 import SettingValue


Ref = Reference


def test_configuration() -> None:
    setting_values: OrderedDict[str, SettingValue] = OrderedDict()
    settings = Settings(setting_values)
    model1 = Model('model1', None, 'description', None, [])
    model2 = Model('model2', None, 'description', None, [])
    config = Configuration('description', None, [model1, model2], settings)

    assert config.description == 'description'

    assert len(config.models) == 2
    assert config.models[Ref('model1')] is model1
    assert config.models[Ref('model2')] is model2

    assert isinstance(config.settings, Settings)
    assert len(config.settings) == 0


def test_create_duplicate_models() -> None:
    with pytest.raises(ValueError):
        Configuration('desc', models=[Model('a'), Model('a')])


def test_create_duplicate_programs() -> None:
    with pytest.raises(ValueError):
        Configuration(
                'desc', programs=[Program('p', script='p'), Program('p', script='q')])


def test_load_models() -> None:
    text = (
            'ymmsl_version: v0.2\n'
            'description: Test loading multiple models\n'
            'models:\n'
            '  macro_micro:\n'
            '    components:\n'
            '      macro:\n'
            '        ports:\n'
            '          o_i: out\n'
            '          s: in\n'
            '        description: the macro component\n'
            '        implementation: macro_program\n'
            '      micro:\n'
            '        ports:\n'
            '          f_init: init\n'
            '          o_f: final\n'
            '        description: the micro component\n'
            '        implementation: micro_program\n'
            '  do_nothing:\n'
            '    components:\n'
            '      nil:\n'
            '        ports: {}\n'
            '        description: a component that does nothing\n'
            '        implementation: nil_program\n'
            )

    configuration = load(text)

    assert isinstance(configuration, Configuration)
    assert len(configuration.models) == 2
    mm = configuration.models[Ref('macro_micro')]
    assert mm.components[0].ports['out'] == Port(
            Identifier('out'), Operator.O_I, Timeline(''))
    dn = configuration.models[Ref('do_nothing')]
    assert len(dn.components[0].ports) == 0


def test_load_nil_settings() -> None:
    text = (
            'ymmsl_version: v0.2\n'
            'description: test loading nil-valued settings\n'
            'settings:\n'
    )

    configuration = load(text)

    assert isinstance(configuration, Configuration)
    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.resources) == 0


def test_load_custom_implementations(test_config10_text: str) -> None:
    configuration = load(test_config10_text)

    assert isinstance(configuration, Configuration)
    assert configuration.custom_implementations == {
            Reference('c1'): Reference('program1'),
            Reference('c2.init_model'): Reference('initer2')
            }


def test_dump_custom_implementations(
        test_config10: Configuration, test_config10_text: str) -> None:
    text = dump(test_config10)
    assert text == test_config10_text


def test_load_no_settings() -> None:
    text = (
            'ymmsl_version: v0.2\n'
            'description: test loading with no settings\n'
            )

    configuration = load(text)

    assert isinstance(configuration, Configuration)
    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.resources) == 0


def test_dump_empty_settings() -> None:
    configuration = Configuration('', None, None, Settings())
    text = dump(configuration)

    assert text == (
            'ymmsl_version: v0.2\n'
            'description: \'\'\n')


def test_load_programs(test_config5_text: str) -> None:
    configuration = load(test_config5_text)

    assert isinstance(configuration, Configuration)
    assert len(configuration.programs) == 1
    prog = configuration.programs[Reference('macro')]
    assert prog.name == 'macro'
    assert prog.ports.sending_port_names() == ['final', 'out1', 'out2']
    assert prog.ports.receiving_port_names() == ['init', 'in1', 'in2']
    assert prog.base_env == BaseEnv.LOGIN
    assert prog.modules is not None
    assert len(prog.modules) == 2
    assert prog.modules[0] == 'gcc/13.3.0'
    assert prog.modules[1] == 'FFTW/3.2.1'
    assert prog.virtual_env == Path('/home/user/.venv')
    assert len(prog.env) == 2
    assert prog.env['SETTING'] == 'something'
    assert prog.env['VARIABLE'] == '42'
    assert prog.execution_model == ExecutionModel.INTELMPI
    assert prog.executable == Path('python3')
    assert prog.args == ['/home/user/script.py']
    assert prog.can_share_resources is False
    assert prog.keeps_state_for_next_use == KeepsStateForNextUse.HELPFUL


def test_dump_programs(
        test_config5: Configuration, test_config5_text: str) -> None:
    text = dump(test_config5)
    assert text == test_config5_text


def test_load_resources() -> None:
    text = (
            'ymmsl_version: v0.2\n'
            'description: testing loading of resources\n'
            'resources:\n'
            '  macro:\n'
            '    threads: 10\n'
            '  micro:\n'
            '    threads: 1\n'
            )

    configuration = load(text)

    assert isinstance(configuration, Configuration)
    assert configuration.resources[Ref('macro')].name == 'macro'
    assert configuration.resources[Ref('macro')].threads == 10      # type: ignore
    assert configuration.resources[Ref('micro')].name == 'micro'
    assert configuration.resources[Ref('micro')].threads == 1       # type: ignore


def test_dump_resources() -> None:
    resources = [
            ThreadedResReq(Ref('macro'), 10),
            ThreadedResReq(Ref('micro'), 1)]

    configuration = Configuration('', resources=resources)

    text = dump(configuration)
    assert text == (
            'ymmsl_version: v0.2\n'
            'description: \'\'\n'
            'resources:\n'
            '  macro:\n'
            '    threads: 10\n'
            '  micro:\n'
            '    threads: 1\n'
            )


def test_configuration_update_description() -> None:
    description1 = ''
    description2 = 'single line description'
    description3 = 'multiline\ndescription'

    overlay1 = Configuration(description=description1)
    overlay2 = Configuration(description=description2)
    overlay3 = Configuration(description=description3)

    base = Configuration(description=description1)

    base.update(overlay1)
    assert base.description == ''

    base.update(overlay2)
    assert base.description == description2

    base.update(overlay3)
    assert base.description == description2 + '\n\n' + description3

    base.update(overlay1)
    assert base.description == description2 + '\n\n' + description3


def test_configuration_update_model_error() -> None:
    base = Configuration(
            'Configuration for testing', None, [
                Model('model', Ports(), 'description', None, [
                    Component('macro', Ports(o_i='out', s='in'), 'description'),
                    Component('micro', Ports(f_init='init', o_f='final'), 'description')
                ], [
                    Conduit('macro.out', 'micro.init'),
                    Conduit('micro.final', 'macro.in')]
                )
            ])

    overlay1 = Configuration(
            'Extra component', None,
            [
                Model('model', None, 'description', None,
                      [Component('micro2', Ports(), 'description')], [])
            ])

    with pytest.raises(RuntimeError):
        base.update(overlay1)

    overlay2 = Configuration(
            'Extra conduit', None, [Model('model', None, 'description', None, [], [
                Conduit('micro.final', 'macro.in2')])])

    with pytest.raises(RuntimeError):
        base.update(overlay2)


def test_configuration_update_imports() -> None:
    base = Configuration('', [
        ImportStatement('a.b.c', 'implementation', 'p'),
        ImportStatement('d.b.c', 'implementation', 'q')])

    overlay = Configuration('', [
        ImportStatement('e.f.g', 'implementation', 's'),
        ImportStatement('b.f.h', 'implementation', 't')])

    base.update(overlay)

    assert base.imports[0].module == 'a.b.c'
    assert base.imports[0].name == 'p'
    assert base.imports[1].module == 'd.b.c'
    assert base.imports[1].name == 'q'
    assert base.imports[2].module == 'e.f.g'
    assert base.imports[2].name == 's'
    assert base.imports[3].module == 'b.f.h'
    assert base.imports[3].name == 't'


def test_configuration_update_custom_implementations() -> None:
    base = Configuration(
            'Configuration for testing', custom_implementations={
                Reference('c1'): Reference('impl1')})

    overlay1 = Configuration(
            'Extra and override', custom_implementations={
                Reference('c1'): Reference('impl2'),
                Reference('c2.a'): Reference('impl1')})

    base.update(overlay1)

    assert base.custom_implementations[Reference('c1')] == 'impl2'
    assert base.custom_implementations[Reference('c2.a')] == 'impl1'


def test_configuration_update_programs() -> None:
    base = Configuration(
            'Configuration for testing',
            programs=[Program('impl1', executable=Path('impl1'))])

    overlay1 = Configuration(
            'Extra program',
            programs=[Program('impl2', executable=Path('impl2'))])

    base.update(overlay1)

    assert base.programs[Reference('impl1')].name == 'impl1'
    assert base.programs[Reference('impl2')].name == 'impl2'

    overlay2 = Configuration(
            'Conflicting program',
            programs=[Program('impl1', executable=Path('impl3'))])

    with pytest.raises(RuntimeError):
        base.update(overlay2)


def test_configuration_update_resources_override() -> None:
    resources1 = ThreadedResReq(Ref('my.macro'), 10)
    resources2 = ThreadedResReq(Ref('my.micro'), 100)
    base = Configuration('', resources=[resources1, resources2])

    resources3 = ThreadedResReq(Ref('my.micro'), 2)
    overlay = Configuration('', resources=[resources3])

    base.update(overlay)

    assert len(base.resources) == 2
    assert base.resources[Ref('my.macro')] == resources1
    assert base.resources[Ref('my.micro')] == resources3


def test_configuration_update_checkpoint(test_config4: Configuration) -> None:
    # Note: test_checkpoint.py tests merging of checkpoint definitions
    base = Configuration('', checkpoints=Checkpoints(
            wallclock_time=test_config4.checkpoints.wallclock_time))
    overlay = Configuration('', checkpoints=Checkpoints(
            simulation_time=test_config4.checkpoints.simulation_time))

    assert base.checkpoints.simulation_time == []
    assert overlay.checkpoints.wallclock_time == []

    base.update(overlay)
    assert (base.checkpoints.simulation_time == overlay.checkpoints.simulation_time)


def test_configuration_update_resume() -> None:
    base = Configuration('', resume={Ref('a'): Path('a')})
    overlay = Configuration('', resume={Ref('b'): Path('b')})

    base.update(overlay)
    assert len(base.resume) == 2
    assert base.resume[Ref('a')] == Path('a')
    assert base.resume[Ref('b')] == Path('b')


def test_configuration_update_resume_override() -> None:
    base = Configuration('', resume={Ref('a'): Path('a'), Ref('b'): Path('b')})
    overlay = Configuration('', resume={Ref('b'): Path('b_update')})

    base.update(overlay)
    assert len(base.resume) == 2
    assert base.resume[Ref('a')] == Path('a')
    assert base.resume[Ref('b')] == Path('b_update')


def test_configuration_update_resources_add() -> None:
    resources1 = ThreadedResReq(Ref('my.macro'), 10)
    base = Configuration('', resources=[resources1])

    resources2 = ThreadedResReq(Ref('my.micro'), 2)
    overlay = Configuration('', resources=[resources2])

    base.update(overlay)

    assert len(base.resources) == 2
    assert base.resources[Ref('my.macro')] == resources1
    assert base.resources[Ref('my.micro')] == resources2


def test_check_duplicate_implementations(test_config13: Configuration) -> None:
    with pytest.raises(RuntimeError) as e:
        test_config13.check_consistent()

    assert len(str(e.value).split('\n')) == 2


def test_check_consistent_implementation_ports(test_config8: Configuration) -> None:
    test_config8.check_consistent()


def test_check_inconsistent_implementation_ports(test_config9: Configuration) -> None:
    with pytest.raises(RuntimeError) as e:
        test_config9.check_consistent()

    assert len(str(e.value).split('\n')) == 8


def test_check_consistent_custom_implementations(test_config11: Configuration) -> None:
    test_config11.check_consistent()


def test_check_inconsistent_custom_impls(test_config12: Configuration) -> None:
    with pytest.raises(RuntimeError) as e:
        test_config12.check_consistent()

    assert len(str(e.value).split('\n')) == 3


def test_check_consistent_settings(test_config3: Configuration) -> None:
    test_config3.check_consistent()

    test_config3.settings['submodel.c2[3].delta'] = 10
    with pytest.raises(RuntimeError) as e:
        test_config3.check_consistent()

    assert len(str(e.value).split('\n')) == 2

    del test_config3.settings['submodel.c2[3].delta']
    test_config3.settings['alpha'] = [[1.2, 3.4], [5.6, 7.8]]

    with pytest.raises(RuntimeError) as e:
        test_config3.check_consistent()

    assert len(str(e.value).split('\n')) == 2

    test_config3.settings['alpha'] = 3.2

    model2 = test_config3.models[Reference('supported_settings_test2')]
    assert model2.supported_settings is not None
    model2.supported_settings['delta'] = SettingType.INT

    with pytest.raises(RuntimeError) as e:
        test_config3.check_consistent()

    assert len(str(e.value).split('\n')) == 2


def test_check_consistent_resources(test_config6: Configuration) -> None:
    test_config6.check_consistent()


def test_check_inconsistent_resources(test_config7: Configuration) -> None:
    with pytest.raises(RuntimeError) as e:
        test_config7.check_consistent()

    assert len(str(e.value).split('\n')) == 4
