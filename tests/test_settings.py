#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from ymmsl.settings import Setting, Settings
from ymmsl.identity import Identifier, Reference

from typing import cast, List
import yatiml
from ruamel import yaml


def test_setting() -> None:
    setting = Setting('submodel.test', 12)
    assert str(setting.parameter) == 'submodel.test'
    assert isinstance(setting.value, int)
    assert setting.value == 12

    setting = Setting('par1', 'test')
    assert str(setting.parameter) == 'par1'
    assert isinstance(setting.value, str)
    assert setting.value == 'test'

    setting = Setting('submodel.par1[3]', 3.14159)
    assert str(setting.parameter) == 'submodel.par1[3]'
    assert isinstance(setting.value, float)
    assert setting.value == 3.14159

    setting = Setting('extra_accuracy', True)
    assert str(setting.parameter) == 'extra_accuracy'
    assert isinstance(setting.value, bool)
    assert setting.value is True

    setting = Setting('submodel.par1', [1.0, 2.0, 3.0])
    assert str(setting.parameter) == 'submodel.par1'
    assert isinstance(setting.value, list)
    assert len(setting.value) == 3
    assert setting.value == [1.0, 2.0, 3.0]

    setting = Setting('submodel.par1', [[1.0, 2.0], [3.0, 4.0]])
    assert str(setting.parameter) == 'submodel.par1'
    assert isinstance(setting.value, list)
    assert len(setting.value) == 2
    assert setting.value[0] == [1.0, 2.0]
    assert setting.value[1] == [3.0, 4.0]


def test_settings() -> None:
    parameter_values = [
        Setting('submodel._muscle_grain', [0.01, 0.01]),
        Setting('submodel._muscle_extent', [10.0, 3.0]),
        Setting('submodel._muscle_timestep', 0.001),
        Setting('submodel._muscle_total_time', 0.1),
        Setting('bf.velocity', 0.48),
        Setting('init.max_depth', 0.11)
    ]
    settings = Settings(parameter_values)
    assert list(settings.parameter_values[0].parameter) == [
        'submodel', '_muscle_grain'
    ]
    assert cast(List[float], settings.parameter_values[1].value)[1] == 3.0
    assert settings.parameter_values[2].value == 0.001
    assert list(settings.parameter_values[4].parameter) == ['bf', 'velocity']
    assert settings.parameter_values[5].value == 0.11


def test_settings_from_dict() -> None:
    settings = Settings({
        'submodel._muscle_grain': [0.01, 0.01],
        'submodel._muscle_extent': [10.0, 3.0],
        'submodel._muscle_timestep': 0.001,
        'submodel._muscle_total_time': 0.1,
        'bf.velocity': 0.48,
        'init.max_depth': 0.11})

    assert ['submodel', '_muscle_grain'] in [
            list(s.parameter) for s in settings.parameter_values]

    assert ('submodel._muscle_extent', [10.0, 3.0]) in [
            (str(s.parameter), s.value) for s in settings.parameter_values]

    assert ('submodel._muscle_timestep', 0.001) in [
            (str(s.parameter), s.value) for s in settings.parameter_values]


def test_load_settings() -> None:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [Identifier, Reference, Setting, Settings])
    yatiml.set_document_type(Loader, Settings)

    text = ('parameter_values:\n'
            '  domain1._muscle_grain: [0.01]\n'
            '  domain1._muscle_extent: [1.5]\n'
            '  submodel1._muscle_timestep: 0.001\n'
            '  submodel1._muscle_total_time: 100.0\n'
            '  test_str: value\n'
            '  test_int: 13\n'
            '  test_bool: true\n'
            '  test_list: [12.3, 1.3]\n')

    settings = yaml.load(text, Loader=Loader)
    assert len(settings.parameter_values) == 8
    assert str(settings.parameter_values[0].parameter) == 'domain1._muscle_grain'
    assert settings.parameter_values[0].value[0] == 0.01
    assert settings.parameter_values[3].value == 100.0

    assert str(settings.parameter_values[4].parameter) == 'test_str'
    assert ([str(s.parameter) for s in settings.parameter_values]
            == ['domain1._muscle_grain', 'domain1._muscle_extent',
                'submodel1._muscle_timestep', 'submodel1._muscle_total_time',
                'test_str', 'test_int', 'test_bool', 'test_list'])
    assert settings.parameter_values[6].value is True
    assert settings.parameter_values[7].value == [12.3, 1.3]


def test_dump_settings() -> None:
    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [Identifier, Reference, Setting, Settings])

    parameter_values = [Setting('domain1._muscle_grain', [0.01]),
                        Setting('domain1._muscle_extent', [1.5]),
                        Setting('submodel1._muscle_timestep', 0.001),
                        Setting('submodel1._muscle_total_time', 100.0),
                        Setting('test_str', 'value'),
                        Setting('test_int', 12),
                        Setting('test_bool', True),
                        Setting('test_list', [12.3, 1.3])]
    settings = Settings(parameter_values)

    text = yaml.dump(settings, Dumper=Dumper)
    assert text == ('parameter_values:\n'
                    '  domain1._muscle_grain: [0.01]\n'
                    '  domain1._muscle_extent: [1.5]\n'
                    '  submodel1._muscle_timestep: 0.001\n'
                    '  submodel1._muscle_total_time: 100.0\n'
                    '  test_str: value\n'
                    '  test_int: 12\n'
                    '  test_bool: true\n'
                    '  test_list: [12.3, 1.3]\n')
