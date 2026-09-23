from copy import copy
from typing import Callable

import pytest
import yatiml

from ymmsl.v0_2.component import Component
from ymmsl.v0_2.identity import Identifier
from ymmsl.v0_2.implementation import Implementation, Reference
from ymmsl.v0_2.model import (
    Conduit,
    ConduitFilter,
    MatchingTimelines,
    Model,
    MulticastConduit,
)
from ymmsl.v0_2.ports import Operator, Port, Ports, Timeline
from ymmsl.v0_2.supported_settings import (
    SettingType,
    SupportedSetting,
    SupportedSettings,
)

Ref = Reference


@pytest.fixture
def load_model() -> Callable:
    return yatiml.load_function(
        Model,
        Component,
        Conduit,
        ConduitFilter,
        Identifier,
        MatchingTimelines,
        MulticastConduit,
        Ports,
        Reference,
        SettingType,
        SupportedSetting,
        SupportedSettings,
        Timeline,
    )


@pytest.fixture
def dumps_model() -> Callable:
    return yatiml.dumps_function(
        Model,
        Component,
        Conduit,
        ConduitFilter,
        Identifier,
        Implementation,
        MatchingTimelines,
        MulticastConduit,
        Ports,
        Reference,
        SettingType,
        SupportedSetting,
        SupportedSettings,
        Timeline,
    )


def test_conduit_filter() -> None:
    assert ConduitFilter.LAST.is_reducer()
    assert ConduitFilter.REPEAT.is_repeater()
    assert ConduitFilter.PAD.is_repeater()


def test_conduit_order() -> None:
    Conduit("a", "b", "last last")
    Conduit("a", "b", "last pad")
    Conduit("a", "b", "last repeat")
    Conduit("a", "b", "repeat repeat")
    Conduit("a", "b", "repeat pad")
    Conduit("a", "b", "pad pad")
    with pytest.raises(RuntimeError):
        Conduit("a", "b", "repeat last")
    with pytest.raises(RuntimeError):
        Conduit("a", "b", "pad last")
    with pytest.raises(RuntimeError):
        Conduit("a", "b", "pad repeat")


def test_conduit_access() -> None:
    conduit = Conduit("macro.out", "micro.in")

    assert str(conduit) == "Conduit(macro.out -> micro.in)"
    assert conduit == Conduit("macro.out", "micro.in")
    assert conduit != Conduit("micro.in", "macro.out")

    assert conduit.sending_component() == "macro"
    assert conduit.sending_port() == "out"
    assert conduit.receiving_component() == "micro"
    assert conduit.receiving_port() == "in"

    conduit = Conduit("out", "in")
    assert conduit.sending_component() == Reference([])
    assert conduit.receiving_component() == Reference([])


def test_load_plain_conduit() -> None:
    load = yatiml.load_function(Conduit, ConduitFilter)

    text = "sender: macro.out\nreceiver: micro.in\n"

    conduit = load(text)
    assert conduit.sender == "macro.out"
    assert conduit.receiver == "micro.in"


def test_load_model_conduit() -> None:
    load = yatiml.load_function(Conduit, ConduitFilter)

    text = "sender: out\nreceiver: in\n"

    conduit = load(text)
    assert conduit.sender == "out"
    assert conduit.receiver == "in"


def test_load_filtered_conduit() -> None:
    load = yatiml.load_function(Conduit, ConduitFilter)

    text = "sender: micro1.final\nreceiver: micro2.init\nfilters: last pad\n"

    conduit = load(text)
    assert conduit.sender == "micro1.final"
    assert conduit.receiver == "micro2.init"
    assert conduit.filters == [ConduitFilter.LAST, ConduitFilter.PAD]


def test_load_invalid_filter() -> None:
    load = yatiml.load_function(Conduit, ConduitFilter)

    text = "sender: micro1.final\nreceiver: micro2.init\nfilters: convert-data-format\n"

    with pytest.raises(yatiml.RecognitionError):
        load(text)


def test_dump_conduit() -> None:
    dumps = yatiml.dumps_function(Conduit, ConduitFilter, Reference)
    conduit = Conduit("c1.out", "c2.in", [ConduitFilter.LAST, ConduitFilter.REPEAT])
    text = dumps(conduit)

    assert text == ("sender: c1.out\nreceiver: last repeat c2.in\n")


def test_multicast_conduits() -> None:
    c1 = Conduit("macro.out", "micro.init")
    mc1 = MulticastConduit("micro.final", ["macro.in", "micro2.init"])
    m = Model("test_model", None, "description", None, [], None, [c1, mc1])

    assert m.conduits[0] is c1
    assert m.conduits[1].sender == "micro.final"
    assert m.conduits[1].receiver == "macro.in"
    assert m.conduits[2].sender == "micro.final"
    assert m.conduits[2].receiver == "micro2.init"


def test_load_multicast_conduits() -> None:
    load = yatiml.load_function(MulticastConduit)

    text = "sender: init.out\nreceiver:\n- c1.in\n- repeat pad c2.in\n"

    conduit = load(text)

    assert conduit.sender == "init.out"
    assert conduit.receiver == ["c1.in", "repeat pad c2.in"]
    assert conduit.as_conduits() == [
        Conduit("init.out", "c1.in"),
        Conduit("init.out", "c2.in", [ConduitFilter.REPEAT, ConduitFilter.PAD]),
    ]


def test_load_multicast_invalid_filter() -> None:
    load = yatiml.load_function(MulticastConduit)

    text = "sender: init.out\nreceiver:\n- c1.in\n- convert_data_format c2.in\n"

    mc_conduit = load(text)
    with pytest.raises(RuntimeError):
        mc_conduit.as_conduits()


def test_dump_multicast_conduits() -> None:
    dump = yatiml.dumps_function(MulticastConduit)

    conduit = MulticastConduit("init.out", ["c1.in", "repeat pad c2.in"])
    text = dump(conduit)

    assert text == ("sender: init.out\nreceiver:\n- c1.in\n- repeat pad c2.in\n")


def test_create_matching_timelines() -> None:
    mt = MatchingTimelines(Timeline("tl1"), "tl2")
    assert isinstance(mt.head, Timeline)
    assert mt.head == Timeline("tl1")
    assert isinstance(mt.matches, set)
    assert mt.matches == {Timeline("tl1"), Timeline("tl2")}

    mt = MatchingTimelines(Timeline("tl1"), ["tl2", "tl3"])
    assert isinstance(mt.head, Timeline)
    assert mt.head == Timeline("tl1")
    assert isinstance(mt.matches, set)
    assert mt.matches == {Timeline("tl1"), Timeline("tl2"), Timeline("tl3")}

    mt = MatchingTimelines(Timeline("tl1"), [Timeline("tl2")])
    assert isinstance(mt.head, Timeline)
    assert mt.head == Timeline("tl1")
    assert isinstance(mt.matches, set)
    assert mt.matches == {Timeline("tl1"), Timeline("tl2")}

    mt = MatchingTimelines(Timeline("tl1"), "tl2 tl4 tl5")
    assert isinstance(mt.head, Timeline)
    assert mt.head == Timeline("tl1")
    assert isinstance(mt.matches, set)
    assert mt.matches == {
        Timeline("tl1"),
        Timeline("tl2"),
        Timeline("tl4"),
        Timeline("tl5"),
    }


def test_copy_matching_timelines() -> None:
    tl1 = Timeline("tl1")
    tl2 = Timeline("tl2")
    mt1 = MatchingTimelines(tl1, [tl2])

    mt2 = copy(mt1)

    assert mt2.head is mt1.head
    assert mt2.matches is not mt1.matches
    for m2 in mt2.matches:
        assert len([m1 for m1 in mt1.matches if m1 is m2]) > 0


def test_merge_matching_timelines() -> None:
    mt1 = MatchingTimelines(Timeline("tl1"), "tl2")
    mt2 = MatchingTimelines(Timeline("tl2"), "tl3")

    mt1 |= mt2
    assert mt1.head == "tl1"
    assert mt1.matches == {Timeline("tl1"), Timeline("tl2"), Timeline("tl3")}

    mt3 = MatchingTimelines(Timeline("tl4"), "tl5")
    mt1 |= mt3
    assert mt1.head == "tl1"
    assert mt1.matches == {
        Timeline("tl1"),
        Timeline("tl2"),
        Timeline("tl3"),
        Timeline("tl4"),
        Timeline("tl5"),
    }

    mt4 = MatchingTimelines(Timeline("c1.c2.tl1"), "c1.c3.tl1")
    mt4 |= mt3
    assert mt4.head == "tl4"
    assert mt4.matches == {
        Timeline("tl4"),
        Timeline("tl5"),
        Timeline("c1.c2.tl1"),
        Timeline("c1.c3.tl1"),
    }


def test_load_matching_timelines() -> None:
    load = yatiml.load_function(MatchingTimelines, Timeline)

    text = "head: timeline1\nmatches: timeline2"
    mt = load(text)
    assert isinstance(mt.head, Timeline)
    assert mt.head == "timeline1"

    assert isinstance(mt.matches, set)
    assert all(isinstance(m, Timeline) for m in mt.matches)
    assert mt.matches == {Timeline("timeline1"), Timeline("timeline2")}

    for text in (
        "head: common\nmatches:\n- timeline1\n- timeline2",
        "head: common\nmatches: timeline1 timeline2",
    ):
        mt = load(text)
        assert isinstance(mt.head, Timeline)
        assert mt.head == "common"

        assert isinstance(mt.matches, set)
        assert all(isinstance(m, Timeline) for m in mt.matches)
        assert mt.matches == {
            Timeline("common"),
            Timeline("timeline1"),
            Timeline("timeline2"),
        }


def test_dump_matching_timelines() -> None:
    dumps = yatiml.dumps_function(MatchingTimelines, Timeline)

    mt = MatchingTimelines("timeline1", "timeline2")
    text = dumps(mt)
    assert text == "head: timeline1\nmatches: timeline2\n"

    mt = MatchingTimelines("common", ["timeline1", "timeline2"])
    text = dumps(mt)
    assert text == "head: common\nmatches: timeline1 timeline2\n"

    mt = MatchingTimelines("a", "b c d e f g")
    text = dumps(mt)
    assert text == "head: a\nmatches:\n- b\n- c\n- d\n- e\n- f\n- g\n"


def test_load_model(load_model: Callable, model_text: str) -> None:
    m = load_model(model_text)

    assert m.name == "test_model"
    assert m.ports is not None
    assert m.ports["in"] == Port(Identifier("in"), Operator.F_INIT, Timeline(""))
    assert m.ports["out"] == Port(Identifier("out"), Operator.O_F, Timeline(""))
    assert m.description == "Test model for loading/dumping\n"
    assert m.supported_settings is not None
    assert m.supported_settings["eta"].typ == SettingType.FLOAT
    assert m.components[Ref("ic")].name == Reference("ic")
    assert m.components[Ref("smc")].name == Reference("smc")
    assert m.components[Ref("bf")].name == Reference("bf")
    assert m.components[Ref("smc2bf")].name == Reference("smc2bf")
    assert m.components[Ref("bf2smc")].name == Reference("bf2smc")
    assert m.conduits[0].sender == Reference("ic.out")
    assert m.conduits[1].sender == Reference("smc.cell_positions")
    assert m.conduits[2].receiver == Reference("bf.initial_domain")
    assert m.conduits[3].receiver == Reference("bf2smc.in")
    assert m.conduits[4].sender == Reference("bf2smc.out")


def test_load_model_with_multicast_conduits(
    load_model: Callable, model_multicast_text: str
) -> None:
    m = load_model(model_multicast_text)

    assert m.conduits[0].sender == "a.out"
    assert m.conduits[0].receiver == "b.in"
    assert m.conduits[1].sender == "a.out"
    assert m.conduits[1].receiver == "c.in"


def test_load_model_with_filters(
    load_model: Callable, model_with_filters_text: str
) -> None:
    m = load_model(model_with_filters_text)

    assert m.name == "test_model_conduit_filters"
    assert m.ports is not None
    assert len(m.ports) == 0
    assert m.description == "Test model for loading/dumping conduit filters\n"
    assert m.supported_settings is None
    assert m.components[Ref("init")].name == Reference("init")
    assert m.components[Ref("macro1")].name == Reference("macro1")
    assert m.components[Ref("micro1")].name == Reference("micro1")
    assert m.components[Ref("macro2")].name == Reference("macro2")
    assert m.components[Ref("micro2")].name == Reference("micro2")

    assert m.conduits[0].sender == Reference("init.macro_out")
    assert m.conduits[0].receiver == Reference("macro1.init")
    assert m.conduits[0].filters == []
    assert m.conduits[1].sender == Reference("init.micro_out")
    assert m.conduits[1].receiver == Reference("micro1.init_state")
    assert m.conduits[1].filters == [ConduitFilter.PAD]
    assert m.conduits[5].sender == Reference("micro1.final_state")
    assert m.conduits[5].receiver == Reference("micro2.init_state")
    assert m.conduits[5].filters == [ConduitFilter.LAST, ConduitFilter.PAD]


def test_load_model_with_invalid_filters(load_model: Callable) -> None:
    text = (
        "name: test_model_with_invalid_filters\n"
        "description: Testing invalid filters\n"
        "conduits:\n"
        "  init.micro_out: invalid-filter micro1.init_state\n"
    )

    with pytest.raises(yatiml.RecognitionError):
        load_model(text)


def test_load_model_with_timelines(
    load_model: Callable, model_matching_timelines_text: str
) -> None:
    model = load_model(model_matching_timelines_text)

    assert model.matching_timelines is not None
    assert len(model.matching_timelines) == 1
    assert model.matching_timelines[0].head == Timeline("main")
    assert model.matching_timelines[0].matches == {
        Timeline("left"),
        Timeline("main"),
        Timeline("right"),
    }


def test_dump_model(dumps_model: Callable, model: Model, model_text: str) -> None:
    text = dumps_model(model)
    assert text == model_text


def test_dump_model_with_multicast_conduits(
    dumps_model: Callable, model_multicast: Model, model_multicast_text: str
) -> None:
    text = dumps_model(model_multicast)
    assert text == model_multicast_text


def test_dump_model_with_filters(
    dumps_model: Callable, model_with_filters: Model, model_with_filters_text: str
) -> None:
    text = dumps_model(model_with_filters)
    assert text == model_with_filters_text


def test_dump_model_with_matching_timelines(
    dumps_model: Callable,
    model_matching_timelines: Model,
    model_matching_timelines_text: str,
) -> None:
    text = dumps_model(model_matching_timelines)
    assert text == model_matching_timelines_text


def test_consistent() -> None:
    model_ports = Ports(f_init=["model_init"], o_f=["model_final"])

    macro_ports = Ports(f_init=["Minit"], o_i=["Mout"], s=["Min"], o_f=["Mfinal"])
    macro = Component("macro", macro_ports, "macro_impl")

    micro_ports = Ports(f_init=["minit"], o_f=["mfinal"])
    micro = Component("micro", micro_ports, "micro_impl")

    conduits = [
        Conduit("model_init", "macro.Minit"),
        Conduit("macro.Mout", "micro.minit"),
        Conduit("micro.mfinal", "macro.Min"),
        Conduit("macro.Mfinal", "model_final"),
    ]

    model = Model(
        "with_conduits",
        model_ports,
        "description",
        None,
        [macro, micro],
        None,
        conduits,
    )

    errors = model.check_consistent()
    assert not errors


def test_conduits_inconsistent() -> None:
    model_ports = Ports(f_init=["model_init"], o_f=["model_final"])

    macro_ports = Ports(f_init=["Minit"], o_i=["Mout"], s=["Min"], o_f=["Mfinal"])
    macro = Component("macro", macro_ports, "macro_impl")

    micro_ports = Ports(f_init=["minit"], o_f=["mfinal"])
    micro = Component("micro", micro_ports, "micro_impl")

    conduits = [
        Conduit("modelinit", "macro.Minit"),
        Conduit("macro.Mout", "micro.m_init"),
        Conduit("macro.Mout", "miicro.minit"),
        Conduit("macroo.Mout", "micro.minit"),
        Conduit("micro.m_final", "macro.Min"),
        Conduit("macro.Mfinal", "modelfinal"),
    ]

    model = Model(
        "bad_conduits", model_ports, "description", None, [macro, micro], None, conduits
    )

    errors = model.check_consistent()
    assert len(errors) == 6
