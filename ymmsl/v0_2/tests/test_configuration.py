from collections import OrderedDict
from pathlib import Path

import pytest

from ymmsl.io import load, dump
from ymmsl.v0_2 import (
        Configuration, Checkpoints, Component, Conduit, Identifier, ImportStatement,
        Model, Operator, Port, Ports, Program, Reference, Settings, SettingType,
        SettingValue, ThreadedResReq, Timeline)


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


def test_load_custom_implementations(config_custom_implementations_text: str) -> None:
    configuration = load(config_custom_implementations_text)

    assert isinstance(configuration, Configuration)
    assert configuration.custom_implementations == {
            Reference('c1'): Reference('program1'),
            Reference('c2.init_model'): Reference('initer2')
            }


def test_dump_custom_implementations(
        config_custom_implementations: Configuration,
        config_custom_implementations_text: str) -> None:
    text = dump(config_custom_implementations)
    assert text == config_custom_implementations_text


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


def test_configuration_update_checkpoint(
        config_update_checkpoint: Configuration) -> None:
    # Note: test_checkpoint.py tests merging of checkpoint definitions
    base = Configuration('', checkpoints=Checkpoints(
            wallclock_time=config_update_checkpoint.checkpoints.wallclock_time))
    overlay = Configuration('', checkpoints=Checkpoints(
            simulation_time=config_update_checkpoint.checkpoints.simulation_time))

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


def test_check_duplicate_implementations(
        config_duplicate_implementations: Configuration) -> None:
    with pytest.raises(RuntimeError) as e:
        config_duplicate_implementations.check_consistent()

    assert len(str(e.value).split('\n')) == 2


def test_check_consistent_implementation_ports(
        config_consistent_impl_ports: Configuration) -> None:
    config_consistent_impl_ports.check_consistent()


def test_check_inconsistent_implementation_ports(
        config_inconsistent_impl_ports: Configuration) -> None:
    with pytest.raises(RuntimeError) as e:
        config_inconsistent_impl_ports.check_consistent()

    assert len(str(e.value).split('\n')) == 8


def test_check_consistent_custom_implementations(
        config_consistent_custom_impls: Configuration) -> None:
    config_consistent_custom_impls.check_consistent()


def test_check_inconsistent_custom_impls(
        config_inconsistent_custom_impls: Configuration) -> None:
    with pytest.raises(RuntimeError) as e:
        config_inconsistent_custom_impls.check_consistent()

    assert len(str(e.value).split('\n')) == 3


def test_check_consistent_settings(config_consistent_settings: Configuration) -> None:
    config_consistent_settings.check_consistent()

    config_consistent_settings.settings['submodel.c2[3].delta'] = 10
    with pytest.raises(RuntimeError) as e:
        config_consistent_settings.check_consistent()

    assert len(str(e.value).split('\n')) == 2

    del config_consistent_settings.settings['submodel.c2[3].delta']
    config_consistent_settings.settings['alpha'] = [[1.2, 3.4], [5.6, 7.8]]

    with pytest.raises(RuntimeError) as e:
        config_consistent_settings.check_consistent()

    assert len(str(e.value).split('\n')) == 2

    config_consistent_settings.settings['alpha'] = 3.2

    model2 = config_consistent_settings.models[Reference('supported_settings_test2')]
    assert model2.supported_settings is not None
    model2.supported_settings['delta'] = SettingType.INT

    with pytest.raises(RuntimeError) as e:
        config_consistent_settings.check_consistent()

    assert len(str(e.value).split('\n')) == 2


def test_check_consistent_resources(config_consistent_resources: Configuration) -> None:
    config_consistent_resources.check_consistent()


def test_check_inconsistent_resources(
        config_inconsistent_resources: Configuration) -> None:
    with pytest.raises(RuntimeError) as e:
        config_inconsistent_resources.check_consistent()

    assert len(str(e.value).split('\n')) == 4
