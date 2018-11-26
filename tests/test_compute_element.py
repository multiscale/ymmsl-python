from ymmsl import Operator, Port, Identifier


def test_operator() -> None:
    op1 = Operator.NONE
    op2 = Operator.F_INIT
    op3 = Operator.O_I

    assert op1 == Operator.NONE
    assert op2 == Operator.F_INIT
    assert op3 == Operator.O_I

    assert op1.allows_sending()
    assert op1.allows_receiving()

    assert not op2.allows_sending()
    assert op2.allows_receiving()

    assert op3.allows_sending()
    assert not op3.allows_receiving()


def test_port() -> None:
    ep1 = Port(Identifier('test_in'), Operator.F_INIT)

    assert str(ep1.name == 'test_in')
    assert ep1.operator == Operator.F_INIT
