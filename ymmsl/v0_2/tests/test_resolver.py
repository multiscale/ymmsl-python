import logging
import sys
from collections.abc import Generator
import os
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from ymmsl.io import load
from ymmsl.v0_2.configuration import Configuration
from ymmsl.v0_2.identity import Reference
from ymmsl.v0_2.resolver import resolve

if sys.version_info < (3, 10):
    from importlib_metadata import EntryPoints, EntryPoint
else:
    from importlib.metadata import EntryPoints, EntryPoint


@pytest.fixture
def env_ymmsl_path() -> Generator[None, None, None]:
    cur_dir = Path(__file__).parents[0]
    ymmsl1 = cur_dir / 'ymmsl1'
    ymmsl2 = cur_dir / 'ymmsl2'
    ymmsl3 = cur_dir / 'ymmsl3'     # intentionally does not exist

    os.environ['YMMSL_PATH'] = f'{ymmsl3}:{ymmsl2}:{ymmsl1}'

    yield

    del os.environ['YMMSL_PATH']


def test_resolve_imports(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: Testing resolving imports\n'
            'imports:\n'
            '- from a.d import implementation test_importing\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)
    assert config.models == {}

    resolve(Reference('test_resolve_imports'), config)

    assert len(config.imports) == 0
    assert len(config.models) == 1
    assert config.models[Reference('a.d.test_importing')].name == 'a.d.test_importing'
    assert len(config.programs) == 2
    assert config.programs[Reference('a.d.micro')].executable == Path('python3')
    assert config.programs[Reference('a.b.c.macro')].executable == Path('my_program')


def test_resolve_imports_module_not_found(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: Testing missing modules\n'
            'imports:\n'
            '- from a.doesnotexist import implementation test_error\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    with pytest.raises(RuntimeError) as e:
        resolve(Reference('test_module_not_found'), config)

    assert 'Failed to find a file' in str(e.value)
    assert len(config.imports) == 1


def test_resolve_imports_broken_module(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: Testing missing modules\n'
            'imports:\n'
            '- from a.broken import implementation test_error\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    with pytest.raises(RuntimeError) as e:
        resolve(Reference('test_broken_module'), config)

    assert 'model' in str(e.value) and 'models' in str(e.value)
    assert len(config.imports) == 1


def test_resolve_imports_implementation_not_found(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: Testing missing modules\n'
            'imports:\n'
            '- from a.d import implementation mucro\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    with pytest.raises(RuntimeError) as e:
        resolve(Reference('test_implementation_not_found'), config)

    assert 'Implementation mucro not found' in str(e.value)
    assert len(config.imports) == 1


def test_resolve_imports_no_shadowing(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: Testing resolving imports\n'
            'imports:\n'
            '- from a.d import implementation test_importing\n'
            'programs:\n'
            '  test_importing:\n'
            '    executable: python3\n'
            '    args: /home/user/test_importing.py\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    with pytest.raises(RuntimeError) as e:
        resolve(Reference('test_no_shadowing'), config)

    assert 'both defined and imported' in str(e.value)
    assert len(config.imports) == 1


TEST_YMMSL_1 = """
ymmsl_version: v0.2
description: Testing resolving imports
programs:
  test_importing:
    executable: python3
    args: test_program.py
"""


@pytest.fixture()
def mock_entry_points() -> Generator[Mock]:
    testmod = "ymmsl.v0_2.tests.test_resolver"
    # N.B. these entry points don't havea dist attribute set
    test_entrypoints = [
        EntryPoint("test.ymmsl1", f"{testmod}:TEST_YMMSL_1", "ymmsl.path"),
        # This one doesn't exist:
        EntryPoint("test.ymmsl2", f"{testmod}:TEST_YMMSL_2", "ymmsl.path"),
        # Two entrypoints with the same name
        EntryPoint("test.xyz", f"{testmod}:TEST_YMMSL_1", "ymmsl.path"),
        EntryPoint("test.xyz", f"{testmod}:TEST_YMMSL_2", "ymmsl.path"),
    ]
    with patch("ymmsl.v0_2.resolver.entry_points") as mock_entry_points:
        mock_entry_points.side_effect = EntryPoints(test_entrypoints).select
        yield mock_entry_points


def test_resolve_entrypoints(mock_entry_points: Mock) -> None:
    config = load("""
        ymmsl_version: v0.2
        description: Test
        imports:
        - from test.ymmsl1 import implementation test_importing
    """)
    assert isinstance(config, Configuration)
    resolve(Reference("test_importing"), config)

    test_importing = Reference("test.ymmsl1.test_importing")
    assert test_importing in config.programs
    assert config.programs[test_importing].executable == Path("python3")
    assert config.programs[test_importing].args == ["test_program.py"]


def test_resolve_entrypoints_duplicate_name(
        mock_entry_points: Mock, caplog: pytest.LogCaptureFixture) -> None:
    config = load("""
        ymmsl_version: v0.2
        description: Test
        imports:
        - from test.xyz import implementation test_importing
    """)
    assert isinstance(config, Configuration)
    with caplog.at_level(logging.WARNING):
        resolve(Reference("test_importing"), config)
    assert len(caplog.record_tuples) == 1  # Expect one warning log message
    module, level, text = caplog.record_tuples[0]
    assert module == "ymmsl.v0_2.resolver"
    assert level == logging.WARNING
    assert "Multiple entry points" in text
    assert "ymmsl.v0_2.tests.test_resolver:TEST_YMMSL_1" in text
    assert "ymmsl.v0_2.tests.test_resolver:TEST_YMMSL_2" in text

    test_importing = Reference("test.xyz.test_importing")
    assert test_importing in config.programs
    assert config.programs[test_importing].executable == Path("python3")
    assert config.programs[test_importing].args == ["test_program.py"]


def test_resolve_entrypoints_loading_error(mock_entry_points: Mock) -> None:
    config = load("""
        ymmsl_version: v0.2
        description: Test
        imports:
        - from test.ymmsl2 import implementation test_importing
    """)
    assert isinstance(config, Configuration)
    with pytest.raises(RuntimeError, match="Error while loading the entrypoint"):
        resolve(Reference("test_importing"), config)
