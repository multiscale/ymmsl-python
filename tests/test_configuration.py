from collections import OrderedDict
from typing_extensions import Type

import pytest
from ruamel import yaml
import yatiml
from ymmsl import (
        Component, Configuration, Identifier, Implementation, Model,
        ModelReference, Reference, Resources, Settings)
from ymmsl import SettingValue     # noqa: F401 # pylint: disable=unused-import
from ymmsl.document import Document


@pytest.fixture
def configuration_loader() -> Type:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [
        Configuration, Document, Identifier, Implementation, Reference,
        Resources, Settings])
    yatiml.set_document_type(Loader, Document)
    return Loader


@pytest.fixture
def configuration_dumper() -> Type:
    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [
        Configuration, Document, Identifier, Implementation, Reference,
        Resources, Settings])
    return Dumper


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
    assert implementation1 in base.implementations
    assert implementation2 in base.implementations


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
    assert implementation1 in base.implementations
    assert implementation3 in base.implementations


def test_configuration_update_resources_add() -> None:
    resources1 = Resources(Reference('my.macro'), 10)
    base = Configuration(resources=[resources1])

    resources2 = Resources(Reference('my.micro'), 2)
    overlay = Configuration(resources=[resources2])

    base.update(overlay)

    assert len(base.resources) == 2
    assert resources1 in base.resources
    assert resources2 in base.resources


def test_configuration_update_resources_override() -> None:
    resources1 = Resources(Reference('my.macro'), 10)
    resources2 = Resources(Reference('my.micro'), 100)
    base = Configuration(resources=[resources1, resources2])

    resources3 = Resources(Reference('my.micro'), 2)
    overlay = Configuration(resources=[resources3])

    base.update(overlay)

    assert len(base.resources) == 2
    assert resources1 in base.resources
    assert resources3 in base.resources


def test_load_nil_settings(configuration_loader: Type) -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'settings:\n'
            )

    configuration = yaml.load(text, Loader=configuration_loader)

    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.implementations) == 0
    assert len(configuration.resources) == 0


def test_load_no_settings(configuration_loader: Type) -> None:
    text = (
            'ymmsl_version: v0.1\n'
            )

    configuration = yaml.load(text, Loader=configuration_loader)

    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.implementations) == 0
    assert len(configuration.resources) == 0


def test_dump_empty_settings(configuration_dumper: Type) -> None:
    configuration = Configuration(None, Settings())
    text = yaml.dump(configuration, Dumper=configuration_dumper)

    assert text == 'ymmsl_version: v0.1\n'


def test_load_implementations(configuration_loader: Type) -> None:
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

    configuration = yaml.load(text, Loader=configuration_loader)

    assert configuration.implementations[0].name == 'macro'
    assert configuration.implementations[0].script == (
            '#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n')
    assert configuration.implementations[1].name == 'meso'
    assert configuration.implementations[1].script == (
            '#!/bin/bash\n\n/home/test/meso.py\n')
    assert configuration.implementations[2].name == 'micro'
    assert configuration.implementations[2].script == (
            '/home/test/micro')


def test_load_implementations_script_list(configuration_loader: Type) -> None:
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

    configuration = yaml.load(text, Loader=configuration_loader)

    assert configuration.implementations[0].name == 'macro'
    assert configuration.implementations[0].script == (
            '#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n')
    assert configuration.implementations[1].name == 'meso'
    assert configuration.implementations[1].script == (
            '#!/bin/bash\n\n/home/test/meso.py')
    assert configuration.implementations[2].name == 'micro'
    assert configuration.implementations[2].script == (
            '/home/test/micro')


def test_dump_implementations(configuration_dumper: Type) -> None:
    implementations = [
            Implementation(
                Reference('macro'),
                '#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n'),
            Implementation(
                Reference('meso'),
                '#!/bin/bash\n\n/home/test/meso.py'),
            Implementation(Reference('micro'), '/home/test/micro')]

    configuration = Configuration(None, None, implementations)

    text = yaml.dump(configuration, Dumper=configuration_dumper)
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


def test_load_resources(configuration_loader: Type) -> None:
    text = (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  macro: 10\n'
            '  micro:\n'
            '    num_cores: 1\n'
            )

    configuration = yaml.load(text, Loader=configuration_loader)

    assert configuration.resources[0].name == 'macro'
    assert configuration.resources[0].num_cores == 10
    assert configuration.resources[1].name == 'micro'
    assert configuration.resources[1].num_cores == 1


def test_dump_resources(configuration_dumper: Type) -> None:
    resources = [
            Resources(Reference('macro'), 10),
            Resources(Reference('micro'), 1)]

    configuration = Configuration(None, None, None, resources)

    text = yaml.dump(configuration, Dumper=configuration_dumper)
    assert text == (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  macro: 10\n'
            '  micro: 1\n'
            )
