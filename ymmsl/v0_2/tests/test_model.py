from ymmsl.v0_2.identity import Identifier
from ymmsl.v0_2.model import (
        Component, Conduit, Implementation, Model, MulticastConduit, Ports, Reference)
from ymmsl.v0_2.ports import Operator, Port, Timeline

import pytest
import yatiml


def test_conduit_access() -> None:
    conduit = Conduit('macro.out', 'micro.in')

    assert str(conduit) == 'Conduit(macro.out -> micro.in)'
    assert conduit == Conduit('macro.out', 'micro.in')
    assert conduit != Conduit('micro.in', 'macro.out')

    assert conduit.sending_component() == 'macro'
    assert conduit.sending_port() == 'out'
    assert conduit.receiving_component() == 'micro'
    assert conduit.receiving_port() == 'in'

    conduit = Conduit('out', 'in')
    assert conduit.sending_component() == Reference([])
    assert conduit.receiving_component() == Reference([])


def test_load_plain_conduit() -> None:
    load = yatiml.load_function(Conduit)

    text = (
            'sender: macro.out\n'
            'receiver: micro.in\n'
            )

    conduit = load(text)
    assert conduit.sender == 'macro.out'
    assert conduit.receiver == 'micro.in'


def test_load_model_conduit() -> None:
    load = yatiml.load_function(Conduit)

    text = (
            'sender: out\n'
            'receiver: in\n'
            )

    conduit = load(text)
    assert conduit.sender == 'out'
    assert conduit.receiver == 'in'


def test_multicast_conduits() -> None:
    c1 = Conduit('macro.out', 'micro.init')
    mc1 = MulticastConduit('micro.final', ['macro.in', 'micro2.init'])
    m = Model('test_model', None, 'description', None, [], [c1, mc1])

    assert m.conduits[0] is c1
    assert m.conduits[1].sender == 'micro.final'
    assert m.conduits[1].receiver == 'macro.in'
    assert m.conduits[2].sender == 'micro.final'
    assert m.conduits[2].receiver == 'micro2.init'


def test_load_model() -> None:
    load_model = yatiml.load_function(
            Model, Component, Conduit, Identifier, Implementation,
            MulticastConduit, Ports, Reference)

    text = (
            'name: test_model\n'
            'ports:\n'
            '  f_init: in\n'
            '  o_f: out\n'
            'description: Description of what this does\n'
            'components:\n'
            '  macro1:\n'
            '    ports:\n'
            '      f_init: init\n'
            '      o_i: out\n'
            '      s: in\n'
            '      o_f: final\n'
            '    description: description\n'
            '    implementation: macro\n'
            '  micro1:\n'
            '    ports:\n'
            '      f_init: init\n'
            '      o_f: final\n'
            '    description: description\n'
            '    implementation: micro\n'
            'conduits:\n'
            '  in: macro1.init\n'
            '  macro1.out: micro1.init\n'
            '  micro1.final: macro1.in\n'
            '  macro1.final: out\n'
            )

    m = load_model(text)

    assert m.name == 'test_model'
    assert m.ports is not None
    assert m.ports['in'] == Port(Identifier('in'), Operator.F_INIT, Timeline(''))
    assert m.ports['out'] == Port(Identifier('out'), Operator.O_F, Timeline(''))
    assert m.description == 'Description of what this does'
    assert m.components[0].name == Reference('macro1')
    assert m.components[1].name == Reference('micro1')
    assert m.conduits[0].sender == Reference('in')
    assert m.conduits[1].sender == Reference('macro1.out')
    assert m.conduits[2].receiver == Reference('macro1.in')
    assert m.conduits[3].sender == Reference('macro1.final')


def test_consistent() -> None:
    model_ports = Ports(f_init=['model_init'], o_f=['model_final'])

    macro_ports = Ports(f_init=['Minit'], o_i=['Mout'], s=['Min'], o_f=['Mfinal'])
    macro = Component('macro', macro_ports, 'macro_impl')

    micro_ports = Ports(f_init=['minit'], o_f=['mfinal'])
    micro = Component('micro', micro_ports, 'micro_impl')

    conduits = [
            Conduit('model_init', 'macro.Minit'),
            Conduit('macro.Mout', 'micro.minit'),
            Conduit('micro.mfinal', 'macro.Min'),
            Conduit('macro.Mfinal', 'model_final')]

    model = Model(
            'with_conduits', model_ports, 'description', None, [macro, micro], conduits)

    model.check_consistent()


def test_conduits_inconsistent() -> None:
    model_ports = Ports(f_init=['model_init'], o_f=['model_final'])

    macro_ports = Ports(f_init=['Minit'], o_i=['Mout'], s=['Min'], o_f=['Mfinal'])
    macro = Component('macro', macro_ports, 'macro_impl')

    micro_ports = Ports(f_init=['minit'], o_f=['mfinal'])
    micro = Component('micro', micro_ports, 'micro_impl')

    conduits = [
            Conduit('modelinit', 'macro.Minit'),
            Conduit('macro.Mout', 'micro.m_init'),
            Conduit('macro.Mout', 'miicro.minit'),
            Conduit('macroo.Mout', 'micro.minit'),
            Conduit('micro.m_final', 'macro.Min'),
            Conduit('macro.Mfinal', 'modelfinal')]

    model = Model(
            'bad_conduits', model_ports, 'description', None, [macro, micro], conduits)

    with pytest.raises(RuntimeError) as e:
        model.check_consistent()

    assert len(str(e.value).split('\n')) == 7
