from collections import OrderedDict
from typing import Any, List  # noqa: F401

from ymmsl import (Configuration, SettingValue, Reference, Settings, load)  # noqa: F401


def test_configuration() -> None:
    setting_values = OrderedDict()    # type: OrderedDict[str, SettingValue]
    settings = Settings(setting_values)
    config = Configuration(None, settings)
    assert isinstance(config.settings, Settings)
    assert len(config.settings) == 0
