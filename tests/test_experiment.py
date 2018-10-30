#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from ymmsl.experiment import Experiment, ScaleSettings, Setting
from ymmsl.identity import Identifier, Reference

import yatiml
from ruamel import yaml


def test_scale_value() -> None:
    reference = Reference.from_string('submodel.muscle.x')
    scale = ScaleSettings(reference, 0.01, 3.0)
    assert str(scale.scale) == 'submodel.muscle.x'
    assert scale.grain == 0.01
    assert scale.extent == 3.0


def test_setting() -> None:
    setting = Setting(Reference.from_string('submodel.test'), 12)
    assert str(setting.parameter) == 'submodel.test'
    assert isinstance(setting.value, int)
    assert setting.value == 12

    setting = Setting(Reference.from_string('par1'), 'test')
    assert str(setting.parameter) == 'par1'
    assert isinstance(setting.value, str)
    assert setting.value == 'test'

    setting = Setting(Reference.from_string('submodel.par1[3]'), 3.14159)
    assert str(setting.parameter) == 'submodel.par1[3]'
    assert isinstance(setting.value, float)
    assert setting.value == 3.14159

    setting = Setting(Reference.from_string('submodel.par1'), [1.0, 2.0, 3.0])
    assert str(setting.parameter) == 'submodel.par1'
    assert isinstance(setting.value, list)
    assert len(setting.value) == 3
    assert setting.value == [1.0, 2.0, 3.0]

    setting = Setting(Reference.from_string('submodel.par1'), [[1.0, 2.0], [3.0, 4.0]])
    assert str(setting.parameter) == 'submodel.par1'
    assert isinstance(setting.value, list)
    assert len(setting.value) == 2
    assert setting.value[0] == [1.0, 2.0]
    assert setting.value[1] == [3.0, 4.0]


def test_experiment() -> None:
    model = Reference.from_string('isr2d')
    x = ScaleSettings(Reference.from_string('submodel.muscle.x'), 0.01, 10.0)
    y = ScaleSettings(Reference.from_string('submodel.muscle.y'), 0.01, 3.0)
    t = ScaleSettings(Reference.from_string('submodel.muscle.t'), 0.001, 0.1)
    parameter_values = [
        Setting(Reference.from_string('bf.velocity'), 0.48),
        Setting(Reference.from_string('init.max_depth'), 0.11)
    ]
    experiment = Experiment(model, [x, y, t], parameter_values)
    assert str(experiment.model) == 'isr2d'
    assert experiment.scales[0].scale.parts == [
        'submodel', 'muscle', 'x'
    ]
    assert experiment.scales[1].extent == 3.0
    assert experiment.scales[2].grain == 0.001
    assert experiment.parameter_values[0].parameter.parts == ['bf', 'velocity']
    assert experiment.parameter_values[1].value == 0.11


def test_load_experiment() -> None:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [Experiment, Identifier, Reference,
                                  ScaleSettings, Setting])
    yatiml.set_document_type(Loader, Experiment)

    text = ('model: test_model\n'
            'scales:\n'
            '  domain1.x:\n'
            '    grain: 0.01\n'
            '    extent: 1.5\n'
            '  submodel1.t:\n'
            '    grain: 0.001\n'
            '    extent: 100.0\n'
            'parameter_values:\n'
            '  test_str: value\n'
            '  test_int: 13\n'
            '  test_list: [12.3, 1.3]\n')

    experiment = yaml.load(text, Loader=Loader)
    assert str(experiment.model) == 'test_model'
    assert len(experiment.scales) == 2
    assert str(experiment.scales[0].scale) == 'domain1.x'
    assert experiment.scales[0].grain == 0.01
    assert experiment.scales[1].extent == 100.0

    assert str(experiment.parameter_values[0].parameter) == 'test_str'
    assert ([str(s.parameter) for s in experiment.parameter_values]
            == ['test_str', 'test_int', 'test_list'])
    assert experiment.parameter_values[2].value == [12.3, 1.3]


def test_dump_experiment() -> None:
    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [Experiment, Identifier, Reference,
                                  ScaleSettings, Setting])

    ref = Reference.from_string

    model = ref('test_model')
    scales = [ScaleSettings(ref('domain1.x'), 0.01, 1.5),
              ScaleSettings(ref('submodel1.t'), 0.001, 100.0)]
    parameter_values = [Setting(ref('test_str'), 'value'),
                        Setting(ref('test_int'), 12),
                        Setting(ref('test_list'), [12.3, 1.3])]
    experiment = Experiment(model, scales, parameter_values)

    text = yaml.dump(experiment, Dumper=Dumper)
    print(text)
    assert text == ('model: test_model\n'
                    'scales:\n'
                    '  domain1.x:\n'
                    '    grain: 0.01\n'
                    '    extent: 1.5\n'
                    '  submodel1.t:\n'
                    '    grain: 0.001\n'
                    '    extent: 100.0\n'
                    'parameter_values:\n'
                    '  test_str: value\n'
                    '  test_int: 12\n'
                    '  test_list:\n'
                    '  - 12.3\n'
                    '  - 1.3\n')
