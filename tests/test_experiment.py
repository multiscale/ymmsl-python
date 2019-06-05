#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from ymmsl.experiment import Experiment, Setting
from ymmsl.identity import Identifier, Reference

from typing import cast, List
import yatiml
from ruamel import yaml


def test_setting() -> None:
    setting = Setting(Reference('submodel.test'), 12)
    assert str(setting.parameter) == 'submodel.test'
    assert isinstance(setting.value, int)
    assert setting.value == 12

    setting = Setting(Reference('par1'), 'test')
    assert str(setting.parameter) == 'par1'
    assert isinstance(setting.value, str)
    assert setting.value == 'test'

    setting = Setting(Reference('submodel.par1[3]'), 3.14159)
    assert str(setting.parameter) == 'submodel.par1[3]'
    assert isinstance(setting.value, float)
    assert setting.value == 3.14159

    setting = Setting(Reference('extra_accuracy'), True)
    assert str(setting.parameter) == 'extra_accuracy'
    assert isinstance(setting.value, bool)
    assert setting.value is True

    setting = Setting(Reference('submodel.par1'), [1.0, 2.0, 3.0])
    assert str(setting.parameter) == 'submodel.par1'
    assert isinstance(setting.value, list)
    assert len(setting.value) == 3
    assert setting.value == [1.0, 2.0, 3.0]

    setting = Setting(Reference('submodel.par1'), [[1.0, 2.0], [3.0, 4.0]])
    assert str(setting.parameter) == 'submodel.par1'
    assert isinstance(setting.value, list)
    assert len(setting.value) == 2
    assert setting.value[0] == [1.0, 2.0]
    assert setting.value[1] == [3.0, 4.0]


def test_experiment() -> None:
    model = Reference('isr2d')
    parameter_values = [
        Setting(Reference('submodel._muscle_grain'), [0.01, 0.01]),
        Setting(Reference('submodel._muscle_extent'), [10.0, 3.0]),
        Setting(Reference('submodel._muscle_timestep'), 0.001),
        Setting(Reference('submodel._muscle_total_time'), 0.1),
        Setting(Reference('bf.velocity'), 0.48),
        Setting(Reference('init.max_depth'), 0.11)
    ]
    experiment = Experiment(model, parameter_values)
    assert str(experiment.model) == 'isr2d'
    assert list(experiment.parameter_values[0].parameter) == [
        'submodel', '_muscle_grain'
    ]
    assert cast(List[float], experiment.parameter_values[1].value)[1] == 3.0
    assert experiment.parameter_values[2].value == 0.001
    assert list(experiment.parameter_values[4].parameter) == ['bf', 'velocity']
    assert experiment.parameter_values[5].value == 0.11


def test_load_experiment() -> None:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [Experiment, Identifier, Reference, Setting])
    yatiml.set_document_type(Loader, Experiment)

    text = ('model: test_model\n'
            'parameter_values:\n'
            '  domain1._muscle_grain: [0.01]\n'
            '  domain1._muscle_extent: [1.5]\n'
            '  submodel1._muscle_timestep: 0.001\n'
            '  submodel1._muscle_total_time: 100.0\n'
            '  test_str: value\n'
            '  test_int: 13\n'
            '  test_bool: true\n'
            '  test_list: [12.3, 1.3]\n')

    experiment = yaml.load(text, Loader=Loader)
    assert str(experiment.model) == 'test_model'
    assert len(experiment.parameter_values) == 8
    assert str(experiment.parameter_values[0].parameter) == 'domain1._muscle_grain'
    assert experiment.parameter_values[0].value[0] == 0.01
    assert experiment.parameter_values[3].value == 100.0

    assert str(experiment.parameter_values[4].parameter) == 'test_str'
    assert ([str(s.parameter) for s in experiment.parameter_values]
            == ['domain1._muscle_grain', 'domain1._muscle_extent',
                'submodel1._muscle_timestep', 'submodel1._muscle_total_time',
                'test_str', 'test_int', 'test_bool', 'test_list'])
    assert experiment.parameter_values[6].value is True
    assert experiment.parameter_values[7].value == [12.3, 1.3]


def test_dump_experiment() -> None:
    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [Experiment, Identifier, Reference, Setting])

    ref = Reference

    model = ref('test_model')
    parameter_values = [Setting(ref('domain1._muscle_grain'), [0.01]),
                        Setting(ref('domain1._muscle_extent'), [1.5]),
                        Setting(ref('submodel1._muscle_timestep'), 0.001),
                        Setting(ref('submodel1._muscle_total_time'), 100.0),
                        Setting(ref('test_str'), 'value'),
                        Setting(ref('test_int'), 12),
                        Setting(ref('test_bool'), True),
                        Setting(ref('test_list'), [12.3, 1.3])]
    experiment = Experiment(model, parameter_values)

    text = yaml.dump(experiment, Dumper=Dumper)
    print(text)
    assert text == ('model: test_model\n'
                    'parameter_values:\n'
                    '  domain1._muscle_grain:\n'
                    '  - 0.01\n'
                    '  domain1._muscle_extent:\n'
                    '  - 1.5\n'
                    '  submodel1._muscle_timestep: 0.001\n'
                    '  submodel1._muscle_total_time: 100.0\n'
                    '  test_str: value\n'
                    '  test_int: 12\n'
                    '  test_bool: true\n'
                    '  test_list:\n'
                    '  - 12.3\n'
                    '  - 1.3\n')
