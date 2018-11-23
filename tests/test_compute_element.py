#!/usr/bin/env python
"""Tests for the compute_element module.
"""

from ymmsl import Operator, Port, Identifier


def test_operator() -> None:
    op1 = Operator.NONE
    op2 = Operator.F_INIT
    op3 = Operator.MAP

    assert op1 == Operator.NONE
    assert op2 == Operator.F_INIT
    assert op3 == Operator.MAP


def test_port() -> None:
    ep1 = Port(Identifier('test_in'), Operator.F_INIT)

    assert str(ep1.name == 'test_in')
    assert ep1.operator == Operator.F_INIT
