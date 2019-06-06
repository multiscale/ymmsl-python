#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

#import logging
from typing import Any, List  # noqa: F401

from ymmsl import (Experiment, Reference, Setting, Simulation,
                   YmmslDocument)  # noqa: F401

import yatiml
import ymmsl


def test_ymmsl() -> None:
    parameter_values = []  # type: List[Setting]
    experiment = Experiment('isr2d', parameter_values)
    doc = YmmslDocument('v0.1', experiment)
    assert isinstance(doc.experiment, Experiment)
    assert isinstance(doc.experiment.model, Reference)
    assert str(doc.experiment.model) == 'isr2d'
    assert doc.experiment.model[0] == 'isr2d'
    assert doc.experiment.parameter_values == []


def test_loader(caplog: Any) -> None:
    # yatiml.logger.setLevel(logging.DEBUG)
    # caplog.set_level(logging.DEBUG)

    text = ('version: v0.1\n'
            'experiment:\n'
            '  model: test_model\n'
            '  parameter_values:\n'
            '    test_str: value\n'
            '    test_int: 13\n'
            '    test_list: [12.3, 1.3]\n'
            )
    document = ymmsl.load(text)
    experiment = document.experiment
    assert experiment is not None
    assert str(experiment.model) == 'test_model'
    assert len(experiment.parameter_values) == 3
    assert isinstance(experiment.parameter_values[2].value, list)
    assert experiment.parameter_values[2].value[1] == 1.3

    text = 'version: v0.1\n'
    document = ymmsl.load(text)
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
    document = ymmsl.load(text)
    simulation = document.simulation
    assert isinstance(simulation, Simulation)
    assert str(simulation.name) == 'test_model'
    assert len(simulation.compute_elements) == 5
    assert str(simulation.compute_elements[4].name) == 'bf2smc'
    assert str(simulation.compute_elements[2].implementation) == 'isr2d.blood_flow'
    assert len(simulation.conduits) == 5
    assert str(simulation.conduits[0].sender) == 'ic.out'
    assert str(simulation.conduits[1].sending_port()) == 'cell_positions'
    assert str(simulation.conduits[3].receiving_compute_element()) == 'bf2smc'


def test_dumper() -> None:
    experiment = Experiment('test_model', [])
    document = YmmslDocument('v0.1', experiment)
    text = ymmsl.save(document)
    assert text == ('version: v0.1\n'
                    'experiment:\n'
                    '  model: test_model\n'
                    )
