from collections import OrderedDict
from typing import Callable

import pytest
import yatiml
from ymmsl import (
        Component, Configuration, Identifier, Implementation, Model,
        ModelReference, Reference, Resources, Settings)
from ymmsl import SettingValue     # noqa: F401 # pylint: disable=unused-import
from ymmsl.document import Document


@pytest.fixture
def load_configuration() -> Callable:
    return yatiml.load_function(
            Document, Configuration, Identifier, Implementation, Reference,
            Resources, Settings)


@pytest.fixture
def dump_configuration() -> Callable:
    return yatiml.dumps_function(
            Configuration, Document, Identifier, Implementation, Reference,
            Resources, Settings)


def test_configuration() -> None:
    setting_values = OrderedDict()    # type: OrderedDict[str, SettingValue]
    settings = Settings(setting_values)
    config = Configuration(None, settings)
    assert isinstance(config.settings, Settings)
    assert len(config.settings) == 0


def test_configuration_update_model1() -> None:
    model_ref1 = ModelReference('model1')
    base = Configuration(model_ref1)
    model_ref2 = ModelReference('model2')
    overlay = Configuration(model_ref2)

    base.update(overlay)

    assert base.model == model_ref2


def test_configuration_update_model2() -> None:
    model_ref1 = ModelReference('model1')
    base = Configuration(model_ref1)

    component1 = Component('macro', 'my.macro')
    model2 = Model('model2', [component1])
    overlay = Configuration(model2)

    base.update(overlay)

    assert base.model == model2


def test_configuration_update_model3() -> None:
    component1 = Component('macro', 'my.macro')
    model1 = Model('model1', [component1])
    base = Configuration(model1)

    model_ref2 = ModelReference('model2')
    overlay = Configuration(model_ref2)

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
            Reference('my.macro'), '/home/test/macro.py')
    base = Configuration(implementations=[implementation1])

    implementation2 = Implementation(
            Reference('my.micro'), '/home/test/micro.py')
    overlay = Configuration(implementations=[implementation2])

    base.update(overlay)

    assert len(base.implementations) == 2
    assert base.implementations[Reference('my.macro')] == implementation1
    assert base.implementations[Reference('my.micro')] == implementation2


def test_configuration_update_implementations_override() -> None:
    implementation1 = Implementation(
            Reference('my.macro'), '/home/test/macro.py')
    implementation2 = Implementation(
            Reference('my.micro'), '/home/test/micro.py')
    base = Configuration(implementations=[implementation1, implementation2])

    implementation3 = Implementation(
            Reference('my.micro'), '/home/test/surrogate.py')
    overlay = Configuration(implementations=[implementation3])

    base.update(overlay)

    assert len(base.implementations) == 2
    assert base.implementations[Reference('my.macro')] == implementation1
    assert base.implementations[Reference('my.micro')] == implementation3


def test_configuration_update_resources_add() -> None:
    resources1 = Resources(Reference('my.macro'), 10)
    base = Configuration(resources=[resources1])

    resources2 = Resources(Reference('my.micro'), 2)
    overlay = Configuration(resources=[resources2])

    base.update(overlay)

    assert len(base.resources) == 2
    assert base.resources[Reference('my.macro')] == resources1
    assert base.resources[Reference('my.micro')] == resources2


def test_configuration_update_resources_override() -> None:
    resources1 = Resources(Reference('my.macro'), 10)
    resources2 = Resources(Reference('my.micro'), 100)
    base = Configuration(resources=[resources1, resources2])

    resources3 = Resources(Reference('my.micro'), 2)
    overlay = Configuration(resources=[resources3])

    base.update(overlay)

    assert len(base.resources) == 2
    assert base.resources[Reference('my.macro')] == resources1
    assert base.resources[Reference('my.micro')] == resources3


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
    configuration = Configuration(None, Settings())
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


def test_load_implementations_script_list(load_configuration: Callable) -> None:
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
            '#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n')
    assert configuration.implementations['meso'].name == 'meso'
    assert configuration.implementations['meso'].script == (
            '#!/bin/bash\n\n/home/test/meso.py')
    assert configuration.implementations['micro'].name == 'micro'
    assert configuration.implementations['micro'].script == (
            '/home/test/micro')


def test_dump_implementations(dump_configuration: Callable) -> None:
    implementations = [
            Implementation(
                Reference('macro'),
                '#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n'),
            Implementation(
                Reference('meso'),
                '#!/bin/bash\n\n/home/test/meso.py'),
            Implementation(Reference('micro'), '/home/test/micro')]

    configuration = Configuration(None, None, implementations)

    text = dump_configuration(configuration)
    assert text == (
            'ymmsl_version: v0.1\n'
            'implementations:\n'
            '  macro:\n'
            '  - \'#!/bin/bash\'\n'
            '  - \'\'\n'
            '  - /usr/bin/python3 /home/test/macro.py\n'
            '  - \'\'\n'
            '  meso:\n'
            '  - \'#!/bin/bash\'\n'
            '  - \'\'\n'
            '  - /home/test/meso.py\n'
            '  micro: /home/test/micro\n'
            )


def test_load_resources(load_configuration: Callable) -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  macro: 10\n'
            '  micro:\n'
            '    num_cores: 1\n'
            )

    configuration = load_configuration(text)

    assert configuration.resources['macro'].name == 'macro'
    assert configuration.resources['macro'].num_cores == 10
    assert configuration.resources['micro'].name == 'micro'
    assert configuration.resources['micro'].num_cores == 1


def test_dump_resources(dump_configuration: Callable) -> None:
    resources = [
            Resources(Reference('macro'), 10),
            Resources(Reference('micro'), 1)]

    configuration = Configuration(None, None, None, resources)

    text = dump_configuration(configuration)
    assert text == (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  macro: 10\n'
            '  micro: 1\n'
            )
