from ymmsl.v0_2.identity import Identifier, Reference
from ymmsl.v0_2.ports import Operator, Port, Ports, Timeline

import pytest
import yatiml


Ref = Reference


def test_create_empty_timeline() -> None:
    tl = Timeline('')
    assert tl.absolute is False
    assert len(tl._parts) == 0


def test_create_root_timeline() -> None:
    tl = Timeline(':')
    assert tl.absolute is True
    assert len(tl._parts) == 0


def test_create_absolute_timeline() -> None:
    tl = Timeline(':timeline')
    assert tl.absolute is True
    assert len(tl._parts) == 1
    assert tl._parts[0] == 'timeline'


def test_create_relative_timeline() -> None:
    tl = Timeline('timeline')
    assert tl.absolute is False
    assert len(tl._parts) == 1
    assert tl._parts[0] == 'timeline'


def test_create_full_timeline() -> None:
    tl = Timeline('c1.a:c2.b:c3:c4')
    assert tl.absolute is False
    assert len(tl._parts) == 4
    assert tl._parts == ['c1.a', 'c2.b', 'c3', 'c4']


def test_create_absolute_from_list_of_str() -> None:
    tl = Timeline(['c1.a', 'c2.b', 'c3', 'c4'], True)
    assert tl.absolute is True
    assert len(tl._parts) == 4
    assert tl._parts == ['c1.a', 'c2.b', 'c3', 'c4']


def test_create_relative_from_list_of_ref() -> None:
    tl = Timeline([Ref('c1'), Ref('c2.a')], False)
    assert tl.absolute is False
    assert len(tl._parts) == 2
    assert tl._parts == ['c1', 'c2.a']


def test_timeline_equality() -> None:
    tl1 = Timeline(':c0:c1:c2.a')
    tl2 = Timeline(['c0', 'c1', 'c2.a'], True)
    assert tl1 == tl2

    tl2._parts[1] = Reference('c1.x')
    assert tl1 != tl2

    tl1._parts[1] = Reference('c1.x')
    assert tl1 == tl2

    tl2.absolute = False
    assert tl1 != tl2

    tl1.absolute = False
    assert tl1 == tl2

    tl2.absolute = True
    assert tl1 != tl2


def test_timeline_to_str() -> None:
    tl = Timeline([Ref('c1'), Ref('c2.a'), Ref('c3')], False)
    assert str(tl) == 'c1:c2.a:c3'

    tl.absolute = True
    assert str(tl) == ':c1:c2.a:c3'


def test_timeline_indexing() -> None:
    tl = Timeline(':c0:c1:c2.p:c3.q')
    assert len(tl) == 4
    assert isinstance(tl[0], Reference)
    assert tl[0] == 'c0'
    assert isinstance(tl[1], Reference)
    assert tl[1] == 'c1'
    assert isinstance(tl[2], Reference)
    assert tl[2] == 'c2.p'
    assert isinstance(tl[3], Reference)
    assert tl[3] == 'c3.q'

    with pytest.raises(IndexError):
        tl[4]


def test_timeline_concatenation() -> None:
    tl1 = Timeline(':c1:c2.a')
    tl2 = Timeline('c3.b:c4')
    tl3 = tl1 + tl2

    assert tl3.absolute is True
    assert len(tl3._parts) == 4
    assert tl3 == Timeline(':c1:c2.a:c3.b:c4')

    tl2.absolute = True

    with pytest.raises(ValueError):
        tl1 + tl2


def test_timeline_concatenate_empty() -> None:
    tl1 = Timeline('c1:c2.a')
    tl2 = Timeline('')

    tl3 = tl1 + tl2
    assert tl3 == tl1

    tl4 = tl2 + tl1
    assert tl4 == tl1


def test_create_empty_ports() -> None:
    p = Ports()
    assert len(p._ports) == 0


def test_create_ports_by_operator() -> None:
    p = Ports('a', None, 'b c', ['d', 'e'])

    assert p._ports == {
            'a': Port(Identifier('a'), Operator.F_INIT, Timeline('')),
            'b': Port(Identifier('b'), Operator.S, Timeline('')),
            'c': Port(Identifier('c'), Operator.S, Timeline('')),
            'd': Port(Identifier('d'), Operator.O_F, Timeline('')),
            'e': Port(Identifier('e'), Operator.O_F, Timeline(''))}


def test_create_ports_from_list() -> None:
    t1 = Timeline('timeline1')
    t2 = Timeline('timeline2')

    p = Ports([
            Port(Identifier('a'), Operator.F_INIT, Timeline('')),
            Port(Identifier('b'), Operator.O_F, Timeline('')),
            Port(Identifier('c'), Operator.O_I, t1),
            Port(Identifier('d'), Operator.S, t1),
            Port(Identifier('e'), Operator.O_I, t2),
            Port(Identifier('f'), Operator.S, t2)
            ])

    assert p._ports == {
            'a': Port(Identifier('a'), Operator.F_INIT, Timeline('')),
            'b': Port(Identifier('b'), Operator.O_F, Timeline('')),
            'c': Port(Identifier('c'), Operator.O_I, t1),
            'd': Port(Identifier('d'), Operator.S, t1),
            'e': Port(Identifier('e'), Operator.O_I, t2),
            'f': Port(Identifier('f'), Operator.S, t2)
            }


def test_ports_access() -> None:
    p = Ports('a', None, 'b c', ['d', 'e'])

    assert 'a' in p
    assert Identifier('a') in p
    assert 'z' not in p
    assert Identifier('q') not in p

    assert p['a'] == Port(Identifier('a'), Operator.F_INIT, Timeline(''))
    assert p['b'] == Port(Identifier('b'), Operator.S, Timeline(''))
    assert p[Identifier('c')] == Port(Identifier('c'), Operator.S, Timeline(''))
    assert p['d'] == Port(Identifier('d'), Operator.O_F, Timeline(''))
    assert p[Identifier('e')] == Port(Identifier('e'), Operator.O_F, Timeline(''))


def test_ports_iteration() -> None:
    p = Ports('p', 'q r', ['s', 't'], 'u v')
    names = 'pqrstuv'

    for port_name, ref in zip(p, names):
        assert port_name == ref


def test_load_ports_simple() -> None:
    load = yatiml.load_function(Ports, Port, Operator, Timeline)

    text = (
            'f_init:\n'
            '- a\n'
            '- b\n'
            'o_i: c\n'
            'o_f: d e\n'
            )

    p = load(text)

    assert p._ports == {
            'a': Port(Identifier('a'), Operator.F_INIT, Timeline('')),
            'b': Port(Identifier('b'), Operator.F_INIT, Timeline('')),
            'c': Port(Identifier('c'), Operator.O_I, Timeline('')),
            'd': Port(Identifier('d'), Operator.O_F, Timeline('')),
            'e': Port(Identifier('e'), Operator.O_F, Timeline(''))
            }


def test_load_ports_with_timelines() -> None:
    load = yatiml.load_function(Ports, Port, Operator, Timeline)

    text = (
            'f_init: a b\n'
            'o_f: c\n'
            '+timeline1:\n'
            '  o_i: d\n'
            '  s: e f\n'
            '+timeline2:\n'
            '  o_i: g h\n'
            )

    p = load(text)

    assert p._ports == {
            'a': Port(Identifier('a'), Operator.F_INIT, Timeline('')),
            'b': Port(Identifier('b'), Operator.F_INIT, Timeline('')),
            'c': Port(Identifier('c'), Operator.O_F, Timeline('')),
            'd': Port(Identifier('d'), Operator.O_I, Timeline('timeline1')),
            'e': Port(Identifier('e'), Operator.S, Timeline('timeline1')),
            'f': Port(Identifier('f'), Operator.S, Timeline('timeline1')),
            'g': Port(Identifier('g'), Operator.O_I, Timeline('timeline2')),
            'h': Port(Identifier('h'), Operator.O_I, Timeline('timeline2'))
            }


def test_load_ports_invalid_operator() -> None:
    load = yatiml.load_function(Ports, Port, Operator, Timeline)

    text = (
            'f_init: a b\n'
            'o_i: d\n'
            's: e f\n'
            'o_g: g h\n'
            )

    with pytest.raises(yatiml.RecognitionError):
        load(text)


def test_load_ports_invalid_timeline() -> None:
    load = yatiml.load_function(Ports, Port, Operator, Timeline)

    text = (
            'f_init: a b\n'
            '+timeline1:\n'
            '  o_i: d\n'
            '  s: e f\n'
            'timeline2:\n'
            '  o_i: g h\n'
            )

    with pytest.raises(yatiml.RecognitionError):
        load(text)


def test_load_ports_invalid_timeline_operator() -> None:
    load = yatiml.load_function(Ports, Port, Operator, Timeline)

    text = (
            'f_init: a b\n'
            '+timeline1:\n'
            '  o_i: d\n'
            '  s: e f\n'
            '+timeline2:\n'
            '  o_i: g h\n'
            '  +timeline3:\n'
            '    o_i: i\n'
            )

    with pytest.raises(yatiml.RecognitionError):
        load(text)


def test_dump_simple_ports() -> None:
    dumps = yatiml.dumps_function(Ports, Port, Operator, Timeline)

    p = Ports(['init'], ['out'], 'in', 'final')
    text = dumps(p)

    assert text == (
            'f_init: init\n'
            'o_i: out\n'
            's: in\n'
            'o_f: final\n'
            )


def test_dump_long_ports() -> None:
    dumps = yatiml.dumps_function(Ports, Port, Operator, Timeline)

    p = Ports(
            'a b c d e f', None, None, [
                'port_with_a_long_name', 'another_one_like_that',
                'this_is_really_going_to_cause_trouble'])
    text = dumps(p)

    assert text == (
            'f_init:\n'
            '- a\n'
            '- b\n'
            '- c\n'
            '- d\n'
            '- e\n'
            '- f\n'
            'o_f:\n'
            '- port_with_a_long_name\n'
            '- another_one_like_that\n'
            '- this_is_really_going_to_cause_trouble\n'
            )


def test_dump_ports_with_timelines() -> None:
    dumps = yatiml.dumps_function(Ports, Port, Operator, Timeline)

    p = Ports([
        Port(Identifier('init'), Operator.F_INIT, Timeline('')),
        Port(Identifier('out1'), Operator.O_I, Timeline('timeline1')),
        Port(Identifier('out2'), Operator.O_I, Timeline('timeline2')),
        Port(Identifier('in1'), Operator.S, Timeline('timeline1')),
        Port(Identifier('in2'), Operator.S, Timeline('timeline2')),
        Port(Identifier('final'), Operator.O_F, Timeline(''))
        ])

    text = dumps(p)

    assert text == (
            'f_init: init\n'
            '+timeline1:\n'
            '  o_i: out1\n'
            '  s: in1\n'
            '+timeline2:\n'
            '  o_i: out2\n'
            '  s: in2\n'
            'o_f: final\n'
            )


def test_sending_receiving_port_names() -> None:
    p = Ports('a', 'b c', 'd e', 'f')

    assert p.sending_port_names() == ['b', 'c', 'f']
    assert p.receiving_port_names() == ['a', 'd', 'e']
