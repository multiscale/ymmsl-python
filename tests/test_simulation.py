#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from ymmsl import ComputeElementDecl, Conduit, Identifier, Reference, Simulation

import pytest
import yatiml
from ruamel import yaml


def test_compute_element_declaration() -> None:
    test_decl = ComputeElementDecl(
            Reference('test'), Reference('ns.model'))
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns.model'
    assert test_decl.multiplicity == []
    assert str(test_decl) == 'test'

    test_decl = ComputeElementDecl(
            Reference('test'), Reference('ns2.model2'), [1, 2])
    assert isinstance(test_decl.name, Reference)
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns2.model2'
    assert test_decl.multiplicity == [1, 2]
    assert str(test_decl) == 'test[1][2]'

    with pytest.raises(ValueError):
        test_decl = ComputeElementDecl(
                Reference('test'), Reference('ns2.model2[1]'))


def test_conduit() -> None:
    test_ref = Reference('submodel1.port1')
    test_ref2 = Reference('submodel2.port2')
    test_conduit = Conduit(test_ref, test_ref2)
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
        Conduit(Reference('x'), test_ref)

    with pytest.raises(ValueError):
        Conduit(Reference('x[3].y.z'), test_ref)

    with pytest.raises(ValueError):
        Conduit(Reference('x[3]'), test_ref)

    test_conduit2 = Conduit(test_ref, test_ref2)
    assert test_conduit == test_conduit2

    test_conduit3 = Conduit(Reference('submodel1.port1'),
                            Reference('submodel2.port2'))
    assert test_conduit == test_conduit3

    assert 'Conduit' in str(test_conduit)
    assert 'submodel1.port1' in str(test_conduit)
    assert 'submodel2.port2' in str(test_conduit)

    test_conduit4 = Conduit(Reference('x.y[1][2]'), Reference('a.b[3]'))
    assert test_conduit4.sender[2] == 1
    assert test_conduit4.sender[3] == 2
    assert str(test_conduit4.sending_compute_element()) == 'x'
    assert str(test_conduit4.sending_port()) == 'y'
    assert test_conduit4.sending_slot() == [1, 2]
    assert test_conduit4.receiver[2] == 3
    assert str(test_conduit4.receiving_compute_element()) == 'a'
    assert str(test_conduit4.receiving_port()) == 'b'
    assert test_conduit4.receiving_slot() == [3]


def test_simulation() -> None:
    macro = ComputeElementDecl(
            Reference('macro'), Reference('my.macro'))
    micro = ComputeElementDecl(
            Reference('micro'), Reference('my.micro'))
    comp_els = [macro, micro]
    conduit1 = Conduit(Reference('macro.intermediate_state'),
                       Reference('micro.initial_state'))
    conduit2 = Conduit(Reference('micro.final_state'),
                       Reference('macro.state_update'))
    conduits = [conduit1, conduit2]
    sim = Simulation(Identifier('test_sim'), comp_els, conduits)

    assert str(sim.name) == 'test_sim'
    assert sim.compute_elements == comp_els
    assert sim.conduits == conduits


def test_load_simulation() -> None:
    class Loader(yatiml.Loader):
        pass

    yatiml.add_to_loader(Loader, [ComputeElementDecl, Conduit, Identifier,
                                  Reference, Simulation])
    yatiml.set_document_type(Loader, Simulation)

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
    simulation = yaml.load(text, Loader=Loader)
    assert str(simulation.name) == 'test_model'
    assert len(simulation.compute_elements) == 5
    assert str(simulation.compute_elements[2].implementation) == 'isr2d.blood_flow'
    assert str(simulation.compute_elements[4].name) == 'bf2smc'

    assert len(simulation.conduits) == 5
    assert str(simulation.conduits[0].sending_compute_element()) == 'ic'
    assert str(simulation.conduits[0].sending_port()) == 'out'
    assert str(simulation.conduits[3].receiving_compute_element()) == 'bf2smc'
    assert str(simulation.conduits[3].receiving_port()) == 'in'


def test_dump_simulation() -> None:
    class Dumper(yatiml.Dumper):
        pass

    yatiml.add_to_dumper(Dumper, [ComputeElementDecl, Conduit, Identifier,
                                  Reference, Simulation])

    impl1 = Reference('test.impl1')
    impl2 = Reference('test.impl2')
    ce1 = ComputeElementDecl(Reference('ce1'), impl1)
    ce2 = ComputeElementDecl(Reference('ce2'), impl2)
    ce1_out = Reference('ce1.state_out')
    ce2_in = Reference('ce2.init_in')
    ce2_out = Reference('ce2.fini_out')
    ce1_in = Reference('ce1.boundary_in')
    cd1 = Conduit(ce1_out, ce2_in)
    cd2 = Conduit(ce2_out, ce1_in)
    simulation = Simulation(Identifier('test_sim'), [ce1, ce2], [cd1, cd2])

    text = yaml.dump(simulation, Dumper=Dumper)
    print(text)
    assert text == ('name: test_sim\n'
                    'compute_elements:\n'
                    '  ce1: test.impl1\n'
                    '  ce2: test.impl2\n'
                    'conduits:\n'
                    '  ce1.state_out: ce2.init_in\n'
                    '  ce2.fini_out: ce1.boundary_in\n'
                    )
