#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from ymmsl import Identifier, Reference

import pytest


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
