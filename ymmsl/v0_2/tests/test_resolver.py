from collections.abc import Generator
import os
from pathlib import Path

import pytest

from ymmsl.io import load
from ymmsl.v0_2.configuration import Configuration
from ymmsl.v0_2.identity import Reference
from ymmsl.v0_2.resolver import resolve


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
