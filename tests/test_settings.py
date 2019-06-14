from ymmsl import Identifier, ParameterValue, Reference, Settings

from collections import OrderedDict
from typing import cast, List
import yatiml
from ruamel import yaml


def test_settings() -> None:
    parameter_values = OrderedDict([
        ('submodel._muscle_grain', [0.01, 0.01]),
        ('submodel._muscle_extent', [10.0, 3.0]),
        ('submodel._muscle_timestep', 0.001),
        ('submodel._muscle_total_time', 0.1),
        ('bf.velocity', 0.48),
        ('init.max_depth', 0.11)
        ])  # type: OrderedDict[str, ParameterValue]
    settings = Settings(parameter_values)
    assert list(settings.ordered_items()[0][0]) == [
        'submodel', '_muscle_grain'
    ]
    assert cast(List[float], settings.ordered_items()[1][1])[1] == 3.0
    assert settings['submodel._muscle_timestep'] == 0.001
    assert list(settings.ordered_items()[4][0]) == ['bf', 'velocity']
    assert settings['init.max_depth'] == 0.11


def test_load_settings() -> None:
    class Loader(yatiml.Loader):
        pass

    # The below fails mypy on Travis with
    # List item 1 has incompatible type "Type[Reference]"; expected "ABCMeta"
    # Overrode, no idea where to start looking...
    yatiml.add_to_loader(Loader, [Identifier, Reference, Settings])     # type: ignore
    yatiml.set_document_type(Loader, Settings)

    text = ('domain1._muscle_grain: [0.01]\n'
            'domain1._muscle_extent: [1.5]\n'
            'submodel1._muscle_timestep: 0.001\n'
            'submodel1._muscle_total_time: 100.0\n'
            'test_str: value\n'
            'test_int: 13\n'
            'test_bool: true\n'
            'test_list: [12.3, 1.3]\n')

    settings = yaml.load(text, Loader=Loader)
    assert len(settings) == 8
    assert str(settings.ordered_items()[0][0]) == 'domain1._muscle_grain'
    assert settings['domain1._muscle_grain'][0] == 0.01
    assert settings['submodel1._muscle_total_time'] == 100.0

    assert str(settings.ordered_items()[4][0]) == 'test_str'
    assert ([str(s[0]) for s in settings.ordered_items()]
            == ['domain1._muscle_grain', 'domain1._muscle_extent',
                'submodel1._muscle_timestep', 'submodel1._muscle_total_time',
                'test_str', 'test_int', 'test_bool', 'test_list'])
    assert settings['test_bool'] is True
    assert settings['test_list'] == [12.3, 1.3]


def test_dump_settings() -> None:
    class Dumper(yatiml.Dumper):
        pass

    # The below fails mypy on Travis with
    # List item 1 has incompatible type "Type[Reference]"; expected "ABCMeta"
    # Overrode, no idea where to start looking...
    yatiml.add_to_dumper(Dumper, [Identifier, Reference, Settings])     # type: ignore

    settings = Settings(OrderedDict([
            ('domain1._muscle_grain', [0.01]),
            ('domain1._muscle_extent', [1.5]),
            ('submodel1._muscle_timestep', 0.001),
            ('submodel1._muscle_total_time', 100.0),
            ('test_str', 'value'),
            ('test_int', 12),
            ('test_bool', True),
            ('test_list', [12.3, 1.3])]))

    text = yaml.dump(settings, Dumper=Dumper)
    assert text == ('domain1._muscle_grain: [0.01]\n'
                    'domain1._muscle_extent: [1.5]\n'
                    'submodel1._muscle_timestep: 0.001\n'
                    'submodel1._muscle_total_time: 100.0\n'
                    'test_str: value\n'
                    'test_int: 12\n'
                    'test_bool: true\n'
                    'test_list: [12.3, 1.3]\n')
