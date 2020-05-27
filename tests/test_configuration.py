from collections import OrderedDict
from typing_extensions import Type

import pytest
from ruamel import yaml
import yatiml
from ymmsl import Configuration, Settings
from ymmsl import SettingValue     # noqa: F401 # pylint: disable=unused-import
from ymmsl.document import Document


@pytest.fixture
def configuration_loader() -> Type:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [Configuration, Document, Settings])
    yatiml.set_document_type(Loader, Document)
    return Loader


@pytest.fixture
def configuration_dumper() -> Type:
    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [Configuration, Document, Settings])
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


def test_load_no_settings(configuration_loader: Type) -> None:
    text = (
            'ymmsl_version: v0.1\n'
            )

    configuration = yaml.load(text, Loader=configuration_loader)

    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0


def test_dump_empty_settings(configuration_dumper: Type) -> None:
    configuration = Configuration(None, Settings())
    text = yaml.dump(configuration, Dumper=configuration_dumper)

    assert text == 'ymmsl_version: v0.1\n'
