from typing import Callable

import pytest
import yatiml

from ymmsl import (Component, Conduit, Identifier, Model, ModelReference,
                   Reference)


@pytest.fixture
def load_model() -> Callable:
    return yatiml.load_function(
            Model, Component, Conduit, Identifier, Reference)


@pytest.fixture
def dump_model() -> Callable:
    return yatiml.dumps_function(
            Component, Conduit, Identifier, Model, Reference)


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
    assert str(test_decl) == 'test[10]'

    test_decl = Component('test', 'ns2.model2', [1, 2])
    assert isinstance(test_decl.name, Reference)
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns2.model2'
    assert test_decl.multiplicity == [1, 2]
    assert str(test_decl) == 'test[1][2]'

    with pytest.raises(ValueError):
        test_decl = Component('test', 'ns2.model2[1]')


def test_conduit() -> None:
    test_conduit = Conduit('submodel1.port1', 'submodel2.port2')
    assert str(test_conduit.sender[0]) == 'submodel1'
    assert str(test_conduit.sender[1]) == 'port1'
    assert str(test_conduit.receiver[0]) == 'submodel2'
    assert str(test_conduit.receiver[1]) == 'port2'

    assert str(test_conduit.sending_component()) == 'submodel1'
    assert str(test_conduit.sending_port()) == 'port1'
    assert test_conduit.sending_slot() == []
    assert str(test_conduit.receiving_component()) == 'submodel2'
    assert str(test_conduit.receiving_port()) == 'port2'
    assert test_conduit.receiving_slot() == []

    with pytest.raises(ValueError):
        Conduit('x', 'submodel1.port1')

    with pytest.raises(ValueError):
        Conduit('x[3].y.z', 'submodel1.port1')

    with pytest.raises(ValueError):
        Conduit('x[3]', 'submodel1.port1')

    test_conduit2 = Conduit('submodel1.port1', 'submodel2.port2')
    assert test_conduit == test_conduit2

    assert 'Conduit' in str(test_conduit)
    assert 'submodel1.port1' in str(test_conduit)
    assert 'submodel2.port2' in str(test_conduit)

    test_conduit4 = Conduit('x.y[1][2]', 'a.b[3]')
    assert test_conduit4.sender[2] == 1
    assert test_conduit4.sender[3] == 2
    assert str(test_conduit4.sending_component()) == 'x'
    assert str(test_conduit4.sending_port()) == 'y'
    assert test_conduit4.sending_slot() == [1, 2]
    assert test_conduit4.receiver[2] == 3
    assert str(test_conduit4.receiving_component()) == 'a'
    assert str(test_conduit4.receiving_port()) == 'b'
    assert test_conduit4.receiving_slot() == [3]


def test_load_model_reference() -> None:
    load = yatiml.load_function(
            ModelReference, Component, Conduit, Identifier, Model,
            ModelReference, Reference)

    text = 'name: test_model\n'
    model = load(text)
    assert isinstance(model, ModelReference)
    assert str(model.name) == 'test_model'

    text = ('name: test_model\n'
            'components:\n'
            '  ic: isr2d.initial_conditions\n'
            '  smc: isr2d.smc\n'
            '  bf: isr2d.blood_flow\n'
            '  smc2bf: isr2d.smc2bf\n'
            '  bf2smc: isr2d.bf2smc\n'
            'conduits:\n'
            '  ic.out: smc.initial_state\n'
            '  smc.cell_positions: smc2bf.in\n'
            '  smc2bf.out: bf.initial_domain\n'
            '  bf.wss_out: bf2smc.in\n'
            '  bf2smc.out: smc.wss_in\n'
            )
    model = load(text)
    assert isinstance(model, Model)
    assert str(model.name) == 'test_model'


def test_model() -> None:
    macro = Component('macro', 'my.macro')
    micro = Component('micro', 'my.micro')
    components = [macro, micro]
    conduit1 = Conduit('macro.intermediate_state', 'micro.initial_state')
    conduit2 = Conduit('micro.final_state', 'macro.state_update')
    conduits = [conduit1, conduit2]
    model = Model('test_sim', components, conduits)

    assert str(model.name) == 'test_sim'
    assert model.components == components
    assert model.conduits == conduits


def test_model_update_add_component() -> None:
    macro = Component('macro', 'my.macro')
    base = Model('test_update', [macro])

    micro = Component('micro', 'my.micro')
    conduit1 = Conduit('macro.intermediate_state', 'micro.initial_state')
    conduit2 = Conduit('micro.final_state', 'macro.state_update')
    conduits = [conduit1, conduit2]
    overlay = Model('test_update_add', [micro], conduits)

    base.update(overlay)

    assert len(base.components) == 2
    assert macro in base.components
    assert micro in base.components
    assert conduit1 in base.conduits
    assert conduit2 in base.conduits


def test_model_update_insert_component_on_conduit() -> None:
    macro = Component('macro', 'my.macro')
    micro = Component('micro', 'my.micro')
    components = [macro, micro]
    conduit1 = Conduit('macro.intermediate_state', 'micro.initial_state')
    conduit2 = Conduit('micro.final_state', 'macro.state_update')
    conduits = [conduit1, conduit2]
    base = Model('test_update', components, conduits)

    tee = Component('tee', 'muscle3.tee')
    conduit3 = Conduit('macro.intermediate_state', 'tee.input')
    conduit4 = Conduit('tee.output', 'micro.initial_state')
    overlay = Model('test_update_tee', [tee], [conduit3, conduit4])

    base.update(overlay)

    assert len(base.components) == 3
    assert macro in base.components
    assert micro in base.components
    assert tee in base.components

    assert len(base.conduits) == 3
    assert conduit2 in base.conduits
    assert conduit3 in base.conduits
    assert conduit4 in base.conduits


def test_model_update_replace_component() -> None:
    macro = Component('macro', 'my.macro')
    micro = Component('micro', 'my.micro')
    components = [macro, micro]
    conduit1 = Conduit('macro.intermediate_state', 'micro.initial_state')
    conduit2 = Conduit('micro.final_state', 'macro.state_update')
    conduits = [conduit1, conduit2]
    base = Model('test_update', components, conduits)

    surrogate = Component('micro', 'my.surrogate')
    overlay = Model('test_update_surrogate', [surrogate])

    base.update(overlay)

    assert len(base.components) == 2
    assert macro in base.components
    assert surrogate in base.components

    assert len(base.conduits) == 2
    assert conduit1 in base.conduits
    assert conduit2 in base.conduits


def test_load_model(load_model: Callable) -> None:
    text = ('name: test_model\n'
            'components:\n'
            '  ic: isr2d.initial_conditions\n'
            '  smc: isr2d.smc\n'
            '  bf: isr2d.blood_flow\n'
            '  smc2bf: isr2d.smc2bf\n'
            '  bf2smc: isr2d.bf2smc\n'
            'conduits:\n'
            '  ic.out: smc.initial_state\n'
            '  smc.cell_positions: smc2bf.in\n'
            '  smc2bf.out: bf.initial_domain\n'
            '  bf.wss_out: bf2smc.in\n'
            '  bf2smc.out: smc.wss_in\n'
            )
    model = load_model(text)
    assert str(model.name) == 'test_model'
    assert len(model.components) == 5
    assert str(model.components[2].implementation) == 'isr2d.blood_flow'
    assert str(model.components[4].name) == 'bf2smc'

    assert len(model.conduits) == 5
    assert str(model.conduits[0].sending_component()) == 'ic'
    assert str(model.conduits[0].sending_port()) == 'out'
    assert str(model.conduits[3].receiving_component()) == 'bf2smc'
    assert str(model.conduits[3].receiving_port()) == 'in'


def test_load_no_conduits(load_model: Callable) -> None:
    text = ('name: test_model\n'
            'components:\n'
            '  smc: isr2d.smc\n'
            )

    model = load_model(text)
    assert str(model.name) == 'test_model'
    assert len(model.components) == 1
    assert str(model.components[0].name) == 'smc'
    assert str(model.components[0].implementation) == 'isr2d.smc'
    assert isinstance(model.conduits, list)
    assert len(model.conduits) == 0


def test_dump_model(dump_model: Callable) -> None:
    ce1 = Component('ce1', 'test.impl1')
    ce2 = Component('ce2', 'test.impl2')
    cd1 = Conduit('ce1.state_out', 'ce2.init_in')
    cd2 = Conduit('ce2.fini_out', 'ce1.boundary_in')
    model = Model('test_model', [ce1, ce2], [cd1, cd2])

    text = dump_model(model)
    assert text == ('name: test_model\n'
                    'components:\n'
                    '  ce1: test.impl1\n'
                    '  ce2: test.impl2\n'
                    'conduits:\n'
                    '  ce1.state_out: ce2.init_in\n'
                    '  ce2.fini_out: ce1.boundary_in\n'
                    )


def test_dump_no_conduits(dump_model: Callable) -> None:
    ce1 = Component('ce1', 'test.impl1')
    model = Model('test_model', [ce1])

    text = dump_model(model)
    assert text == ('name: test_model\n'
                    'components:\n'
                    '  ce1: test.impl1\n'
                    )
