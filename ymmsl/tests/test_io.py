import pytest
import yatiml

import ymmsl
from ymmsl import v0_2


def test_invalid_version() -> None:
    """This is a regression test, the error was really confusing"""
    with pytest.raises(yatiml.RecognitionError):
        ymmsl.load("ymmsl_version: v0_1")


def test_component_description_trailing_whitespace() -> None:
    """Regression test

    PyYAML refuses to use block mode if there is trailing whitespace.
    """
    c = v0_2.Component("c1", v0_2.Ports(), "Test  \nmore test!")
    dump = yatiml.dumps_function(v0_2.Component, v0_2.Ports, v0_2.Reference)
    text = dump(c)
    assert text == ("name: c1\nports: {}\ndescription: |\n  Test\n  more test!\n")


def test_configuration_description_trailing_whitespace() -> None:
    """Regression test, see above"""
    c = v0_2.Configuration("Test\nmore test!   ")
    dump = yatiml.dumps_function(v0_2.Configuration, v0_2.Settings, v0_2.Checkpoints)
    text = dump(c)
    assert text == ("description: |\n  Test\n  more test!\n")


def test_model_description_trailing_whitespace() -> None:
    """Regression test, see above"""
    m = v0_2.Model("test_model", v0_2.Ports(), "Test\nmore test   \nand more")
    dump = yatiml.dumps_function(
        v0_2.Model, v0_2.Implementation, v0_2.Ports, v0_2.Reference
    )
    text = dump(m)
    assert text == (
        "name: test_model\n"
        "description: |\n"
        "  Test\n"
        "  more test\n"
        "  and more\n"
        "components: {}\n"
    )


def test_program_description_trailing_whitespace() -> None:
    """Regression test, see above"""
    p = v0_2.Program("test_program", v0_2.Ports(), "Test   ", script="")
    dump = yatiml.dumps_function(
        v0_2.Program,
        v0_2.BaseEnv,
        v0_2.ExecutionModel,
        v0_2.Implementation,
        v0_2.KeepsStateForNextUse,
        v0_2.Ports,
        v0_2.Reference,
    )
    text = dump(p)
    assert text == ("name: test_program\ndescription: |\n  Test\nscript: ''\n")


def test_supported_settings_trailing_whitespace() -> None:
    """Regression test, see above"""
    s = v0_2.SupportedSettings(
        {
            "alpha": "float Collision angle   ",
            "beta": "float Dampening coefficient",
            "gamma": "int Number\n  of\nrays  ",
        }
    )
    dump = yatiml.dumps_function(
        v0_2.SupportedSettings, v0_2.Identifier, v0_2.SettingType, v0_2.SupportedSetting
    )
    text = dump(s)
    assert text == (
        "alpha: float Collision angle\n"
        "beta: float Dampening coefficient\n"
        "gamma:\n"
        "  type: int\n"
        "  description: |\n"
        "    Number\n"
        "      of\n"
        "    rays\n"
    )
