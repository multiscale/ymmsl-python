from collections import OrderedDict

import pytest

from ymmsl import (ComputeElement, Conduit, Identifier, Model, ModelReference,
                   Settings, YmmslDocument)


@pytest.fixture
def test_yaml1() -> str:
    text = ('version: v0.1\n'
            'settings:\n'
            '  parameter_values:\n'
            '    test_str: value\n'
            '    test_int: 13\n'
            '    test_list: [12.3, 1.3]\n'
            )
    return text


@pytest.fixture
def test_doc1() -> YmmslDocument:
    settings = Settings(OrderedDict([
        ('test_str', 'value'),
        ('test_int', 13),
        ('test_list', [12.3, 1.3])]))
    return YmmslDocument('v0.1', None, settings)


@pytest.fixture
def test_yaml2() -> str:
    text = ('version: v0.1\n'
            'model:\n'
            '  name: test_model\n'
            '  compute_elements:\n'
            '    ic: isr2d.initial_conditions\n'
            '    smc: isr2d.smc\n'
            '    bf: isr2d.blood_flow\n'
            '    smc2bf: isr2d.smc2bf\n'
            '    bf2smc: isr2d.bf2smc\n'
            '  conduits:\n'
            '    ic.out: smc.initial_state\n'
            '    smc.cell_positions: smc2bf.in\n'
            '    smc2bf.out: bf.initial_domain\n'
            '    bf.wss_out: bf2smc.in\n'
            '    bf2smc.out: smc.wss_in\n')
    return text


@pytest.fixture
def test_doc2() -> YmmslDocument:
    model = Model(
            Identifier('test_model'),
            [
                ComputeElement('ic', 'isr2d.initial_conditions'),
                ComputeElement('smc', 'isr2d.smc'),
                ComputeElement('bf', 'isr2d.blood_flow'),
                ComputeElement('smc2bf', 'isr2d.smc2bf'),
                ComputeElement('bf2smc', 'isr2d.bf2smc')],
            [
                Conduit('ic.out', 'smc.initial_state'),
                Conduit('smc.cell_positions', 'smc2bf.in'),
                Conduit('smc2bf.out', 'bf.initial_domain'),
                Conduit('bf.wss_out', 'bf2smc.in'),
                Conduit('bf2smc.out', 'smc.wss_in')])
    return YmmslDocument('v0.1', model)


@pytest.fixture
def test_yaml3() -> str:
    text = ('version: v0.1\n'
            'model:\n'
            '  name: test_model\n')
    return text


@pytest.fixture
def test_doc3() -> YmmslDocument:
    model = ModelReference(Identifier('test_model'))
    return YmmslDocument('v0.1', model)
