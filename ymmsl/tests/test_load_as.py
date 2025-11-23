from typing import cast, List

from ymmsl.io import load_as
import ymmsl.v0_1 as v0_1
import ymmsl.v0_2 as v0_2


def test_load_as_v0_1(test_yaml1: str) -> None:
    config = load_as(v0_1.PartialConfiguration, test_yaml1)
    assert isinstance(config, v0_1.PartialConfiguration)
    assert cast(List[int], config.settings['test_list'])[0] == 12.3


def test_load_as_v0_2(test_yaml1: str) -> None:
    config = load_as(v0_2.Configuration, test_yaml1)
    assert isinstance(config, v0_2.Configuration)
    assert config.settings['test_str'] == 'value'
