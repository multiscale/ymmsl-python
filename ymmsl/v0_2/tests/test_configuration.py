from collections import OrderedDict
from pathlib import Path

from ymmsl.io import load, dump
from ymmsl.v0_2 import (
        Configuration, Checkpoints, Reference, Settings, ThreadedResReq)
from ymmsl.v0_2 import SettingValue     # noqa: F401 # pylint: disable=unused-import


Ref = Reference


def test_configuration() -> None:
    setting_values = OrderedDict()    # type: OrderedDict[str, SettingValue]
    settings = Settings(setting_values)
    config = Configuration('', settings)
    assert isinstance(config.settings, Settings)
    assert len(config.settings) == 0


def test_check_consistent(test_config6: Configuration) -> None:
    test_config6.check_consistent()


def test_configuration_update_description() -> None:
    description1 = ''
    description2 = 'single line description'
    description3 = 'multiline\ndescription'

    overlay1 = Configuration(description=description1)
    overlay2 = Configuration(description=description2)
    overlay3 = Configuration(description=description3)

    base = Configuration(description=description1)

    base.update(overlay1)
    assert base.description == ''

    base.update(overlay2)
    assert base.description == description2

    base.update(overlay3)
    assert base.description == description2 + '\n\n' + description3

    base.update(overlay1)
    assert base.description == description2 + '\n\n' + description3


def test_load_nil_settings() -> None:
    text = (
            'ymmsl_version: v0.2\n'
            'description: test loading nil-valued settings\n'
            'settings:\n'
    )

    configuration = load(text)

    assert isinstance(configuration, Configuration)
    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.resources) == 0


def test_load_no_settings() -> None:
    text = (
            'ymmsl_version: v0.2\n'
            'description: test loading with no settings\n'
            )

    configuration = load(text)

    assert isinstance(configuration, Configuration)
    assert isinstance(configuration.settings, Settings)
    assert len(configuration.settings) == 0
    assert len(configuration.resources) == 0


def test_dump_empty_settings() -> None:
    configuration = Configuration('', Settings())
    text = dump(configuration)

    assert text == (
            'ymmsl_version: v0.2\n'
            'description: \'\'\n')


def test_configuration_update_resources_add() -> None:
    resources1 = ThreadedResReq(Ref('my.macro'), 10)
    base = Configuration('', resources=[resources1])

    resources2 = ThreadedResReq(Ref('my.micro'), 2)
    overlay = Configuration('', resources=[resources2])

    base.update(overlay)

    assert len(base.resources) == 2
    assert base.resources[Ref('my.macro')] == resources1
    assert base.resources[Ref('my.micro')] == resources2


def test_load_resources() -> None:
    text = (
            'ymmsl_version: v0.2\n'
            'description: testing loading of resources\n'
            'resources:\n'
            '  macro:\n'
            '    threads: 10\n'
            '  micro:\n'
            '    threads: 1\n'
            )

    configuration = load(text)

    assert isinstance(configuration, Configuration)
    assert configuration.resources[Ref('macro')].name == 'macro'
    assert configuration.resources[Ref('macro')].threads == 10      # type: ignore
    assert configuration.resources[Ref('micro')].name == 'micro'
    assert configuration.resources[Ref('micro')].threads == 1       # type: ignore


def test_dump_resources() -> None:
    resources = [
            ThreadedResReq(Ref('macro'), 10),
            ThreadedResReq(Ref('micro'), 1)]

    configuration = Configuration('', None, resources)

    text = dump(configuration)
    assert text == (
            'ymmsl_version: v0.2\n'
            'description: \'\'\n'
            'resources:\n'
            '  macro:\n'
            '    threads: 10\n'
            '  micro:\n'
            '    threads: 1\n'
            )


def test_configuration_update_resources_override() -> None:
    resources1 = ThreadedResReq(Ref('my.macro'), 10)
    resources2 = ThreadedResReq(Ref('my.micro'), 100)
    base = Configuration('', resources=[resources1, resources2])

    resources3 = ThreadedResReq(Ref('my.micro'), 2)
    overlay = Configuration('', resources=[resources3])

    base.update(overlay)

    assert len(base.resources) == 2
    assert base.resources[Ref('my.macro')] == resources1
    assert base.resources[Ref('my.micro')] == resources3


def test_configuration_update_checkpoint(
        test_config4: Configuration) -> None:
    # Note: test_checkpoint.py tests merging of checkpoint definitions
    base = Configuration('', checkpoints=Checkpoints(
            wallclock_time=test_config4.checkpoints.wallclock_time))
    overlay = Configuration('', checkpoints=Checkpoints(
            simulation_time=test_config4.checkpoints.simulation_time))

    assert base.checkpoints.simulation_time == []
    assert overlay.checkpoints.wallclock_time == []

    base.update(overlay)
    assert (base.checkpoints.simulation_time
            == overlay.checkpoints.simulation_time)


def test_configuration_update_resume() -> None:
    base = Configuration('', resume={Ref('a'): Path('a')})
    overlay = Configuration('', resume={Ref('b'): Path('b')})

    base.update(overlay)
    assert len(base.resume) == 2
    assert base.resume[Ref('a')] == Path('a')
    assert base.resume[Ref('b')] == Path('b')


def test_configuration_update_resume_override() -> None:
    base = Configuration('', resume={Ref('a'): Path('a'), Ref('b'): Path('b')})
    overlay = Configuration('', resume={Ref('b'): Path('b_update')})

    base.update(overlay)
    assert len(base.resume) == 2
    assert base.resume[Ref('a')] == Path('a')
    assert base.resume[Ref('b')] == Path('b_update')
