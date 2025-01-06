from pathlib import Path

import pytest
from ymmsl import (
        BaseEnv, ExecutionModel, Implementation, KeepsStateForNextUse, Reference)


def test_implementation() -> None:
    impl = Implementation(Reference('test_impl'), script='run_test_impl')
    assert impl.name == 'test_impl'
    assert impl.script == 'run_test_impl'


def test_implementation_script_list() -> None:
    impl = Implementation(
            name=Reference('test_impl'),
            script=[
                '#!/bin/bash',
                '',
                'test_impl'])

    assert impl.name == 'test_impl'
    assert impl.script == '#!/bin/bash\n\ntest_impl\n'


def test_implementations_executable() -> None:
    impl = Implementation(
            name=Reference('test_impl'),
            base_env=BaseEnv.MANAGER,
            modules=['python/3.6.0', 'gcc/9.3.0'],
            virtual_env=Path('/home/user/envs/venv'),
            env={
                'VAR1': '1',
                'VAR2': 'Testing'},
            executable=Path('/home/user/software/my_submodel/bin/model'),
            args='-v -a',
            execution_model=ExecutionModel.OPENMPI,
            can_share_resources=False)

    assert impl.name == 'test_impl'
    assert impl.base_env == BaseEnv.MANAGER
    assert impl.modules == ['python/3.6.0', 'gcc/9.3.0']
    assert impl.virtual_env == Path('/home/user/envs/venv')
    assert impl.env is not None
    assert impl.env['VAR1'] == '1'
    assert impl.env['VAR2'] == 'Testing'
    assert impl.executable == Path('/home/user/software/my_submodel/bin/model')
    assert impl.args == ['-v -a']
    assert impl.execution_model == ExecutionModel.OPENMPI
    assert impl.can_share_resources is False


def test_implementations_exclusive() -> None:
    with pytest.raises(RuntimeError):
        Implementation(name=Reference('test'), script='', executable=Path())


def test_implementations_script() -> None:
    script = (
            '#!/bin/bash\n'
            '\n'
            'mpirun my_model\n')

    impl = Implementation(
            name=Reference('test_impl'),
            execution_model=ExecutionModel.OPENMPI,
            can_share_resources=False,
            keeps_state_for_next_use=KeepsStateForNextUse.HELPFUL,
            script=script)

    assert impl.name == 'test_impl'
    assert impl.execution_model == ExecutionModel.OPENMPI
    assert impl.can_share_resources is False
    assert impl.keeps_state_for_next_use == KeepsStateForNextUse.HELPFUL
    assert impl.script == script


def test_implementations_script_invalid_args() -> None:
    with pytest.raises(RuntimeError):
        Implementation(
                name=Reference('test_impl'),
                execution_model=ExecutionModel.DIRECT,
                env={'TEST': 'NOT_ALLOWED'},
                script='test')
