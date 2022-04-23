from collections import OrderedDict
from pathlib import Path
from typing import Callable

import pytest
import yatiml
from ymmsl import (
        Component, Configuration, ExecutionModel, Identifier, Implementation,
        Model, ModelReference, MPICoresResReq, MPINodesResReq,
        PartialConfiguration, Reference, Settings, ThreadedResReq)
from ymmsl import SettingValue     # noqa: F401 # pylint: disable=unused-import
from ymmsl.document import Document
from ymmsl.execution import ResourceRequirements


@pytest.fixture
def load_configuration() -> Callable:
    return yatiml.load_function(
            Document, ExecutionModel, Configuration, Identifier,
            Implementation, MPICoresResReq, MPINodesResReq,
            PartialConfiguration, Reference, ResourceRequirements, Settings,
            ThreadedResReq)


@pytest.fixture
def dump_configuration() -> Callable:
    return yatiml.dumps_function(
            Configuration, Document, ExecutionModel, Identifier,
            Implementation, MPICoresResReq, MPINodesResReq,
            PartialConfiguration, Reference, ResourceRequirements, Settings,
            ThreadedResReq)


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


def test_load_nil_settings(load_configuration: Callable) -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'settings:\n'
    )

    configuration = load_configuration(text)

    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.implementations) == 0
    assert len(configuration.resources) == 0


def test_load_no_settings(load_configuration: Callable) -> None:
    text = (
            'ymmsl_version: v0.1\n'
            )

    configuration = load_configuration(text)

    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.implementations) == 0
    assert len(configuration.resources) == 0


def test_dump_empty_settings(dump_configuration: Callable) -> None:
    configuration = PartialConfiguration(None, Settings())
    text = dump_configuration(configuration)

    assert text == 'ymmsl_version: v0.1\n'


def test_load_implementations(load_configuration: Callable) -> None:
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

    configuration = load_configuration(text)

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


def test_load_implementations_script_list(
        load_configuration: Callable) -> None:
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

    configuration = load_configuration(text)

    assert configuration.implementations['macro'].name == 'macro'
    assert configuration.implementations['macro'].script == (
            '#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n\n')
    assert configuration.implementations['meso'].name == 'meso'
    assert configuration.implementations['meso'].script == (
            '#!/bin/bash\n\n/home/test/meso.py\n')
    assert configuration.implementations['micro'].name == 'micro'
    assert configuration.implementations['micro'].script == (
            '/home/test/micro')


def test_dump_implementations(dump_configuration: Callable) -> None:
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

    text = dump_configuration(configuration)
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


def test_load_resources(load_configuration: Callable) -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  macro:\n'
            '    threads: 10\n'
            '  micro:\n'
            '    threads: 1\n'
            )

    configuration = load_configuration(text)

    assert configuration.resources['macro'].name == 'macro'
    assert configuration.resources['macro'].threads == 10
    assert configuration.resources['micro'].name == 'micro'
    assert configuration.resources['micro'].threads == 1


def test_dump_resources(dump_configuration: Callable) -> None:
    resources = [
            ThreadedResReq(Reference('macro'), 10),
            ThreadedResReq(Reference('micro'), 1)]

    configuration = PartialConfiguration(None, None, None, resources)

    text = dump_configuration(configuration)
    assert text == (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  macro:\n'
            '    threads: 10\n'
            '  micro:\n'
            '    threads: 1\n'
            )
