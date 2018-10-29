#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from ymmsl import ComputeElementDecl, Conduit, Identifier, Reference, Simulation

import pytest


def test_compute_element_declaration() -> None:
    test_decl = ComputeElementDecl(
            Identifier('test'), Reference.from_string('ns.model'))
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns.model'
    assert test_decl.count == 1
    assert str(test_decl) == 'test[1]'

    test_decl = ComputeElementDecl(
            Identifier('test'), Reference.from_string('ns2.model2'), 2)
    assert isinstance(test_decl.name, Identifier)
    assert str(test_decl.name) == 'test'
    assert str(test_decl.implementation) == 'ns2.model2'
    assert test_decl.count == 2
    assert str(test_decl) == 'test[2]'

    with pytest.raises(ValueError):
        test_decl = ComputeElementDecl(
                Identifier('test'), Reference.from_string('ns2.model2[1]'))


def test_conduit() -> None:
    test_ref = Reference.from_string('submodel1.port1')
    test_ref2 = Reference.from_string('submodel2.port2')
    test_conduit = Conduit(test_ref, test_ref2)
    assert str(test_conduit.sender.parts[0]) == 'submodel1'
    assert str(test_conduit.sender.parts[1]) == 'port1'
    assert str(test_conduit.receiver.parts[0]) == 'submodel2'
    assert str(test_conduit.receiver.parts[1]) == 'port2'

    assert str(test_conduit.sending_compute_element()) == 'submodel1'
    assert str(test_conduit.sending_port()) == 'port1'
    assert str(test_conduit.receiving_compute_element()) == 'submodel2'
    assert str(test_conduit.receiving_port()) == 'port2'


def test_simulation() -> None:
    macro = ComputeElementDecl(
            Identifier('macro'), Reference.from_string('my.macro'))
    micro = ComputeElementDecl(
            Identifier('micro'), Reference.from_string('my.micro'))
    comp_els = [macro, micro]
    conduit1 = Conduit(Reference.from_string('macro.intermediate_state'),
                       Reference.from_string('micro.initial_state'))
    conduit2 = Conduit(Reference.from_string('micro.final_state'),
                       Reference.from_string('macro.state_update'))
    conduits = [conduit1, conduit2]
    sim = Simulation(Identifier('test_sim'), comp_els, conduits)

    assert str(sim.name) == 'test_sim'
    assert sim.compute_elements == comp_els
    assert sim.conduits == conduits
