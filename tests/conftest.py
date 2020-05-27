from collections import OrderedDict

import pytest

from ymmsl import (Component, Conduit, Configuration, Model,
                   ModelReference, Settings)


@pytest.fixture
def test_yaml1() -> str:
    text = ('ymmsl_version: v0.1\n'
            'settings:\n'
            '  test_str: value\n'
            '  test_int: 13\n'
            '  test_list: [12.3, 1.3]\n'
            )
    return text


@pytest.fixture
def test_config1() -> Configuration:
    settings = Settings(OrderedDict([
        ('test_str', 'value'),
        ('test_int', 13),
        ('test_list', [12.3, 1.3])]))
    return Configuration(None, settings)


@pytest.fixture
def test_yaml2() -> str:
    text = ('ymmsl_version: v0.1\n'
            'model:\n'
            '  name: test_model\n'
            '  components:\n'
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
def test_config2() -> Configuration:
    model = Model(
            'test_model',
            [
                Component('ic', 'isr2d.initial_conditions'),
                Component('smc', 'isr2d.smc'),
                Component('bf', 'isr2d.blood_flow'),
                Component('smc2bf', 'isr2d.smc2bf'),
                Component('bf2smc', 'isr2d.bf2smc')],
            [
                Conduit('ic.out', 'smc.initial_state'),
                Conduit('smc.cell_positions', 'smc2bf.in'),
                Conduit('smc2bf.out', 'bf.initial_domain'),
                Conduit('bf.wss_out', 'bf2smc.in'),
                Conduit('bf2smc.out', 'smc.wss_in')])
    return Configuration(model)


@pytest.fixture
def test_yaml3() -> str:
    text = ('ymmsl_version: v0.1\n'
            'model:\n'
            '  name: test_model\n')
    return text


@pytest.fixture
def test_config3() -> Configuration:
    model = ModelReference('test_model')
    return Configuration(model)
