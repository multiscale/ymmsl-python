from collections import OrderedDict
from typing import Any, List  # noqa: F401

from ymmsl import (Configuration, ParameterValue, Reference, Settings, load)  # noqa: F401


def test_configuration() -> None:
    parameter_values = OrderedDict()    # type: OrderedDict[str, ParameterValue]
    settings = Settings(parameter_values)
    config = Configuration(None, settings)
    assert isinstance(config.settings, Settings)
    assert len(config.settings) == 0
