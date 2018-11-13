#!/usr/bin/env python
"""Tests for the compute_element module.
"""

from ymmsl import Operator


def test_operator() -> None:
    op1 = Operator.NONE
    op2 = Operator.F_INIT
    op3 = Operator.MAP

    assert op1 == Operator.NONE
    assert op2 == Operator.F_INIT
    assert op3 == Operator.MAP
