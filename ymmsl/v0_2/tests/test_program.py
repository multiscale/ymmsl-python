from pathlib import Path

import pytest
import yatiml

from ymmsl.v0_2.ports import Operator, Ports
from ymmsl.v0_2.execution import BaseEnv, ExecutionModel, KeepsStateForNextUse
from ymmsl.v0_2.identity import Reference
from ymmsl.v0_2.implementation import Implementation
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
    assert len(prog.ports) == 2
    assert prog.ports['init'].operator == Operator.F_INIT
    assert prog.ports['bc_in'].operator == Operator.S
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
    assert len(prog.ports) == 2
    assert prog.ports['out'].operator == Operator.O_I
    assert prog.ports['in'].operator == Operator.S
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


def test_load_program(test_program_text: str) -> None:
    load = yatiml.load_function(
            Program, BaseEnv, ExecutionModel, Implementation, KeepsStateForNextUse,
            Ports, Reference, SettingType, SupportedSettings)

    prog = load(test_program_text)

    assert prog.name == 'macro'
    assert prog.ports.sending_port_names() == ['final', 'out1', 'out2']
    assert prog.ports.receiving_port_names() == ['init', 'in1', 'in2']
    assert prog.base_env == BaseEnv.LOGIN
    assert prog.modules is not None
    assert len(prog.modules) == 2
    assert prog.modules[0] == 'gcc/13.3.0'
    assert prog.modules[1] == 'FFTW/3.2.1'
    assert prog.virtual_env == Path('/home/user/.venv')
    assert len(prog.env) == 2
    assert prog.env['SETTING'] == 'something'
    assert prog.env['VARIABLE'] == '42'
    assert prog.execution_model == ExecutionModel.INTELMPI
    assert prog.executable == Path('python3')
    assert prog.args == ['/home/user/script.py']
    assert prog.can_share_resources is False
    assert prog.keeps_state_for_next_use == KeepsStateForNextUse.HELPFUL


def test_dump_programs(test_program: Program, test_program_text: str) -> None:
    dump = yatiml.dumps_function(
            Program, BaseEnv, ExecutionModel, Implementation, KeepsStateForNextUse,
            Ports, Reference, SettingType, SupportedSettings)

    text = dump(test_program)
    assert text == test_program_text
