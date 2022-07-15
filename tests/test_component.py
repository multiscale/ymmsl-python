from typing import Iterable

import pytest

from ymmsl import Component, Identifier, Operator, Port, Ports, Reference


def test_operator() -> None:
    op1 = Operator.F_INIT
    op2 = Operator.O_I

    assert op1 == Operator.F_INIT
    assert op2 == Operator.O_I

    assert not op1.allows_sending()
    assert op1.allows_receiving()

    assert op2.allows_sending()
    assert not op2.allows_receiving()


def test_port() -> None:
    ep1 = Port(Identifier('test_in'), Operator.F_INIT)

    assert str(ep1.name) == 'test_in'
    assert ep1.operator == Operator.F_INIT


def test_ports() -> None:
    p1 = Ports(['initial_state'], ['obs_i'], ['bc_i'], ['final_output'])
    p2 = Ports(f_init=['input'], o_f=['output'])
    p3 = Ports(['init1', 'init2'], ['obs1', 'obs2', 'obs3'])

    assert set(p1.port_names()) == {
            'initial_state', 'obs_i', 'bc_i', 'final_output'}
    assert set(p2.port_names()) == {'input', 'output'}
    assert set(p3.port_names()) == {'init1', 'init2', 'obs1', 'obs2', 'obs3'}

    def in_ports(ports: Iterable[Port], name: str, op: Operator) -> bool:
        return any(map(lambda p: p.name == name and p.operator == op, ports))

    assert len(list(p1.all_ports())) == 4
    assert in_ports(p1.all_ports(), 'initial_state', Operator.F_INIT)
    assert in_ports(p1.all_ports(), 'obs_i', Operator.O_I)
    assert in_ports(p1.all_ports(), 'bc_i', Operator.S)
    assert in_ports(p1.all_ports(), 'final_output', Operator.O_F)

    assert len(list(p2.all_ports())) == 2
    assert in_ports(p2.all_ports(), 'input', Operator.F_INIT)
    assert in_ports(p2.all_ports(), 'output', Operator.O_F)

    assert len(list(p3.all_ports())) == 5
    assert in_ports(p3.all_ports(), 'init1', Operator.F_INIT)
    assert in_ports(p3.all_ports(), 'init2', Operator.F_INIT)
    assert in_ports(p3.all_ports(), 'obs1', Operator.O_I)
    assert in_ports(p3.all_ports(), 'obs2', Operator.O_I)
    assert in_ports(p3.all_ports(), 'obs3', Operator.O_I)

    assert p1.operator(Identifier('initial_state')) == Operator.F_INIT
    assert p1.operator(Identifier('bc_i')) == Operator.S
    assert p2.operator(Identifier('output')) == Operator.O_F
    assert p3.operator(Identifier('init2')) == Operator.F_INIT
    assert p3.operator(Identifier('obs3')) == Operator.O_I
    with pytest.raises(KeyError):
        p3.operator(Identifier('x'))


def test_component_declaration() -> None:
    test_decl = Component('test', 'ns.model')
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns.model'
    assert test_decl.multiplicity == []
    assert str(test_decl) == 'test'

    test_decl = Component('test', 'ns.model', 10)
    assert isinstance(test_decl.name, Reference)
    assert str(test_decl.name) == 'test'
    assert test_decl.multiplicity == [10]
    assert str(test_decl) == 'test[0:10]'

    test_decl = Component('test', 'ns2.model2', [1, 2])
    assert isinstance(test_decl.name, Reference)
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns2.model2'
    assert test_decl.multiplicity == [1, 2]
    assert str(test_decl) == 'test[0:1][0:2]'

    with pytest.raises(ValueError):
        test_decl = Component('test', 'ns2.model2[1]')


def test_component_instances() -> None:
    c1 = Component('test', 'model')
    assert c1.instances() == [Reference('test')]

    c2 = Component('test', 'model', 3)
    assert c2.instances() == [
            Reference('test[0]'), Reference('test[1]'), Reference('test[2]')]

    c3 = Component('test', 'model', [2, 2])
    assert c3.instances() == [
            Reference('test[0][0]'), Reference('test[0][1]'),
            Reference('test[1][0]'), Reference('test[1][1]')]
