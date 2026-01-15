from ymmsl.v0_2 import Identifier, Reference, SettingType, SupportedSettings

import logging
from typing import Any

import pytest
import yatiml


@pytest.fixture
def supported_settings() -> SupportedSettings:
    settings = {
            'text': 'str',
            'alpha': 'int',
            'beta': 'float',
            'enable.something': 'bool',
            'things': '[int]',
            'numbers': '[float]',
            'square': '[[float]]'
            }

    return SupportedSettings(settings)


@pytest.fixture
def yaml_text() -> str:
    return (
            'text: str\n'
            'alpha: int\n'
            'beta: float\n'
            'enable.something: bool\n'
            'things: [int]\n'
            'numbers: [float]\n'
            'square: [[float]]\n'
            )


def test_create_supported_settings() -> None:
    supset = SupportedSettings()
    assert supset._store == {}


def test_create_supported_settings2(supported_settings: SupportedSettings) -> None:
    assert supported_settings._store[Reference('text')] == SettingType.STR
    assert supported_settings._store[Reference('alpha')] == SettingType.INT
    assert supported_settings._store[Reference('beta')] == SettingType.FLOAT
    assert supported_settings._store[Reference('enable.something')] == SettingType.BOOL
    assert supported_settings._store[Reference('things')] == SettingType.LIST_INT
    assert supported_settings._store[Reference('numbers')] == SettingType.LIST_FLOAT
    assert supported_settings._store[Reference('square')] == SettingType.LIST_LIST_FLOAT


def test_create_with_bad_name() -> None:
    with pytest.raises(ValueError):
        SupportedSettings({'#test': 'str'})


def test_create_with_bad_type() -> None:
    with pytest.raises(ValueError):
        SupportedSettings({'test': 'nosuchtype'})


def test_equality(supported_settings: SupportedSettings) -> None:
    settings2 = {
            'enable.something': 'bool',
            'square': '[[float]]',
            'alpha': 'int',
            'beta': 'float',
            'things': '[int]',
            'text': 'str',
            'numbers': '[float]',
            }

    supported_settings2 = SupportedSettings(settings2)
    assert supported_settings == supported_settings2


def test_to_string() -> None:
    supset = SupportedSettings({'a': 'str', 'b': 'int'})
    assert str(supset) == "{'a': 'str', 'b': 'int'}"


def test_item_access(supported_settings: SupportedSettings) -> None:
    assert supported_settings['enable.something'] == SettingType.BOOL

    supported_settings['gamma'] = SettingType.LIST_FLOAT
    assert supported_settings._store[Reference('gamma')] == SettingType.LIST_FLOAT
    assert supported_settings[Reference('gamma')] == SettingType.LIST_FLOAT

    supported_settings['gamma'] = '[int]'
    assert supported_settings._store[Reference('gamma')] == SettingType.LIST_INT
    assert supported_settings[Reference('gamma')] == SettingType.LIST_INT


def test_iteration(supported_settings: SupportedSettings) -> None:
    for setting, typ in supported_settings:
        assert isinstance(setting, Reference)
        assert isinstance(typ, SettingType)
        if setting == 'text':
            assert typ == SettingType.STR
        if setting == 'alpha':
            assert typ == SettingType.INT
        if setting == 'beta':
            assert typ == SettingType.FLOAT
        if setting == 'enable.something':
            assert typ == SettingType.BOOL
        if setting == 'things':
            assert typ == SettingType.LIST_INT
        if setting == 'numbers':
            assert typ == SettingType.LIST_FLOAT
        if setting == 'square':
            assert typ == SettingType.LIST_LIST_FLOAT


def test_ordered_items(supported_settings: SupportedSettings) -> None:
    assert supported_settings.ordered_items() == [
            (Reference('text'), SettingType.STR),
            (Reference('alpha'), SettingType.INT),
            (Reference('beta'), SettingType.FLOAT),
            (Reference('enable.something'), SettingType.BOOL),
            (Reference('things'), SettingType.LIST_INT),
            (Reference('numbers'), SettingType.LIST_FLOAT),
            (Reference('square'), SettingType.LIST_LIST_FLOAT)]


def test_copy(supported_settings: SupportedSettings) -> None:
    supported_settings2 = supported_settings.copy()

    assert supported_settings2 is not supported_settings
    assert supported_settings['text'] == supported_settings2['text']

    supported_settings['text'] = SettingType.INT
    assert supported_settings['text'] != supported_settings2['text']


def test_as_ordered_dict(supported_settings: SupportedSettings) -> None:
    assert supported_settings.as_ordered_dict() == {
            'text': 'str',
            'alpha': 'int',
            'beta': 'float',
            'enable.something': 'bool',
            'things': '[int]',
            'numbers': '[float]',
            'square': '[[float]]'}


def test_load(
        supported_settings: SupportedSettings, yaml_text: str, caplog: Any) -> None:
    caplog.set_level(logging.DEBUG)
    load = yatiml.load_function(SupportedSettings, Identifier, Reference, SettingType)
    loaded_settings = load(yaml_text)
    assert loaded_settings == supported_settings


def test_dump(supported_settings: SupportedSettings, yaml_text: str) -> None:
    dumps = yatiml.dumps_function(SupportedSettings, Identifier, Reference, SettingType)
    dumped_settings = dumps(supported_settings)
    assert dumped_settings == yaml_text
