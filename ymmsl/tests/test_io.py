import ymmsl
import yatiml

import pytest


def test_invalid_version() -> None:
    """This is a regression test, the error was really confusing"""
    with pytest.raises(yatiml.RecognitionError):
        ymmsl.load('ymmsl_version: v0_1')
