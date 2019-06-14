from collections import OrderedDict
from typing import Any, List  # noqa: F401

from ymmsl import (ParameterValue, Reference, Settings, YmmslDocument, load)  # noqa: F401


def test_ymmsl() -> None:
    parameter_values = OrderedDict()    # type: OrderedDict[str, ParameterValue]
    settings = Settings(parameter_values)
    doc = YmmslDocument('v0.1', None, settings)
    assert isinstance(doc.settings, Settings)
    assert len(doc.settings) == 0
