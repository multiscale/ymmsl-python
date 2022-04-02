from typing import Iterable

import pytest

from ymmsl import Operator, Port, Ports, Identifier


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

    assert p1.operator('initial_state') == Operator.F_INIT
    assert p1.operator('bc_i') == Operator.S
    assert p2.operator('output') == Operator.O_F
    assert p3.operator('init2') == Operator.F_INIT
    assert p3.operator('obs3') == Operator.O_I
    with pytest.raises(KeyError):
        p3.operator('x')
