#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

import logging
from typing import Any, Dict, List, Union

from ymmsl import (ComputeElementDecl, Conduit, Experiment, Identifier,
                   Reference, ScaleSettings, Setting, Simulation, Ymmsl)

import pytest
import yatiml
import ymmsl
from ruamel import yaml


def test_identifier() -> None:
    part = Identifier('testing')
    assert str(part) == 'testing'

    part = Identifier('CapiTaLs')
    assert str(part) == 'CapiTaLs'

    part = Identifier('under_score')
    assert str(part) == 'under_score'

    part = Identifier('_underscore')
    assert str(part) == '_underscore'

    part = Identifier('digits123')
    assert str(part) == 'digits123'

    with pytest.raises(ValueError):
        Identifier('1initialdigit')

    with pytest.raises(ValueError):
        Identifier('test.period')

    with pytest.raises(ValueError):
        Identifier('test-hyphen')

    with pytest.raises(ValueError):
        Identifier('test space')

    with pytest.raises(ValueError):
        Identifier('test/slash')


def test_reference() -> None:
    test_ref = Reference.from_string('_testing')
    assert str(test_ref) == '_testing'
    assert len(test_ref.parts) == 1
    assert isinstance(test_ref.parts[0], Identifier)
    assert str(test_ref.parts[0]) == '_testing'

    with pytest.raises(ValueError):
        Reference.from_string('1test')

    test_ref = Reference.from_string('test.testing')
    assert len(test_ref.parts) == 2
    assert isinstance(test_ref.parts[0], Identifier)
    assert str(test_ref.parts[0]) == 'test'
    assert isinstance(test_ref.parts[1], Identifier)
    assert str(test_ref.parts[1]) == 'testing'
    assert str(test_ref) == 'test.testing'

    test_ref = Reference.from_string('test[12]')
    assert len(test_ref.parts) == 2
    assert isinstance(test_ref.parts[0], Identifier)
    assert str(test_ref.parts[0]) == 'test'
    assert isinstance(test_ref.parts[1], int)
    assert test_ref.parts[1] == 12
    assert str(test_ref) == 'test[12]'

    test_ref = Reference.from_string('test[12].testing.ok.index[3][5]')
    assert len(test_ref.parts) == 7
    assert isinstance(test_ref.parts[0], Identifier)
    assert str(test_ref.parts[0]) == 'test'
    assert isinstance(test_ref.parts[1], int)
    assert test_ref.parts[1] == 12
    assert isinstance(test_ref.parts[2], Identifier)
    assert str(test_ref.parts[2]) == 'testing'
    assert isinstance(test_ref.parts[3], Identifier)
    assert str(test_ref.parts[3]) == 'ok'
    assert isinstance(test_ref.parts[4], Identifier)
    assert str(test_ref.parts[4]) == 'index'
    assert isinstance(test_ref.parts[5], int)
    assert test_ref.parts[5] == 3
    assert isinstance(test_ref.parts[6], int)
    assert test_ref.parts[6] == 5
    assert str(test_ref) == 'test[12].testing.ok.index[3][5]'

    with pytest.raises(ValueError):
        Reference.from_string('ua",.u8[')

    with pytest.raises(ValueError):
        Reference.from_string('test[4')

    with pytest.raises(ValueError):
        Reference.from_string('test4]')

    with pytest.raises(ValueError):
        Reference.from_string('test[_t]')

    with pytest.raises(ValueError):
        Reference.from_string('testing_{3}')

    with pytest.raises(ValueError):
        Reference.from_string('test.(x)')


def test_compute_element_declaration() -> None:
    test_decl = ComputeElementDecl(
            Identifier('test'), Reference.from_string('ns.model'))
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns.model'
    assert test_decl.count == 1
    assert str(test_decl) == 'test[1]'

    test_decl = ComputeElementDecl(
            Identifier('test'), Reference.from_string('ns2.model2'), 2)
    assert isinstance(test_decl.name, Identifier)
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns2.model2'
    assert test_decl.count == 2
    assert str(test_decl) == 'test[2]'

    with pytest.raises(ValueError):
        test_decl = ComputeElementDecl(
                Identifier('test'), Reference.from_string('ns2.model2[1]'))


def test_conduit() -> None:
    test_ref = Reference.from_string('submodel1.port1')
    test_ref2 = Reference.from_string('submodel2.port2')
    test_conduit = Conduit(test_ref, test_ref2)
    assert str(test_conduit.sender.parts[0]) == 'submodel1'
    assert str(test_conduit.sender.parts[1]) == 'port1'
    assert str(test_conduit.receiver.parts[0]) == 'submodel2'
    assert str(test_conduit.receiver.parts[1]) == 'port2'

    assert str(test_conduit.sending_compute_element()) == 'submodel1'
    assert str(test_conduit.sending_port()) == 'port1'
    assert str(test_conduit.receiving_compute_element()) == 'submodel2'
    assert str(test_conduit.receiving_port()) == 'port2'


def test_simulation() -> None:
    macro = ComputeElementDecl(
            Identifier('macro'), Reference.from_string('my.macro'))
    micro = ComputeElementDecl(
            Identifier('micro'), Reference.from_string('my.micro'))
    comp_els = [macro, micro]
    conduit1 = Conduit(Reference.from_string('macro.intermediate_state'),
                       Reference.from_string('micro.initial_state'))
    conduit2 = Conduit(Reference.from_string('micro.final_state'),
                       Reference.from_string('macro.state_update'))
    conduits = [conduit1, conduit2]
    sim = Simulation(Identifier('test_sim'), comp_els, conduits)

    assert str(sim.name) == 'test_sim'
    assert sim.compute_elements == comp_els
    assert sim.conduits == conduits


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


def test_ymmsl() -> None:
    model = Reference.from_string('isr2d')
    parameter_values = []  # type: List[Setting]
    experiment = Experiment(model, [], parameter_values)
    doc = Ymmsl('v0.1', experiment)
    assert isinstance(doc.experiment, Experiment)
    assert isinstance(doc.experiment.model, Reference)
    assert str(doc.experiment.model) == 'isr2d'
    assert doc.experiment.model.parts[0] == 'isr2d'
    assert doc.experiment.parameter_values == []
    assert doc.experiment.scales == []


def test_loader(caplog: Any) -> None:
    yatiml.logger.setLevel(logging.DEBUG)
    caplog.set_level(logging.DEBUG)

    text = ('version: v0.1\n'
            'experiment:\n'
            '  model: test_model\n'
            '  scales:\n'
            '    domain1.x:\n'
            '      grain: 0.01\n'
            '      extent: 1.5\n'
            '    submodel1.t:\n'
            '      grain: 0.001\n'
            '      extent: 100.0\n'
            '  parameter_values:\n'
            '    test_str: value\n'
            '    test_int: 13\n'
            '    test_list: [12.3, 1.3]\n'
            'simulation:\n'
            '  name: test_model\n'
            '  compute_elements:\n'
            '    ic: isr2d.initial_conditions\n'
            '    smc: isr2d.smc\n'
            '    bf: isr2d.blood_flow\n'
            '    smc2bf: isr2d.smc2bf\n'
            '    bf2smc: isr2d.bf2smc\n'
            '  conduits:\n'
            '    ic.out: smc.initial_state\n'
            '    smc.cell_positions: smc2bf.in\n'
            '    smc2bf.out: bf.initial_domain\n'
            '    bf.wss_out: bf2smc.in\n'
            '    bf2smc.out: smc.wss_in\n'
            )
    document = yaml.load(text, Loader=ymmsl.loader)
    experiment = document.experiment
    assert str(experiment.model) == 'test_model'
    assert len(experiment.scales) == 2
    assert str(experiment.scales[0].scale) == 'domain1.x'
    assert experiment.scales[0].grain == 0.01
    assert experiment.scales[0].extent == 1.5
    assert str(experiment.scales[1].scale) == 'submodel1.t'
    assert experiment.scales[1].grain == 0.001
    assert experiment.scales[1].extent == 100.0
    assert len(experiment.parameter_values) == 3
    assert experiment.parameter_values[2].value[1] == 1.3


def test_dumper() -> None:
    domain1_x = ScaleSettings(Reference.from_string('domain1.x'), 0.01, 1.5)
    submodel1_t = ScaleSettings(Reference.from_string('submodel1.t'), 0.001, 100.0)
    scales = [domain1_x, submodel1_t]
    experiment = Experiment(Reference.from_string('test_model'), scales, [])
    document = Ymmsl('v0.1', experiment)
    text = yaml.dump(document, Dumper=ymmsl.dumper)
    assert text == ('version: v0.1\n'
                    'experiment:\n'
                    '  model: test_model\n'
                    '  scales:\n'
                    '    domain1.x:\n'
                    '      grain: 0.01\n'
                    '      extent: 1.5\n'
                    '      origin: 0.0\n'
                    '    submodel1.t:\n'
                    '      grain: 0.001\n'
                    '      extent: 100.0\n'
                    '      origin: 0.0\n'
                    )
