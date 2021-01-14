from ymmsl import Identifier, Reference, Settings
from ymmsl import SettingValue  # noqa: F401 # pytest: disable=W0611

from collections import OrderedDict
from typing import cast, List
import yatiml

import pytest


@pytest.fixture
def settings() -> Settings:
    return Settings()


def test_create_settings(settings: Settings) -> None:
    assert settings._store == {}


def test_create_settings2() -> None:
    setting_values = OrderedDict([
        ('submodel._muscle_grain', [0.01, 0.01]),
        ('submodel._muscle_extent', [10.0, 3.0]),
        ('submodel._muscle_timestep', 0.001),
        ('submodel._muscle_total_time', 0.1),
        ('bf.velocity', 0.48),
        ('init.max_depth', 0.11)
    ])  # type: OrderedDict[str, SettingValue]
    settings = Settings(setting_values)
    assert list(settings.ordered_items()[0][0]) == [
        'submodel', '_muscle_grain'
    ]
    assert cast(List[float], settings.ordered_items()[1][1])[1] == 3.0
    assert settings['submodel._muscle_timestep'] == 0.001
    assert list(settings.ordered_items()[4][0]) == ['bf', 'velocity']
    assert settings['init.max_depth'] == 0.11


def test_from_broken_dict() -> None:
    with pytest.raises(ValueError):
        Settings(OrderedDict([
            ('$invalid&', 12)]))


def test_equality(settings: Settings) -> None:
    settings2 = Settings()
    assert settings == settings2
    assert settings2 == settings
    assert not (settings != settings2)
    assert not (settings2 != settings)

    settings1 = Settings()
    settings1._store[Reference('x')] = 12
    settings1._store[Reference('y')] = 'test'
    settings1._store[Reference('z')] = [1.4, 5.3]

    settings2._store[Reference('x')] = 12
    settings2._store[Reference('y')] = 'test'
    settings2._store[Reference('z')] = [1.4, 5.3]

    assert settings1 == settings2
    assert settings2 == settings1

    settings3 = Settings()
    settings3._store[Reference('x')] = 12
    settings3._store[Reference('z')] = [1.4, 5.3]

    assert settings3 != settings1
    assert settings1 != settings3

    settings4 = Settings()
    settings4._store[Reference('x')] = 12
    settings4._store[Reference('y')] = 'test'
    settings4._store[Reference('z')] = [1.41, 5.3]

    assert settings1 != settings4
    assert settings4 != settings1
    assert settings3 != settings4
    assert settings4 != settings3

    assert settings1 != 'test'
    assert not (settings4 == 13)


def test_to_string(settings: Settings) -> None:
    assert str(settings) == 'OrderedDict()'
    settings['test'] = 42
    assert 'test' in str(settings)
    assert '42' in str(settings)


def test_get_item(settings: Settings) -> None:
    settings._store[Reference('test')] = 13
    assert settings[Reference('test')] == 13
    assert settings['test'] == 13


def test_set_item(settings: Settings) -> None:
    settings['param1'] = 3
    assert settings._store[Reference('param1')] == 3

    settings[Reference('param2')] = 4
    assert settings._store[Reference('param2')] == 4


def test_del_item(settings: Settings) -> None:
    settings._store = OrderedDict([(Reference('param1'), 'test'),
                                   (Reference('param2'), 0)])
    del settings['param1']
    assert len(settings._store) == 1
    assert Reference('param1') not in settings._store
    with pytest.raises(KeyError):
        settings['param1']  # pylint: disable=pointless-statement
    assert settings._store[Reference('param2')] == 0


def test_iter(settings: Settings) -> None:
    assert len(settings) == 0
    for setting, value in settings.items():
        assert False    # pragma: no cover

    settings._store = OrderedDict([
            (Reference('test1'), 13),
            (Reference('test2'), 'testing'),
            (Reference('test3'), [3.4, 5.6])])
    assert len(settings) == 3

    for setting in settings:
        assert setting in settings

    for setting, value in settings.items():
        assert (
            setting == 'test1' and value == 13 or
            setting == 'test2' and value == 'testing' or
            setting == 'test3' and value == [3.4, 5.6])


def test_update(settings: Settings) -> None:
    settings1 = Settings()
    settings1['param1'] = 13
    settings1['param2'] = 'testing'

    settings.update(settings1)
    assert len(settings) == 2
    assert settings['param1'] == 13
    assert settings['param2'] == 'testing'

    settings2 = Settings()
    settings2[Reference('param2')] = [[1.0, 2.0], [2.0, 3.0]]
    settings2['param3'] = 3.1415
    settings.update(settings2)
    assert len(settings) == 3
    assert settings['param1'] == 13
    assert settings['param2'] == [[1, 2], [2, 3]]
    assert settings['param3'] == 3.1415

    settings3 = Settings()
    settings3[Reference('param1')] = True
    settings.update(settings3)
    assert len(settings) == 3
    assert settings['param1'] is True
    assert settings['param2'] == [[1, 2], [2, 3]]
    assert settings['param3'] == 3.1415


def test_copy() -> None:
    settings1 = Settings()
    settings1['test'] = 12
    settings1['test2'] = [23.0, 12.0]
    settings1['test3'] = 'test3'

    settings2 = settings1.copy()

    assert settings1 == settings2
    settings2['test'] = 13
    assert settings2['test'] == 13
    assert settings1['test'] == 12

    cast(List[float], settings2['test2'])[0] = 24.0
    assert settings2['test2'] == [24.0, 12.0]
    assert settings1['test2'] == [24.0, 12.0]


def test_as_ordered_dict(settings: Settings) -> None:
    settings._store = OrderedDict([
            (Reference('test1'), 12),
            (Reference('test2'), '12'),
            (Reference('test3'), 'testing'),
            (Reference('test4'), [12.3, 45.6])])
    settings_dict = settings.as_ordered_dict()
    assert settings_dict['test1'] == 12
    assert settings_dict['test2'] == '12'
    assert settings_dict['test3'] == 'testing'
    assert settings_dict['test4'] == [12.3, 45.6]

    for i, (key, _) in enumerate(settings_dict.items()):
        assert key == 'test{}'.format(i + 1)


def test_load_settings() -> None:
    load_settings = yatiml.load_function(Settings, Identifier, Reference)

    text = ('domain1._muscle_grain: [0.01]\n'
            'domain1._muscle_extent: [1.5]\n'
            'submodel1._muscle_timestep: 0.001\n'
            'submodel1._muscle_total_time: 100.0\n'
            'test_str: value\n'
            'test_int: 13\n'
            'test_bool: true\n'
            'test_list: [12.3, 1.3]\n')

    settings = load_settings(text)
    assert len(settings) == 8
    assert str(settings.ordered_items()[0][0]) == 'domain1._muscle_grain'
    assert cast(List[float], settings['domain1._muscle_grain'])[0] == 0.01
    assert settings['submodel1._muscle_total_time'] == 100.0

    assert str(settings.ordered_items()[4][0]) == 'test_str'
    assert ([str(s[0]) for s in settings.ordered_items()]
            == ['domain1._muscle_grain', 'domain1._muscle_extent',
                'submodel1._muscle_timestep', 'submodel1._muscle_total_time',
                'test_str', 'test_int', 'test_bool', 'test_list'])
    assert settings['test_bool'] is True
    assert settings['test_list'] == [12.3, 1.3]


def test_dump_settings() -> None:
    dump_settings = yatiml.dumps_function(Identifier, Reference, Settings)

    settings = Settings(OrderedDict([
            ('domain1._muscle_grain', [0.01]),
            ('domain1._muscle_extent', [1.5]),
            ('submodel1._muscle_timestep', 0.001),
            ('submodel1._muscle_total_time', 100.0),
            ('test_str', 'value'),
            ('test_int', 12),
            ('test_bool', True),
            ('test_list', [12.3, 1.3])]))

    text = dump_settings(settings)
    assert text == ('domain1._muscle_grain: [0.01]\n'
                    'domain1._muscle_extent: [1.5]\n'
                    'submodel1._muscle_timestep: 0.001\n'
                    'submodel1._muscle_total_time: 100.0\n'
                    'test_str: value\n'
                    'test_int: 12\n'
                    'test_bool: true\n'
                    'test_list: [12.3, 1.3]\n')
