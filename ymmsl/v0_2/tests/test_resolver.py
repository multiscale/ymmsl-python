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

Ref = Reference


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


def test_apply_custom_implementations_simple(env_ymmsl_path: None) -> None:
    # should import a model, and substitute a local program into it
    # then check that we have a single root model
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: Testing resolving imports with custom_implementations\n'
            'imports:\n'
            '- from a.e import implementation test_model\n'
            '- from a.b.c import implementation macro\n'
            'custom_implementations:\n'
            '  test_model.macro: macro\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    resolve(Reference('test_resolve_imports'), config)

    assert len(config.imports) == 0
    assert len(config.models) == 1
    assert Reference('test_resolve_imports.test_model') in config.models
    m = config.models[Reference('test_resolve_imports.test_model')]
    c = m.components[Reference('macro')]
    assert c.implementation == 'a.b.c.macro'


def test_apply_custom_implementations(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: Testing resolving imports with custom_implementations\n'
            'imports:\n'
            '- from a.g import implementation test_macro_micro\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    resolve(Reference('test_resolve_imports'), config)

    assert len(config.imports) == 0
    assert len(config.models) == 2
    model = config.models[Reference('a.g.test_macro_micro')]
    assert model.name == 'a.g.test_macro_micro'

    macro = model.components[Reference('macro')]
    assert macro.implementation == \
            'a.g.a_e_test_model__customised_for__a_g_test_macro_micro_macro'

    micro = model.components[Reference('micro')]
    assert micro.implementation == 'a.f.micro'

    model = config.models[
            Reference('a.g.a_e_test_model__customised_for__a_g_test_macro_micro_macro')]
    assert model.name == \
            'a.g.a_e_test_model__customised_for__a_g_test_macro_micro_macro'

    macro = model.components[Reference('macro')]
    assert macro.implementation == 'a.g.macro2'

    assert len(config.programs) == 2
    assert config.programs[Reference('a.f.micro')].args == ['/home/user/micro.py']
    assert config.programs[Reference('a.g.macro2')].args == ['/home/user/macro2.py']


def test_apply_custom_implementations_double_use(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: |\n'
            '  Testing resolving imports with custom_implementations, using a model\n'
            '  that uses the same submodel for two different components, to make sure\n'
            '  that we can change an implementation in one without affecting the\n'
            '  other\n'
            'imports:\n'
            '- from a.h import implementation test_macro_macro\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    resolve(Reference('test_resolve_imports'), config)

    assert len(config.imports) == 0
    assert len(config.models) == 3
    model = config.models[Reference('a.h.test_macro_macro')]
    assert model.name == 'a.h.test_macro_macro'

    macro1 = model.components[Reference('macro1')]
    assert macro1.implementation == 'a.e.test_model'

    macro2 = model.components[Reference('macro2')]
    assert macro2.implementation == \
            'a.h.a_e_test_model__customised_for__a_h_test_macro_macro_macro2'

    model = config.models[Reference('a.e.test_model')]
    assert model.name == 'a.e.test_model'

    macro = model.components[Reference('macro')]
    assert macro.implementation == 'a.b.c.macro'

    model = config.models[
            Reference('a.h.a_e_test_model__customised_for__a_h_test_macro_macro_macro2')
            ]
    assert model.name == \
            'a.h.a_e_test_model__customised_for__a_h_test_macro_macro_macro2'

    macro = model.components[Reference('macro')]
    assert macro.implementation == 'a.h.macro2'

    assert len(config.programs) == 2
    assert config.programs[Reference('a.b.c.macro')].executable == Path('my_program')
    assert config.programs[Reference('a.h.macro2')].args == ['/home/user/macro2.py']


def test_apply_custom_implementations_set_none(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: Testing resolving imports with custom_implementations\n'
            'models:\n'
            '  macro_micro:\n'
            '    components:\n'
            '      macro:\n'
            '        ports:\n'
            '          o_i: out\n'
            '          s: in\n'
            '        description: Macro model\n'
            '        implementation: macro\n'
            '      micro:\n'
            '        ports:\n'
            '          f_init: in\n'
            '          o_f: out\n'
            '        description: Micro model\n'
            '        implementation: micro\n'
            'custom_implementations:\n'
            '  macro_micro.micro:\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    resolve(Reference('test_resolve_imports'), config)

    model = config.models[Reference('test_resolve_imports.macro_micro')]
    assert model.components[Reference('micro')].implementation is None


def test_apply_custom_implementations_no_hidden_copies() -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: |\n'
            '  Testing that all local references point to the same object\n'
            'models:\n'
            '  A:\n'
            '    description: Model A\n'
            '    components:\n'
            '      c1:\n'
            '        ports: {}\n'
            '        description: Component c1\n'
            '  B:\n'
            '    description: Model B\n'
            '    components:\n'
            '      c2:\n'
            '        ports: {}\n'
            '        description: Component c2\n'
            '      c3:\n'
            '        ports: {}\n'
            '        description: Component c3\n'
            'programs:\n'
            '  p:\n'
            '    ports:\n'
            '    description: A program\n'
            '    executable: /home/user/p\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    config.models[Ref('A')].components[Ref('c1')].implementation = Ref('p')
    config.custom_implementations[Reference('B.c2')] = Reference('A')
    config.custom_implementations[Reference('B.c3')] = Reference('A')

    resolve(Reference('no_copies'), config)


    # Same thing but using custom implementations for everything
    config = load(ymmsl)
    assert isinstance(config, Configuration)

    config.custom_implementations[Reference('A.c1')] = Reference('p')
    config.custom_implementations[Reference('B.c2')] = Reference('A')
    config.custom_implementations[Reference('B.c3')] = Reference('A')

    resolve(Reference('no_copies'), config)

    b = config.models[Reference('no_copies.B')]
    assert b.components[Reference('c2')].implementation == 'no_copies.A'
    assert b.components[Reference('c3')].implementation == 'no_copies.A'

    a = config.models[Reference('no_copies.A')]
    assert a.components[Reference('c1')].implementation == 'no_copies.p'

    # this should yield the same result as above, because all references to A point to
    # the same object
    config = load(ymmsl)
    assert isinstance(config, Configuration)

    config.custom_implementations[Reference('B.c2')] = Reference('A')
    config.custom_implementations[Reference('B.c3')] = Reference('A')
    config.custom_implementations[Reference('A.c1')] = Reference('p')

    resolve(Reference('no_copies2'), config)

    b = config.models[Reference('no_copies2.B')]
    assert b.components[Reference('c2')].implementation == 'no_copies2.A'
    assert b.components[Reference('c3')].implementation == 'no_copies2.A'

    a = config.models[Reference('no_copies2.A')]
    assert a.components[Reference('c1')].implementation == 'no_copies2.p'


def test_apply_custom_implementations_everything_localised() -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: |\n'
            '  Testing that local and imported models are treated the same when\n'
            '  customised.\n'
            'imports:\n'
            '- from a.e import implementation test_model\n'
            'models:\n'
            '  A:\n'
            '    description: Model A\n'
            '    components:\n'
            '      c1:\n'
            '        ports: {}\n'
            '        description: Component c1\n'
            '  B:\n'
            '    description: Model B\n'
            '    components:\n'
            '      macro:\n'
            '        ports: {}\n'
            '        description: Component c2\n'
            'programs:\n'
            '  p:\n'
            '    ports:\n'
            '    description: A program\n'
            '    executable: /home/user/p\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    config.custom_implementations[Ref('A.c1')] = Ref('test_model')
    config.custom_implementations[Ref('test_model.macro')] = Ref('p')

    resolve(Reference('el'), config)

    c1 = config.models[Ref('el.A')].components[Ref('c1')]
    assert c1.implementation == 'el.test_model'

    test_model = config.models[Ref('el.test_model')]
    assert test_model.components[Ref('macro')].implementation == 'el.p'

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    config.custom_implementations[Ref('A.c1')] = Ref('B')
    config.custom_implementations[Ref('B.macro')] = Ref('p')

    resolve(Reference('el'), config)

    c1 = config.models[Ref('el.A')].components[Ref('c1')]
    assert c1.implementation == 'el.B'

    b = config.models[Ref('el.B')]
    assert b.components[Ref('macro')].implementation == 'el.p'


def test_apply_custom_implementations_cut_branch(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: |\n'
            '  Testing that lopped-off branches are cleaned up properly.\n'
            'imports:\n'
            '- from a.g import implementation test_macro_micro\n'
            'models:\n'
            '  test_deeply_nested:\n'
            '    description: Models within models within models...\n'
            '    components:\n'
            '      c1:\n'
            '        ports:\n'
            '          o_i: out\n'
            '          s: in\n'
            '        description: Macro model\n'
            '        implementation: test_macro_micro\n'
            'programs:\n'
            '  program3:\n'
            '    ports:\n'
            '      o_i: out\n'
            '      s: in\n'
            '    description: Alternative implementation\n'
            '    executable: python3\n'
            '    args: /home/user/program3.py\n'
            'custom_implementations:\n'
            '  test_deeply_nested.c1: program3\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)

    resolve(Reference('nested'), config)
    assert len(config.models) == 1


def test_apply_custom_implementations_errors(env_ymmsl_path: None) -> None:
    ymmsl = (
            'ymmsl_version: v0.2\n'
            'description: |\n'
            '  Testing resolving imports with custom_implementations, using a model\n'
            '  that uses the same submodel for two different components, to make sure\n'
            '  that we can change an implementation in one without affecting the\n'
            '  other\n'
            'imports:\n'
            '- from a.h import implementation test_macro_macro\n'
            'programs:\n'
            '  macro3:\n'
            '    ports:\n'
            '      o_i: out\n'
            '      s: in\n'
            '    description: Alternative macro model implementation\n'
            '    executable: python3\n'
            '    args: /home/user/macro3.py\n'
            )

    config = load(ymmsl)
    assert isinstance(config, Configuration)
    resolve(Reference('test_resolve_imports'), config)

    config = load(ymmsl)
    assert isinstance(config, Configuration)
    config.custom_implementations[Reference('test_macro_mAcro.macro')] = \
            Reference('macro3')
    with pytest.raises(RuntimeError):
        resolve(Reference('test_resolve_imports'), config)

    config = load(ymmsl)
    assert isinstance(config, Configuration)
    config.custom_implementations[Reference('test_macro_macro.macro')] = \
            Reference('Macro3')
    with pytest.raises(RuntimeError):
        resolve(Reference('test_resolve_imports'), config)


    config = load(ymmsl)
    assert isinstance(config, Configuration)
    config.custom_implementations[Reference('test_macro_macro.macro1[0]')] = \
            Reference('macro3')
    with pytest.raises(RuntimeError):
        resolve(Reference('test_resolve_imports'), config)

    config = load(ymmsl)
    assert isinstance(config, Configuration)
    config.custom_implementations[Reference('test_macro_macro.macro3')] = \
            Reference('macro3')
    with pytest.raises(RuntimeError):
        resolve(Reference('test_resolve_imports'), config)

    config = load(ymmsl)
    assert isinstance(config, Configuration)
    config.custom_implementations[Reference('test_macro_macro.macro1.mAcro')] = \
            Reference('macro3')
    with pytest.raises(RuntimeError):
        resolve(Reference('test_resolve_imports'), config)

    config = load(ymmsl)
    assert isinstance(config, Configuration)
    config.custom_implementations[Reference('test_macro_macro.macro1.macro')] = \
            Reference('test_macro_macro')
    config.custom_implementations[Reference('test_macro_macro.macro1.macro.mAcro')] = \
            Reference('macro3')
    with pytest.raises(RuntimeError):
        resolve(Reference('test_resolve_imports'), config)


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
    # N.B. these entry points don't have a dist attribute set
    test_entrypoints = [
        # We should ignore any entrypoints not in the ymmsl.module group
        EntryPoint("test.ymmsl1", "does.not.exist:NONE", "something"),
        # Valid entry point
        EntryPoint("test.ymmsl1", f"{testmod}:TEST_YMMSL_1", "ymmsl.module"),
        # This one doesn't exist:
        EntryPoint("test.ymmsl2", f"{testmod}:TEST_YMMSL_2", "ymmsl.module"),
        # Two entrypoints with the same name
        EntryPoint("test.xyz", f"{testmod}:TEST_YMMSL_1", "ymmsl.module"),
        EntryPoint("test.xyz", f"{testmod}:TEST_YMMSL_2", "ymmsl.module"),
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
