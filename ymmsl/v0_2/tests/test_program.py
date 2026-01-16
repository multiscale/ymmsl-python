from pathlib import Path

import pytest

from ymmsl.v0_2.ports import Ports
from ymmsl.v0_2.execution import BaseEnv, ExecutionModel, KeepsStateForNextUse
from ymmsl.v0_2.identity import Reference
from ymmsl.v0_2.program import Program
from ymmsl.v0_2.supported_settings import SettingType, SupportedSettings


def test_program_script_list() -> None:
    prog = Program(
            name='test_prog',
            ports=Ports(f_init='init', s='bc_in'),
            script=[
                '#!/bin/bash',
                '',
                'test_prog'])

    assert isinstance(prog.name, Reference)
    assert prog.name == 'test_prog'
    assert prog.ports.f_init == ['init']
    assert prog.ports.s == ['bc_in']
    assert prog.script == '#!/bin/bash\n\ntest_prog\n'


def test_program_executable() -> None:
    prog = Program(
            name='test_prog',
            ports=Ports(o_i=['out'], s=['in']),
            description='Description of the program',
            supported_settings=SupportedSettings({'a': '[int]', 'b': 'str'}),
            base_env=BaseEnv.MANAGER,
            modules=['python/3.10.0', 'gcc/13.3.0'],
            virtual_env=Path('/home/user/envs/venv'),
            env={
                'VAR1': '1',
                'VAR2': 'Testing'},
            executable=Path('/home/user/software/my_submodel/bin/model'),
            args='-v -a',
            execution_model=ExecutionModel.OPENMPI,
            can_share_resources=False)

    assert prog.name == 'test_prog'
    assert prog.ports.f_init == []
    assert prog.ports.o_i == ['out']
    assert prog.ports.s == ['in']
    assert prog.ports.o_f == []
    assert prog.description == 'Description of the program'
    assert prog.supported_settings is not None
    assert prog.supported_settings['a'] == SettingType.LIST_INT
    assert prog.supported_settings['b'] == SettingType.STR
    assert prog.base_env == BaseEnv.MANAGER
    assert prog.modules == ['python/3.10.0', 'gcc/13.3.0']
    assert prog.virtual_env == Path('/home/user/envs/venv')
    assert prog.env is not None
    assert prog.env['VAR1'] == '1'
    assert prog.env['VAR2'] == 'Testing'
    assert prog.executable == Path('/home/user/software/my_submodel/bin/model')
    assert prog.args == ['-v -a']
    assert prog.execution_model == ExecutionModel.OPENMPI
    assert prog.can_share_resources is False


def test_program_exclusive() -> None:
    with pytest.raises(RuntimeError):
        Program(name='test', script='', executable=Path())


def test_program_script() -> None:
    script = (
            '#!/bin/bash\n'
            '\n'
            'mpirun my_model\n')

    prog = Program(
            name='test_prog',
            execution_model=ExecutionModel.OPENMPI,
            can_share_resources=False,
            keeps_state_for_next_use=KeepsStateForNextUse.HELPFUL,
            script=script)

    assert prog.name == 'test_prog'
    assert prog.execution_model == ExecutionModel.OPENMPI
    assert prog.can_share_resources is False
    assert prog.keeps_state_for_next_use == KeepsStateForNextUse.HELPFUL
    assert prog.script == script


def test_program_script_invalid_args() -> None:
    with pytest.raises(RuntimeError):
        Program(
                name='test_prog',
                execution_model=ExecutionModel.DIRECT,
                env={'TEST': 'NOT_ALLOWED'},
                script='test')
