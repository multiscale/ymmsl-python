from ymmsl.v0_2 import (
        Identifier, Reference, SettingType, SupportedSetting, SupportedSettings)

import pytest
import yatiml


@pytest.fixture
def supported_settings() -> SupportedSettings:
    settings = {
            'text': 'str',
            'alpha': 'int',
            'beta': 'float',
            'enable.something': 'bool Enables something',
            'things': '[int]',
            'numbers': '[float]',
            'square': '[[float]] Ensure it is not a rectangle'
            }

    return SupportedSettings(settings)


@pytest.fixture
def yaml_text() -> str:
    return (
            'text: str\n'
            'alpha: int\n'
            'beta: float\n'
            'enable.something: bool Enables something\n'
            'things: [int]\n'
            'numbers: [float]\n'
            'square: \'[[float]] Ensure it is not a rectangle\'\n'
            )


def test_create_supported_settings() -> None:
    supset = SupportedSettings()
    assert supset._store == {}


def test_create_supported_settings2(supported_settings: SupportedSettings) -> None:
    s = supported_settings._store
    assert s[Reference('text')].typ == SettingType.STR
    assert s[Reference('text')].description == ''
    assert s[Reference('alpha')].typ == SettingType.INT
    assert s[Reference('beta')].typ == SettingType.FLOAT
    assert s[Reference('enable.something')].typ == SettingType.BOOL
    assert s[Reference('enable.something')].description == 'Enables something'
    assert s[Reference('things')].typ == SettingType.LIST_INT
    assert s[Reference('numbers')].typ == SettingType.LIST_FLOAT
    assert s[Reference('square')].typ == SettingType.LIST_LIST_FLOAT
    assert s[Reference('square')].description == 'Ensure it is not a rectangle'


def test_create_with_bad_name() -> None:
    with pytest.raises(ValueError):
        SupportedSettings({'#test': 'str'})


def test_create_with_bad_type() -> None:
    with pytest.raises(ValueError):
        SupportedSettings({'test': 'nosuchtype'})


def test_equality(supported_settings: SupportedSettings) -> None:
    settings2 = {
            'enable.something': 'bool Enables something',
            'square': '[[float]] Ensure it is not a rectangle',
            'alpha': 'int',
            'beta': 'float',
            'things': '[int]',
            'text': 'str',
            'numbers': '[float]',
            }

    supported_settings2 = SupportedSettings(settings2)
    assert supported_settings == supported_settings2


def test_to_string() -> None:
    supset = SupportedSettings({'a': 'str', 'b': 'int Description'})
    assert str(supset) == 'a: str, b: int'


def test_item_access(supported_settings: SupportedSettings) -> None:
    assert supported_settings['enable.something'].typ == SettingType.BOOL

    supported_settings['gamma'] = SupportedSetting('gamma', '[float]', '')
    assert supported_settings._store[Reference('gamma')].typ == SettingType.LIST_FLOAT
    assert supported_settings[Reference('gamma')].typ == SettingType.LIST_FLOAT

    supported_settings['gamma'] = SupportedSetting('gamma', '[int]', 'description')
    assert supported_settings._store[Reference('gamma')].typ == SettingType.LIST_INT
    assert supported_settings[Reference('gamma')].description == 'description'


def test_iteration(supported_settings: SupportedSettings) -> None:
    for name, setting in supported_settings:
        assert isinstance(name, Reference)
        assert isinstance(setting, SupportedSetting)
        if name == 'text':
            assert setting.typ == SettingType.STR
        if name == 'alpha':
            assert setting.typ == SettingType.INT
        if name == 'beta':
            assert setting.typ == SettingType.FLOAT
        if name == 'enable.something':
            assert setting.typ == SettingType.BOOL
        if name == 'things':
            assert setting.typ == SettingType.LIST_INT
        if name == 'numbers':
            assert setting.typ == SettingType.LIST_FLOAT
        if name == 'square':
            assert setting.typ == SettingType.LIST_LIST_FLOAT


def test_copy(supported_settings: SupportedSettings) -> None:
    supported_settings2 = supported_settings.copy()

    assert supported_settings2 is not supported_settings
    assert supported_settings['text'] == supported_settings2['text']

    supported_settings['text'] = SupportedSetting('text', 'int', '')
    assert supported_settings['text'] != supported_settings2['text']


def test_load(
        supported_settings: SupportedSettings, yaml_text: str) -> None:
    load = yatiml.load_function(
            SupportedSettings, Identifier, Reference, SettingType, SupportedSetting)
    loaded_settings = load(yaml_text)
    assert loaded_settings == supported_settings


def test_dump(supported_settings: SupportedSettings, yaml_text: str) -> None:
    dumps = yatiml.dumps_function(
            SupportedSettings, Identifier, Reference, SettingType, SupportedSetting)
    dumped_settings = dumps(supported_settings)
    assert dumped_settings == yaml_text


def test_load_descriptions() -> None:
    load = yatiml.load_function(
            SupportedSettings, Identifier, Reference, SettingType, SupportedSetting)

    s = load(
            'a: str With inline description\n'
            'b: \'[int] With inline description\'\n'
            'c: \'[[float]] With inline description\'\n'
            'd:\n'
            '  type: str\n'
            '  description: With single-line description\n'
            'e:\n'
            '  type: [float]\n'
            '  description: |-\n'
            '    With multiline\n'
            '    description\n'
            )

    assert s['a'].typ == SettingType.STR
    assert s['a'].description == 'With inline description'

    assert s['b'].typ == SettingType.LIST_INT
    assert s['b'].description == 'With inline description'

    assert s['c'].typ == SettingType.LIST_LIST_FLOAT
    assert s['c'].description == 'With inline description'

    assert s['d'].typ == SettingType.STR
    assert s['d'].description == 'With single-line description'

    assert s['e'].typ == SettingType.LIST_FLOAT
    assert s['e'].description == 'With multiline\ndescription'


def test_dump_descriptions() -> None:
    dumps = yatiml.dumps_function(
            SupportedSettings, Identifier, Reference, SettingType, SupportedSetting)

    supported_settings = SupportedSettings({
        'a': 'str With inline description',
        'b': '[int] With inline description',
        'c': '[[float]] With inline description',
        'd': 'str With single-line description',
        'e': '[float] With multiline\ndescription'})

    text = (
            'a: str With inline description\n'
            'b: \'[int] With inline description\'\n'
            'c: \'[[float]] With inline description\'\n'
            'd: str With single-line description\n'
            'e:\n'
            '  type: [float]\n'
            '  description: |-\n'
            '    With multiline\n'
            '    description\n'
            )

    assert dumps(supported_settings) == text
