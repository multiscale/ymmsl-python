from collections import OrderedDict
from pathlib import Path

import pytest
from ymmsl import (
        Component, Configuration, ExecutionModel, Implementation, Model,
        ModelReference, MPICoresResReq, Checkpoints, ImplementationState,
        PartialConfiguration, Reference, Settings, ThreadedResReq, load, dump)
from ymmsl import SettingValue     # noqa: F401 # pylint: disable=unused-import


def test_configuration() -> None:
    setting_values = OrderedDict()    # type: OrderedDict[str, SettingValue]
    settings = Settings(setting_values)
    config = PartialConfiguration(None, settings)
    assert isinstance(config.settings, Settings)
    assert len(config.settings) == 0


def test_configuration_update_model1() -> None:
    model_ref1 = ModelReference('model1')
    base = PartialConfiguration(model_ref1)
    model_ref2 = ModelReference('model2')
    overlay = PartialConfiguration(model_ref2)

    base.update(overlay)

    assert base.model is not None
    assert overlay.model is not None
    assert base.model.name == overlay.model.name


def test_configuration_update_model2() -> None:
    model_ref1 = ModelReference('model1')
    base = PartialConfiguration(model_ref1)

    component1 = Component('macro', 'my.macro')
    model2 = Model('model2', [component1])
    overlay = PartialConfiguration(model2)

    base.update(overlay)

    assert base.model == model2


def test_configuration_update_model3() -> None:
    component1 = Component('macro', 'my.macro')
    model1 = Model('model1', [component1])
    base = Configuration(model1)

    model_ref2 = ModelReference('model2')
    overlay = PartialConfiguration(model_ref2)

    base.update(overlay)

    assert base.model == model1
    assert model1.name == 'model2'
    assert model1.components == [component1]


def test_configuration_update_model4() -> None:
    component1 = Component('macro', 'my.macro')
    model1 = Model('model1', [component1])
    base = Configuration(model1)

    component2 = Component('micro', 'my.micro')
    model2 = Model('model2', [component2])
    overlay = Configuration(model2)

    base.update(overlay)

    assert isinstance(base.model, Model)
    assert base.model == model1
    assert base.model.name == 'model2'
    assert component1 in base.model.components
    assert component2 in base.model.components


def test_configuration_update_implementations_add() -> None:
    implementation1 = Implementation(
            Reference('my.macro'), executable=Path('/home/test/macro.py'))
    base = PartialConfiguration(implementations=[implementation1])

    implementation2 = Implementation(
            Reference('my.micro'), executable=Path('/home/test/micro.py'))
    overlay = PartialConfiguration(implementations=[implementation2])

    base.update(overlay)

    assert len(base.implementations) == 2
    assert base.implementations[Reference('my.macro')] == implementation1
    assert base.implementations[Reference('my.micro')] == implementation2


def test_configuration_update_implementations_override() -> None:
    implementation1 = Implementation(
            Reference('my.macro'), executable=Path('/home/test/macro.py'))
    implementation2 = Implementation(
            Reference('my.micro'), executable=Path('/home/test/micro.py'))
    base = PartialConfiguration(
            implementations=[implementation1, implementation2])

    implementation3 = Implementation(
            Reference('my.micro'), executable=Path('/home/test/surrogate.py'))
    overlay = PartialConfiguration(implementations=[implementation3])

    base.update(overlay)

    assert len(base.implementations) == 2
    assert base.implementations[Reference('my.macro')] == implementation1
    assert base.implementations[Reference('my.micro')] == implementation3


def test_configuration_update_resources_add() -> None:
    resources1 = ThreadedResReq(Reference('my.macro'), 10)
    base = PartialConfiguration(resources=[resources1])

    resources2 = ThreadedResReq(Reference('my.micro'), 2)
    overlay = PartialConfiguration(resources=[resources2])

    base.update(overlay)

    assert len(base.resources) == 2
    assert base.resources[Reference('my.macro')] == resources1
    assert base.resources[Reference('my.micro')] == resources2


def test_configuration_update_resources_override() -> None:
    resources1 = ThreadedResReq(Reference('my.macro'), 10)
    resources2 = ThreadedResReq(Reference('my.micro'), 100)
    base = PartialConfiguration(resources=[resources1, resources2])

    resources3 = ThreadedResReq(Reference('my.micro'), 2)
    overlay = PartialConfiguration(resources=[resources3])

    base.update(overlay)

    assert len(base.resources) == 2
    assert base.resources[Reference('my.macro')] == resources1
    assert base.resources[Reference('my.micro')] == resources3


def test_configuration_update_description() -> None:
    description1 = ''
    description2 = 'single line description'
    description3 = 'multiline\ndescription'

    overlay1 = PartialConfiguration(description=description1)
    overlay2 = PartialConfiguration(description=description2)
    overlay3 = PartialConfiguration(description=description3)

    base = PartialConfiguration(description=description1)

    base.update(overlay1)
    assert base.description == ''

    base.update(overlay2)
    assert base.description == description2

    base.update(overlay3)
    assert base.description == description2 + '\n\n' + description3

    base.update(overlay1)
    assert base.description == description2 + '\n\n' + description3


def test_configuration_update_checkpoint(
        test_config4: PartialConfiguration) -> None:
    # Note: test_checkpoint.py tests merging of checkpoint definitions
    base = PartialConfiguration(checkpoints=Checkpoints(
            wallclocktime=test_config4.checkpoints.wallclocktime))
    overlay = PartialConfiguration(checkpoints=Checkpoints(
            simulationtime=test_config4.checkpoints.simulationtime))

    assert base.checkpoints.simulationtime is None
    assert overlay.checkpoints.wallclocktime is None

    base.update(overlay)
    assert (base.checkpoints.simulationtime
            == overlay.checkpoints.simulationtime)


def test_configuration_update_resume() -> None:
    base = PartialConfiguration(resume={'a': 'a'})
    overlay = PartialConfiguration(resume={'b': 'b'})

    base.update(overlay)
    assert len(base.resume) == 2
    assert base.resume['a'] == 'a'
    assert base.resume['b'] == 'b'


def test_configuration_update_resume_override() -> None:
    base = PartialConfiguration(resume={'a': 'a', 'b': 'b'})
    overlay = PartialConfiguration(resume={'b': 'b_update'})

    base.update(overlay)
    assert len(base.resume) == 2
    assert base.resume['a'] == 'a'
    assert base.resume['b'] == 'b_update'


def test_as_configuration(
        test_config2: PartialConfiguration, test_config4: PartialConfiguration
        ) -> None:

    with pytest.raises(ValueError):
        test_config2.as_configuration()

    with pytest.raises(ValueError):
        test_config4.as_configuration()

    test_config4.model = test_config2.model

    config = test_config4.as_configuration()

    assert config.model == test_config4.model
    assert config.implementations == test_config4.implementations
    assert config.resources == test_config4.resources
    assert config.description == test_config4.description
    assert config.checkpoints == test_config4.checkpoints
    assert config.resume == test_config4.resume


def test_check_consistent(test_config6: Configuration) -> None:
    test_config6.check_consistent()
    test_config6.implementations[Reference('c')].execution_model = (
            ExecutionModel.DIRECT)
    with pytest.raises(RuntimeError):
        test_config6.check_consistent()
    test_config6.implementations[Reference('c')].execution_model = (
            ExecutionModel.OPENMPI)
    test_config6.resources[Reference('singlethreaded')] = MPICoresResReq(
            Reference('singlethreaded'), 16, 8)
    with pytest.raises(RuntimeError):
        test_config6.check_consistent()


def test_check_consistent_checkpoints(test_config8: Configuration) -> None:
    test_config8.check_consistent()

    del test_config8.resume['macro']
    with pytest.raises(RuntimeError):
        test_config8.check_consistent()

    test_config8.resume = {}  # disable resuming
    test_config8.check_consistent()

    impl_macro = test_config8.implementations['macro_python']
    impl_micro1 = test_config8.implementations['micro1_python']

    impl_macro.supports_checkpoint = False
    with pytest.raises(RuntimeError):
        test_config8.check_consistent()

    impl_macro.supports_checkpoint = True
    impl_micro1.supports_checkpoint = False
    test_config8.check_consistent()

    impl_micro1.state = ImplementationState.STATEFUL
    with pytest.raises(RuntimeError):
        test_config8.check_consistent()

    test_config8.checkpoints = Checkpoints()  # disable checkpointing
    test_config8.check_consistent()


def test_load_nil_settings() -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'settings:\n'
    )

    configuration = load(text)

    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.implementations) == 0
    assert len(configuration.resources) == 0


def test_load_no_settings() -> None:
    text = (
            'ymmsl_version: v0.1\n'
            )

    configuration = load(text)

    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.implementations) == 0
    assert len(configuration.resources) == 0


def test_dump_empty_settings() -> None:
    configuration = PartialConfiguration(None, Settings())
    text = dump(configuration)

    assert text == 'ymmsl_version: v0.1\n'


def test_load_implementations() -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'implementations:\n'
            '  macro:\n'
            '    script: |\n'
            '      #!/bin/bash\n'
            '\n'
            '      /usr/bin/python3 /home/test/macro.py\n'
            '\n'
            '  meso: |\n'
            '    #!/bin/bash\n'
            '\n'
            '    /home/test/meso.py\n'
            '\n'
            '  micro: /home/test/micro\n'
            '  micro2:\n'
            '    modules: python/3.6.0\n'
            '    virtual_env: /home/test/venv\n'
            '    env:\n'
            '      VAR1: 13\n'
            '      VAR2: Testing\n'
            '      VAR3: 12.34\n'
            '      VAR4: true\n'
            '    execution_model: direct\n'
            '    executable: /home/test/micro2\n'
            '    args:\n'
            '      - -s\n'
            '      - -t\n'
            )

    configuration = load(text)

    assert configuration.implementations['macro'].name == 'macro'
    assert configuration.implementations['macro'].script == (
            '#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n')
    assert configuration.implementations['meso'].name == 'meso'
    assert configuration.implementations['meso'].script == (
            '#!/bin/bash\n\n/home/test/meso.py\n')
    assert configuration.implementations['micro'].name == 'micro'
    assert configuration.implementations['micro'].script == (
            '/home/test/micro')

    m2 = configuration.implementations['micro2']
    assert m2.name == 'micro2'
    assert m2.script is None
    assert m2.modules == ['python/3.6.0']
    assert m2.virtual_env == Path('/home/test/venv')
    assert m2.env is not None
    assert m2.env['VAR1'] == '13'
    assert m2.env['VAR2'] == 'Testing'
    assert m2.env['VAR3'] == '12.34'
    assert m2.env['VAR4'] == 'true'
    assert m2.executable == Path('/home/test/micro2')
    assert m2.args == ['-s', '-t']
    assert m2.execution_model == ExecutionModel.DIRECT


def test_load_implementations_script_list() -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'implementations:\n'
            '  macro:\n'
            '    script:\n'
            '    - "#!/bin/bash"\n'
            '    - ""\n'
            '    - /usr/bin/python3 /home/test/macro.py\n'
            '    - ""\n'
            '  meso:\n'
            '    - "#!/bin/bash"\n'
            '    - ""\n'
            '    - /home/test/meso.py\n'
            '  micro: /home/test/micro\n'
            )

    configuration = load(text)

    assert configuration.implementations['macro'].name == 'macro'
    assert configuration.implementations['macro'].script == (
            '#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n\n')
    assert configuration.implementations['meso'].name == 'meso'
    assert configuration.implementations['meso'].script == (
            '#!/bin/bash\n\n/home/test/meso.py\n')
    assert configuration.implementations['micro'].name == 'micro'
    assert configuration.implementations['micro'].script == (
            '/home/test/micro')


def test_dump_implementations() -> None:
    implementations = [
            Implementation(
                name=Reference('macro'),
                script='#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n'
                ),
            Implementation(
                name=Reference('meso'),
                script='#!/bin/bash\n\n/home/test/meso.py'),
            Implementation(name=Reference('micro'), script='/home/test/micro'),
            Implementation(
                name=Reference('micro2'),
                modules=['python/3.6.0', 'gcc/9.3.0'],
                virtual_env=Path('/home/test/env'),
                env={'VAR1': '10', 'VAR2': 'Test'},
                execution_model=ExecutionModel.OPENMPI,
                executable=Path('/home/test/micro2'),
                args=['-v', '-s'])]

    configuration = PartialConfiguration(None, None, implementations)

    text = dump(configuration)
    assert text == (
            'ymmsl_version: v0.1\n'
            'implementations:\n'
            '  macro: |\n'
            '    #!/bin/bash\n'
            '\n'
            '    /usr/bin/python3 /home/test/macro.py\n'
            '  meso: |-\n'
            '    #!/bin/bash\n'
            '\n'
            '    /home/test/meso.py\n'
            '  micro: /home/test/micro\n'
            '  micro2:\n'
            '    modules:\n'
            '    - python/3.6.0\n'
            '    - gcc/9.3.0\n'
            '    virtual_env: /home/test/env\n'
            '    env:\n'
            '      VAR1: \'10\'\n'
            '      VAR2: Test\n'
            '    execution_model: openmpi\n'
            '    executable: /home/test/micro2\n'
            '    args:\n'
            '    - -v\n'
            '    - -s\n'
            )


def test_load_resources() -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  macro:\n'
            '    threads: 10\n'
            '  micro:\n'
            '    threads: 1\n'
            )

    configuration = load(text)

    assert configuration.resources['macro'].name == 'macro'
    assert configuration.resources['macro'].threads == 10
    assert configuration.resources['micro'].name == 'micro'
    assert configuration.resources['micro'].threads == 1


def test_dump_resources() -> None:
    resources = [
            ThreadedResReq(Reference('macro'), 10),
            ThreadedResReq(Reference('micro'), 1)]

    configuration = PartialConfiguration(None, None, None, resources)

    text = dump(configuration)
    assert text == (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  macro:\n'
            '    threads: 10\n'
            '  micro:\n'
            '    threads: 1\n'
            )
