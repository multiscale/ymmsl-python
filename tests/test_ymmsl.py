#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

import logging
from typing import Any, List

from ymmsl import Experiment, Reference, ScaleSettings, Setting, YmmslDocument

import pytest
import yatiml
import ymmsl
from ruamel import yaml


def test_ymmsl() -> None:
    model = Reference.from_string('isr2d')
    parameter_values = []  # type: List[Setting]
    experiment = Experiment(model, [], parameter_values)
    doc = YmmslDocument('v0.1', experiment)
    assert isinstance(doc.experiment, Experiment)
    assert isinstance(doc.experiment.model, Reference)
    assert str(doc.experiment.model) == 'isr2d'
    assert doc.experiment.model.parts[0] == 'isr2d'
    assert doc.experiment.parameter_values == []
    assert doc.experiment.scales == []


def test_loader(caplog: Any) -> None:
    # yatiml.logger.setLevel(logging.DEBUG)
    # caplog.set_level(logging.DEBUG)

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

    text = 'version: v0.1\n'
    document = yaml.load(text, Loader=ymmsl.loader)
    assert document.version == 'v0.1'

    text = ('version: v0.1\n'
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
            '    bf2smc.out: smc.wss_in\n')
    document = yaml.load(text, Loader=ymmsl.loader)
    simulation = document.simulation
    assert str(simulation.name) == 'test_model'
    assert len(simulation.compute_elements) == 5
    assert str(simulation.compute_elements[4].name) == 'bf2smc'
    assert str(simulation.compute_elements[2].implementation) == 'isr2d.blood_flow'
    assert len(simulation.conduits) == 5
    assert str(simulation.conduits[0].sender) == 'ic.out'
    assert str(simulation.conduits[1].sending_port()) == 'cell_positions'
    assert str(simulation.conduits[3].receiving_compute_element()) == 'bf2smc'


def test_dumper() -> None:
    domain1_x = ScaleSettings(Reference.from_string('domain1.x'), 0.01, 1.5)
    submodel1_t = ScaleSettings(Reference.from_string('submodel1.t'), 0.001, 100.0)
    scales = [domain1_x, submodel1_t]
    experiment = Experiment(Reference.from_string('test_model'), scales, [])
    document = YmmslDocument('v0.1', experiment)
    text = yaml.dump(document, Dumper=ymmsl.dumper)
    assert text == ('version: v0.1\n'
                    'experiment:\n'
                    '  model: test_model\n'
                    '  scales:\n'
                    '    domain1.x:\n'
                    '      grain: 0.01\n'
                    '      extent: 1.5\n'
                    '    submodel1.t:\n'
                    '      grain: 0.001\n'
                    '      extent: 100.0\n'
                    )
