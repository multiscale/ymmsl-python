from collections import OrderedDict
from typing_extensions import Type

import pytest
from ruamel import yaml
import yatiml
from ymmsl import (
        Configuration, Identifier, Implementation, Resources, Settings)
from ymmsl import SettingValue     # noqa: F401 # pylint: disable=unused-import
from ymmsl.document import Document


@pytest.fixture
def configuration_loader() -> Type:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [
        Configuration, Document, Identifier, Implementation, Resources,
        Settings])
    yatiml.set_document_type(Loader, Document)
    return Loader


@pytest.fixture
def configuration_dumper() -> Type:
    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [
        Configuration, Document, Identifier, Implementation, Resources,
        Settings])
    return Dumper


def test_configuration() -> None:
    setting_values = OrderedDict()    # type: OrderedDict[str, SettingValue]
    settings = Settings(setting_values)
    config = Configuration(None, settings)
    assert isinstance(config.settings, Settings)
    assert len(config.settings) == 0


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
                Identifier('macro'),
                '#!/bin/bash\n\n/usr/bin/python3 /home/test/macro.py\n'),
            Implementation(
                Identifier('meso'),
                '#!/bin/bash\n\n/home/test/meso.py'),
            Implementation(Identifier('micro'), '/home/test/micro')]

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
            Resources(Identifier('macro'), 10),
            Resources(Identifier('micro'), 1)]

    configuration = Configuration(None, None, None, resources)

    text = yaml.dump(configuration, Dumper=configuration_dumper)
    assert text == (
            'ymmsl_version: v0.1\n'
            'resources:\n'
            '  macro: 10\n'
            '  micro: 1\n'
            )
