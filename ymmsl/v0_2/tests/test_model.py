from ymmsl.v0_2.identity import Identifier
from ymmsl.v0_2.model import (
        Component, Conduit, ConduitFilter, Model, MulticastConduit, Ports, Reference)
from ymmsl.v0_2.ports import Operator, Port, Timeline
from ymmsl.v0_2.supported_settings import SettingType, SupportedSettings

import pytest
import yatiml


def test_conduit_filter() -> None:
    assert ConduitFilter.LAST.is_reducer()
    assert ConduitFilter.REPEAT.is_repeater()
    assert ConduitFilter.PAD.is_repeater()


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
    load = yatiml.load_function(Conduit, ConduitFilter)

    text = (
            'sender: macro.out\n'
            'receiver: micro.in\n'
            )

    conduit = load(text)
    assert conduit.sender == 'macro.out'
    assert conduit.receiver == 'micro.in'


def test_load_model_conduit() -> None:
    load = yatiml.load_function(Conduit, ConduitFilter)

    text = (
            'sender: out\n'
            'receiver: in\n'
            )

    conduit = load(text)
    assert conduit.sender == 'out'
    assert conduit.receiver == 'in'


def test_load_filtered_conduit() -> None:
    load = yatiml.load_function(Conduit, ConduitFilter)

    text = (
            'sender: micro1.final\n'
            'receiver: micro2.init\n'
            'filters: last pad\n'
            )

    conduit = load(text)
    assert conduit.sender == 'micro1.final'
    assert conduit.receiver == 'micro2.init'
    assert conduit.filters == [ConduitFilter.LAST, ConduitFilter.PAD]


def test_load_invalid_filter() -> None:
    load = yatiml.load_function(Conduit, ConduitFilter)

    text = (
            'sender: micro1.final\n'
            'receiver: micro2.init\n'
            'filters: convert-data-format\n'
            )

    with pytest.raises(yatiml.RecognitionError):
        load(text)


def test_dump_conduit() -> None:
    dumps = yatiml.dumps_function(Conduit, ConduitFilter, Reference)
    conduit = Conduit('c1.out', 'c2.in', [ConduitFilter.LAST, ConduitFilter.REPEAT])
    text = dumps(conduit)

    assert text == (
            'sender: c1.out\n'
            'receiver: c2.in\n'
            'filters: last repeat\n')


def test_multicast_conduits() -> None:
    c1 = Conduit('macro.out', 'micro.init')
    mc1 = MulticastConduit('micro.final', ['macro.in', 'micro2.init'])
    m = Model('test_model', None, 'description', None, [], [c1, mc1])

    assert m.conduits[0] is c1
    assert m.conduits[1].sender == 'micro.final'
    assert m.conduits[1].receiver == 'macro.in'
    assert m.conduits[2].sender == 'micro.final'
    assert m.conduits[2].receiver == 'micro2.init'


def test_load_multicast_conduits() -> None:
    load = yatiml.load_function(MulticastConduit)

    text = (
            'sender: init.out\n'
            'receiver:\n'
            '- c1.in\n'
            '- repeat pad c2.in\n'
            )

    conduit = load(text)

    assert conduit.sender == 'init.out'
    assert conduit.receiver == ['c1.in', 'repeat pad c2.in']
    assert conduit.as_conduits() == [
            Conduit('init.out', 'c1.in'),
            Conduit('init.out', 'c2.in', [ConduitFilter.REPEAT, ConduitFilter.PAD])]


def test_load_multicast_invalid_filter() -> None:
    load = yatiml.load_function(MulticastConduit)

    text = (
            'sender: init.out\n'
            'receiver:\n'
            '- c1.in\n'
            '- convert_data_format c2.in\n'
            )

    with pytest.raises(yatiml.RecognitionError):
        load(text)


def test_dump_multicast_conduits() -> None:
    dump = yatiml.dumps_function(MulticastConduit)

    conduit = MulticastConduit(
            'init.out', [
                ('c1.in', []), ('c2.in', [ConduitFilter.REPEAT, ConduitFilter.PAD])])
    text = dump(conduit)

    assert text == (
            'sender: init.out\n'
            'receiver:\n'
            '- c1.in\n'
            '- repeat pad c2.in\n')


def test_load_model(model_text: str) -> None:
    load_model = yatiml.load_function(
            Model, Component, Conduit, ConduitFilter, Identifier, MulticastConduit,
            Ports, Reference, SettingType, SupportedSettings)

    m = load_model(model_text)

    assert m.name == 'test_model'
    assert m.ports is not None
    assert m.ports['in'] == Port(Identifier('in'), Operator.F_INIT, Timeline(''))
    assert m.ports['out'] == Port(Identifier('out'), Operator.O_F, Timeline(''))
    assert m.description == 'Test model for loading/dumping'
    assert m.supported_settings is not None
    assert m.supported_settings['eta'] == SettingType.FLOAT
    assert m.components[0].name == Reference('ic')
    assert m.components[1].name == Reference('smc')
    assert m.components[2].name == Reference('bf')
    assert m.components[3].name == Reference('smc2bf')
    assert m.components[4].name == Reference('bf2smc')
    assert m.conduits[0].sender == Reference('ic.out')
    assert m.conduits[1].sender == Reference('smc.cell_positions')
    assert m.conduits[2].receiver == Reference('bf.initial_domain')
    assert m.conduits[3].receiver == Reference('bf2smc.in')
    assert m.conduits[4].sender == Reference('bf2smc.out')


def test_load_model_with_filters(model_with_filters_text: str) -> None:
    load_model = yatiml.load_function(
            Model, Component, Conduit, ConduitFilter, Identifier, MulticastConduit,
            Ports, Reference, SettingType, SupportedSettings)

    m = load_model(model_with_filters_text)

    assert m.name == 'test_model_conduit_filters'
    assert m.ports is not None
    assert len(m.ports) == 0
    assert m.description == 'Test model for loading/dumping conduit filters'
    assert m.supported_settings is None
    assert m.components[0].name == Reference('init')
    assert m.components[1].name == Reference('macro1')
    assert m.components[2].name == Reference('micro1')
    assert m.components[3].name == Reference('macro2')
    assert m.components[4].name == Reference('micro2')

    assert m.conduits[0].sender == Reference('init.macro_out')
    assert m.conduits[0].receiver == Reference('macro1.init')
    assert m.conduits[0].filters == []
    assert m.conduits[1].sender == Reference('init.micro_out')
    assert m.conduits[1].receiver == Reference('micro1.init_state')
    assert m.conduits[1].filters == [ConduitFilter.PAD]
    assert m.conduits[5].sender == Reference('micro1.final_state')
    assert m.conduits[5].receiver == Reference('micro2.init_state')
    assert m.conduits[5].filters == [ConduitFilter.LAST, ConduitFilter.PAD]


def test_load_model_with_invalid_filters() -> None:
    load_model = yatiml.load_function(
            Model, Component, Conduit, ConduitFilter, Identifier, MulticastConduit,
            Ports, Reference, SettingType, SupportedSettings)

    text = (
            'name: test_model_with_invalid_filters\n'
            'description: Testing invalid filters\n'
            'conduits:\n'
            '  init.micro_out: invalid-filter micro1.init_state\n'
            )

    with pytest.raises(yatiml.RecognitionError):
        load_model(text)


def test_dump_model(model: Model, model_text: str) -> None:
    dumps_model = yatiml.dumps_function(
            Model, Component, Conduit, Identifier, MulticastConduit, Ports, Reference,
            SettingType, SupportedSettings)

    text = dumps_model(model)
    assert text == model_text


def test_dump_model_with_filters(
        model_with_filters: Model, model_with_filters_text: str) -> None:
    dumps_model = yatiml.dumps_function(
            Model, Component, Conduit, ConduitFilter, Identifier, MulticastConduit,
            Ports, Reference, SettingType, SupportedSettings)

    text = dumps_model(model_with_filters)
    assert text == model_with_filters_text


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

    errors = model.check_consistent()
    assert not errors


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

    errors = model.check_consistent()
    assert len(errors) == 6
