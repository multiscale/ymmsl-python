#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from ymmsl import Identifier, Reference

import pytest
import yatiml
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

    assert Identifier('test') == Identifier('test')
    assert Identifier('test1') != Identifier('test2')

    test_dict = {Identifier('test'): 1}
    assert test_dict[Identifier('test')] == 1


def test_reference() -> None:
    test_ref = Reference.from_string('_testing')
    assert str(test_ref) == '_testing'
    assert len(test_ref) == 1
    assert isinstance(test_ref[0], Identifier)
    assert str(test_ref[0]) == '_testing'

    with pytest.raises(ValueError):
        Reference.from_string('1test')

    test_ref = Reference.from_string('test.testing')
    assert len(test_ref) == 2
    assert isinstance(test_ref[0], Identifier)
    assert str(test_ref[0]) == 'test'
    assert isinstance(test_ref[1], Identifier)
    assert str(test_ref[1]) == 'testing'
    assert str(test_ref) == 'test.testing'

    test_ref = Reference.from_string('test[12]')
    assert len(test_ref) == 2
    assert isinstance(test_ref[0], Identifier)
    assert str(test_ref[0]) == 'test'
    assert isinstance(test_ref[1], int)
    assert test_ref[1] == 12
    assert str(test_ref) == 'test[12]'

    test_ref = Reference.from_string('test[12].testing.ok.index[3][5]')
    assert len(test_ref) == 7
    assert isinstance(test_ref[0], Identifier)
    assert str(test_ref[0]) == 'test'
    assert isinstance(test_ref[1], int)
    assert test_ref[1] == 12
    assert isinstance(test_ref[2], Identifier)
    assert str(test_ref[2]) == 'testing'
    assert isinstance(test_ref[3], Identifier)
    assert str(test_ref[3]) == 'ok'
    assert isinstance(test_ref[4], Identifier)
    assert str(test_ref[4]) == 'index'
    assert isinstance(test_ref[5], int)
    assert test_ref[5] == 3
    assert isinstance(test_ref[6], int)
    assert test_ref[6] == 5
    assert str(test_ref) == 'test[12].testing.ok.index[3][5]'

    assert len(test_ref) == 7
    assert str(test_ref[0]) == 'test'
    assert test_ref[1] == 12
    assert str(test_ref[3]) == 'ok'
    assert str(test_ref[:3]) == 'test[12].testing'
    assert str(test_ref[2:]) == 'testing.ok.index[3][5]'
    with pytest.raises(ValueError):
        test_ref[1:]

    with pytest.raises(ValueError):
        Reference([4])

    with pytest.raises(ValueError):
        Reference([3, Identifier('test')])

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

    with pytest.raises(ValueError):
        Reference.from_string('[3]test')

    with pytest.raises(ValueError):
        Reference.from_string('[4].test')

    test_dict = {Reference.from_string('test[4]'): 1}
    assert test_dict[Reference.from_string('test[4]')] == 1


def test_reference_equivalence() -> None:
    assert Reference.from_string('test.test[3]') == Reference.from_string(
            'test.test[3]')
    assert Reference.from_string('test.test[3]') != Reference.from_string(
            'test1.test[3]')


def test_reference_io() -> None:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [Identifier, Reference])
    yatiml.set_document_type(Loader, Reference)

    text = 'test[12]'
    doc = yaml.load(text, Loader=Loader)
    assert str(doc[0]) == 'test'
    assert doc[1] == 12

    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [Identifier, Reference])

    doc = Reference.from_string('test[12].testing.ok.index[3][5]')
    text = yaml.dump(doc, Dumper=Dumper)
    assert text == 'test[12].testing.ok.index[3][5]\n...\n'
