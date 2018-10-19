#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from typing import Dict, List, Union

from ymmsl import ymmsl

import pytest


def test_identifier() -> None:
    part = ymmsl.Identifier('testing')
    assert str(part) == 'testing'

    part = ymmsl.Identifier('CapiTaLs')
    assert str(part) == 'CapiTaLs'

    part = ymmsl.Identifier('under_score')
    assert str(part) == 'under_score'

    part = ymmsl.Identifier('_underscore')
    assert str(part) == '_underscore'

    part = ymmsl.Identifier('digits123')
    assert str(part) == 'digits123'

    with pytest.raises(ValueError):
        ymmsl.Identifier('1initialdigit')

    with pytest.raises(ValueError):
        ymmsl.Identifier('test.period')

    with pytest.raises(ValueError):
        ymmsl.Identifier('test-hyphen')

    with pytest.raises(ValueError):
        ymmsl.Identifier('test space')

    with pytest.raises(ValueError):
        ymmsl.Identifier('test/slash')


def test_compute_element_identifier() -> None:
    test_id = ymmsl.ComputeElementIdentifier('test')
    assert test_id.base == 'test'
    assert len(test_id.indexes) == 0
    assert str(test_id) == 'test'

    test_id = ymmsl.ComputeElementIdentifier('test[2]')
    assert test_id.base == 'test'
    assert test_id.indexes == [2]
    assert str(test_id) == 'test[2]'

    test_id = ymmsl.ComputeElementIdentifier('test[2][4][1]')
    assert test_id.base == 'test'
    assert test_id.indexes == [2, 4, 1]
    assert str(test_id) == 'test[2][4][1]'

    with pytest.raises(ValueError):
        ymmsl.ComputeElementIdentifier('test[1]test2')

    with pytest.raises(ValueError):
        ymmsl.ComputeElementIdentifier('[4]test')

    with pytest.raises(ValueError):
        ymmsl.ComputeElementIdentifier('test[x]')


def test_reference() -> None:
    test_ref = ymmsl.Reference('_testing')
    assert str(test_ref) == '_testing'
    assert len(test_ref.parts) == 1
    assert isinstance(test_ref.parts[0], ymmsl.Identifier)
    assert str(test_ref.parts[0]) == '_testing'

    with pytest.raises(ValueError):
        ymmsl.Reference('1test')

    test_ref = ymmsl.Reference('test.testing')
    assert str(test_ref) == 'test.testing'
    assert len(test_ref.parts) == 2
    assert isinstance(test_ref.parts[0], ymmsl.Identifier)
    assert str(test_ref.parts[0]) == 'test'
    assert isinstance(test_ref.parts[1], ymmsl.Identifier)
    assert str(test_ref.parts[1]) == 'testing'

    test_ref = ymmsl.Reference('test[12]')
    assert str(test_ref) == 'test[12]'
    assert len(test_ref.parts) == 2
    assert isinstance(test_ref.parts[0], ymmsl.Identifier)
    assert str(test_ref.parts[0]) == 'test'
    assert isinstance(test_ref.parts[1], int)
    assert test_ref.parts[1] == 12

    test_ref = ymmsl.Reference('test[12].testing.ok.index[3][5]')
    assert str(test_ref) == 'test[12].testing.ok.index[3][5]'
    assert len(test_ref.parts) == 7
    assert isinstance(test_ref.parts[0], ymmsl.Identifier)
    assert str(test_ref.parts[0]) == 'test'
    assert isinstance(test_ref.parts[1], int)
    assert test_ref.parts[1] == 12
    assert isinstance(test_ref.parts[2], ymmsl.Identifier)
    assert str(test_ref.parts[2]) == 'testing'
    assert isinstance(test_ref.parts[3], ymmsl.Identifier)
    assert str(test_ref.parts[3]) == 'ok'
    assert isinstance(test_ref.parts[4], ymmsl.Identifier)
    assert str(test_ref.parts[4]) == 'index'
    assert isinstance(test_ref.parts[5], int)
    assert test_ref.parts[5] == 3
    assert isinstance(test_ref.parts[6], int)
    assert test_ref.parts[6] == 5

    with pytest.raises(ValueError):
        ymmsl.Reference('ua",.u8[')

    with pytest.raises(ValueError):
        ymmsl.Reference('test[4')

    with pytest.raises(ValueError):
        ymmsl.Reference('test4]')

    with pytest.raises(ValueError):
        ymmsl.Reference('test[_t]')

    with pytest.raises(ValueError):
        ymmsl.Reference('testing_{3}')

    with pytest.raises(ValueError):
        ymmsl.Reference('test.(x)')

def test_scale_value() -> None:
    reference = ymmsl.Reference('submodel.muscle.x')
    scale = ymmsl.ScaleValues(reference, 0.01, 3.0)
    assert str(scale.scale) == 'submodel.muscle.x'
    assert scale.grain == 0.01
    assert scale.extent == 3.0


def test_setting() -> None:
    setting = ymmsl.Setting(ymmsl.Reference('submodel.test'), 12)
    assert str(setting.parameter) == 'submodel.test'
    assert isinstance(setting.value, int)
    assert setting.value == 12

    setting = ymmsl.Setting(ymmsl.Reference('par1'), 'test')
    assert str(setting.parameter) == 'par1'
    assert isinstance(setting.value, str)
    assert setting.value == 'test'

    setting = ymmsl.Setting(ymmsl.Reference('submodel.par1[3]'), 3.14159)
    assert str(setting.parameter) == 'submodel.par1[3]'
    assert isinstance(setting.value, float)
    assert setting.value == 3.14159

    setting = ymmsl.Setting(ymmsl.Reference('submodel.par1'), [1.0, 2.0, 3.0])
    assert str(setting.parameter) == 'submodel.par1'
    assert isinstance(setting.value, list)
    assert len(setting.value) == 3
    assert setting.value == [1.0, 2.0, 3.0]

    setting = ymmsl.Setting(ymmsl.Reference('submodel.par1'), [[1.0, 2.0], [3.0, 4.0]])
    assert str(setting.parameter) == 'submodel.par1'
    assert isinstance(setting.value, list)
    assert len(setting.value) == 2
    assert setting.value[0] == [1.0, 2.0]
    assert setting.value[1] == [3.0, 4.0]


def test_experiment() -> None:
    model = ymmsl.Reference('isr2d')
    x = ymmsl.ScaleValues(ymmsl.Reference('submodel.muscle.x'), 0.01, 10.0)
    y = ymmsl.ScaleValues(ymmsl.Reference('submodel.muscle.y'), 0.01, 3.0)
    t = ymmsl.ScaleValues(ymmsl.Reference('submodel.muscle.t'), 0.001, 0.1)
    parameter_values = [
        ymmsl.Setting(ymmsl.Reference('bf.velocity'), 0.48),
        ymmsl.Setting(ymmsl.Reference('init.max_depth'), 0.11)
    ]
    experiment = ymmsl.Experiment(model, [x, y, t], parameter_values)
    assert str(experiment.model) == 'isr2d'
    assert experiment.scale_values[0].scale.parts == [
        'submodel', 'muscle', 'x'
    ]
    assert experiment.scale_values[1].extent == 3.0
    assert experiment.scale_values[2].grain == 0.001
    assert experiment.parameter_values[0].parameter.parts == ['bf', 'velocity']
    assert experiment.parameter_values[1].value == 0.11


def test_ymmsl() -> None:
    model = ymmsl.Reference('isr2d')
    parameter_values = []  # type: List[ymmsl.Setting]
    experiment = ymmsl.Experiment(model, [], parameter_values)
    doc = ymmsl.Ymmsl(experiment)
    assert isinstance(doc.experiment.model, ymmsl.Reference)
    assert str(doc.experiment.model) == 'isr2d'
    assert doc.experiment.model.parts[0] == 'isr2d'
    assert doc.experiment.parameter_values == []
    assert doc.experiment.scale_values == []


def test_loader() -> None:
    pass


def test_dumper() -> None:
    pass
