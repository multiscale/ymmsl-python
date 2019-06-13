#!/usr/bin/env python
"""Tests for the ymmsl module.
"""

from typing import Any, List  # noqa: F401

from ymmsl import (Reference, Setting, Settings, YmmslDocument,
                   load)  # noqa: F401


def test_ymmsl() -> None:
    parameter_values = []  # type: List[Setting]
    settings = Settings(parameter_values)
    doc = YmmslDocument('v0.1', None, settings)
    assert isinstance(doc.settings, Settings)
    assert doc.settings.parameter_values == []
