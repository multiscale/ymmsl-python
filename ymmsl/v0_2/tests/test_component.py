from ymmsl.v0_2 import Identifier, Component, Operator, Port, Ports, Reference, Timeline

import pytest


def test_component_declaration() -> None:
    test_decl = Component('test', Ports(), 'description', 'ns.model')
    assert isinstance(test_decl.name, Reference)
    assert str(test_decl.name) == 'test'

    assert len(test_decl.ports) == 0

    assert test_decl.description == 'description'

    assert test_decl.optional is False

    assert isinstance(test_decl.implementation, Reference)
    assert str(test_decl.implementation) == 'ns.model'

    assert test_decl.multiplicity == []
    assert str(test_decl) == 'test'


def test_component_multiplicity() -> None:
    test_decl = Component('test', Ports(), 'description', 'ns.model', False, 10)
    assert isinstance(test_decl.name, Reference)
    assert str(test_decl.name) == 'test'
    assert test_decl.multiplicity == [10]
    assert str(test_decl) == 'test[0:10]'

    test_decl = Component('test', Ports(), 'description', 'ns2.model2', False, [1, 2])
    assert isinstance(test_decl.name, Reference)
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns2.model2'
    assert test_decl.multiplicity == [1, 2]
    assert str(test_decl) == 'test[0:1][0:2]'

    with pytest.raises(ValueError):
        test_decl = Component('test', Ports(), 'description', 'ns2.model2[1]')


def test_component_instances() -> None:
    c1 = Component('test', Ports(), 'description', 'model')
    assert c1.instances() == [Reference('test')]

    c2 = Component('test', Ports(), 'description', 'model', False, 3)
    assert c2.instances() == [
            Reference('test[0]'), Reference('test[1]'), Reference('test[2]')]

    c3 = Component('test', Ports(), 'description', 'model', False, [2, 2])
    assert c3.instances() == [
            Reference('test[0][0]'), Reference('test[0][1]'),
            Reference('test[1][0]'), Reference('test[1][1]')]


def test_component_ports() -> None:
    c = Component('test', Ports(['init'], ['out'], ['in'], ['final']), 'description')
    assert isinstance(c.ports, Ports)

    assert c.ports['init'] == Port(Identifier('init'), Operator.F_INIT, Timeline(''))
    assert c.ports['out'] == Port(Identifier('out'), Operator.O_I, Timeline(''))
    assert c.ports['in'] == Port(Identifier('in'), Operator.S, Timeline(''))
    assert c.ports['final'] == Port(Identifier('final'), Operator.O_F, Timeline(''))
