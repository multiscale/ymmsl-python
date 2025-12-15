import pytest

from ymmsl.conversion.converter import convert_to

import ymmsl.v0_1 as v0_1
import ymmsl.v0_2 as v0_2


def test_convert_to_no_change(full_config: v0_1.PartialConfiguration) -> None:
    new_config = convert_to(v0_1.PartialConfiguration, full_config)
    assert isinstance(new_config, v0_1.PartialConfiguration)
    # quick sanity check, conversion checks are specific to each version
    assert new_config.settings['a'] == 42


@pytest.mark.filterwarnings('ignore:.*specify the ports.*')
def test_convert_to(full_config: v0_1.PartialConfiguration) -> None:
    new_config = convert_to(v0_2.Configuration, full_config)
    assert isinstance(new_config, v0_2.Configuration)
    # quick sanity check, conversion checks are specific to each version
    assert new_config.settings['a'] == 42
