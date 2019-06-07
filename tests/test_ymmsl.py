#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from typing import Any, List  # noqa: F401

from ymmsl import (Experiment, Reference, Setting,
                   YmmslDocument)  # noqa: F401


def test_ymmsl() -> None:
    parameter_values = []  # type: List[Setting]
    experiment = Experiment('isr2d', parameter_values)
    doc = YmmslDocument('v0.1', experiment)
    assert isinstance(doc.experiment, Experiment)
    assert isinstance(doc.experiment.model, Reference)
    assert str(doc.experiment.model) == 'isr2d'
    assert doc.experiment.model[0] == 'isr2d'
    assert doc.experiment.parameter_values == []
