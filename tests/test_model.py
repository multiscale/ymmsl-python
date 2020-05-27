from typing_extensions import Type

from ymmsl import (ComputeElement, Conduit, Identifier, Model, ModelReference,
                   Reference)

import pytest
import yatiml
from ruamel import yaml


@pytest.fixture
def model_loader() -> Type:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [ComputeElement, Conduit, Identifier,
                                  Model, Reference])
    yatiml.set_document_type(Loader, Model)
    return Loader


@pytest.fixture
def model_dumper() -> Type:
    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [ComputeElement, Conduit, Identifier,
                                  Model, Reference])
    return Dumper


def test_compute_element_declaration() -> None:
    test_decl = ComputeElement('test', 'ns.model')
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns.model'
    assert test_decl.multiplicity == []
    assert str(test_decl) == 'test'

    test_decl = ComputeElement('test', 'ns.model', 10)
    assert isinstance(test_decl.name, Reference)
    assert str(test_decl.name) == 'test'
    assert test_decl.multiplicity == [10]
    assert str(test_decl) == 'test[10]'

    test_decl = ComputeElement('test', 'ns2.model2', [1, 2])
    assert isinstance(test_decl.name, Reference)
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns2.model2'
    assert test_decl.multiplicity == [1, 2]
    assert str(test_decl) == 'test[1][2]'

    with pytest.raises(ValueError):
        test_decl = ComputeElement('test', 'ns2.model2[1]')


def test_conduit() -> None:
    test_conduit = Conduit('submodel1.port1', 'submodel2.port2')
    assert str(test_conduit.sender[0]) == 'submodel1'
    assert str(test_conduit.sender[1]) == 'port1'
    assert str(test_conduit.receiver[0]) == 'submodel2'
    assert str(test_conduit.receiver[1]) == 'port2'

    assert str(test_conduit.sending_compute_element()) == 'submodel1'
    assert str(test_conduit.sending_port()) == 'port1'
    assert test_conduit.sending_slot() == []
    assert str(test_conduit.receiving_compute_element()) == 'submodel2'
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
    assert str(test_conduit4.sending_compute_element()) == 'x'
    assert str(test_conduit4.sending_port()) == 'y'
    assert test_conduit4.sending_slot() == [1, 2]
    assert test_conduit4.receiver[2] == 3
    assert str(test_conduit4.receiving_compute_element()) == 'a'
    assert str(test_conduit4.receiving_port()) == 'b'
    assert test_conduit4.receiving_slot() == [3]


def test_load_model_reference() -> None:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [ComputeElement, Conduit, Identifier,
                                  Model, ModelReference, Reference])
    yatiml.set_document_type(Loader, ModelReference)

    text = 'name: test_model\n'
    model = yaml.load(text, Loader=Loader)
    assert isinstance(model, ModelReference)
    assert str(model.name) == 'test_model'

    text = ('name: test_model\n'
            'compute_elements:\n'
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
    model = yaml.load(text, Loader=Loader)
    assert isinstance(model, Model)
    assert str(model.name) == 'test_model'


def test_model() -> None:
    macro = ComputeElement('macro', 'my.macro')
    micro = ComputeElement('micro', 'my.micro')
    comp_els = [macro, micro]
    conduit1 = Conduit('macro.intermediate_state', 'micro.initial_state')
    conduit2 = Conduit('micro.final_state', 'macro.state_update')
    conduits = [conduit1, conduit2]
    model = Model('test_sim', comp_els, conduits)

    assert str(model.name) == 'test_sim'
    assert model.compute_elements == comp_els
    assert model.conduits == conduits


def test_load_model(model_loader: Type) -> None:
    text = ('name: test_model\n'
            'compute_elements:\n'
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
    model = yaml.load(text, Loader=model_loader)
    assert str(model.name) == 'test_model'
    assert len(model.compute_elements) == 5
    assert str(model.compute_elements[2].implementation) == 'isr2d.blood_flow'
    assert str(model.compute_elements[4].name) == 'bf2smc'

    assert len(model.conduits) == 5
    assert str(model.conduits[0].sending_compute_element()) == 'ic'
    assert str(model.conduits[0].sending_port()) == 'out'
    assert str(model.conduits[3].receiving_compute_element()) == 'bf2smc'
    assert str(model.conduits[3].receiving_port()) == 'in'


def test_load_no_conduits(model_loader: Type) -> None:
    text = ('name: test_model\n'
            'compute_elements:\n'
            '  smc: isr2d.smc\n'
            )

    model = yaml.load(text, Loader=model_loader)
    assert str(model.name) == 'test_model'
    assert len(model.compute_elements) == 1
    assert str(model.compute_elements[0].name) == 'smc'
    assert str(model.compute_elements[0].implementation) == 'isr2d.smc'
    assert isinstance(model.conduits, list)
    assert len(model.conduits) == 0


def test_dump_model(model_dumper: Type) -> None:
    ce1 = ComputeElement('ce1', 'test.impl1')
    ce2 = ComputeElement('ce2', 'test.impl2')
    cd1 = Conduit('ce1.state_out', 'ce2.init_in')
    cd2 = Conduit('ce2.fini_out', 'ce1.boundary_in')
    model = Model('test_model', [ce1, ce2], [cd1, cd2])

    text = yaml.dump(model, Dumper=model_dumper)
    assert text == ('name: test_model\n'
                    'compute_elements:\n'
                    '  ce1: test.impl1\n'
                    '  ce2: test.impl2\n'
                    'conduits:\n'
                    '  ce1.state_out: ce2.init_in\n'
                    '  ce2.fini_out: ce1.boundary_in\n'
                    )


def test_dump_no_conduits(model_dumper: Type) -> None:
    ce1 = ComputeElement('ce1', 'test.impl1')
    model = Model('test_model', [ce1])

    text = yaml.dump(model, Dumper=model_dumper)
    assert text == ('name: test_model\n'
                    'compute_elements:\n'
                    '  ce1: test.impl1\n'
                    )
