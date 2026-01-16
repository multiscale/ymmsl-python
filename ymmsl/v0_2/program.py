"""Definitions for how to start programs."""
from pathlib import Path
from typing import cast, Dict, List, Optional, Union

import yaml
import yatiml

from ymmsl.v0_2.execution import BaseEnv, ExecutionModel, KeepsStateForNextUse
from ymmsl.v0_2.implementation import Implementation
from ymmsl.v0_2.ports import Ports
from ymmsl.v0_2.supported_settings import SupportedSettings


class Program(Implementation):
    """Describes an installed program.

    A Program normally has an ``executable`` and any other needed attributes, with
    ``script`` set to None. You should specify a script only as a last resort, probably
    after getting some help from the authors of this library. If a script is specified,
    all other attributes except for the name, the execution model, can_share_resources
    and keeps_state_for_next_use must be ``None``.

    If base_env is not specified then it defaults to MANAGER.

    For ``execution_model``, the following values are supported:

    direct
      The program will be executed directly. Use this for non-MPI programs.

    openmpi
      For MPI programs that should be started using OpenMPI's mpirun.

    intelmpi
      For MPI programs that should be started using Intel MPI's mpirun.

    The ``can_share_resources`` attribute describes whether this program can share
    resources (cores) with other components in a macro-micro coupling. Set this to
    ``False`` if the program does significant computing inside of its time update
    loop after having sent messages on its O_I port(s) but before receiving messages on
    its S port(s). In the unlikely case that it's doing significant computing before
    receiving for F_INIT or after sending its O_F messages, likewise set this to
    ``False``.

    Setting this to ``False`` unnecessarily will waste core hours, setting it to
    ``True`` incorrectly will slow down your simulation.

    Attributes:
        name: Name of the program
        ports: Ports this program supports, if fixed
        description: Human-readable description of this program
        supported_settings: Settings supported by this program
        base_env: Base environment to start from
        modules: HPC software modules to load
        virtual_env: Path to a virtual env to activate
        env: Environment variables to set
        execution_model: How to start the executable
        executable: Full path to executable to run
        args: Arguments to pass to the executable
        script: A script that starts the program
        can_share_resources: Whether this program can share resources (cores) with other
            components or not
        keeps_state_for_next_use: Does this program keep state for the next
            iteration of the reuse loop. See :class:`KeepsStateForNextUse`.
    """
    def __init__(
            self,
            name: str,
            ports: Optional[Ports] = None,
            description: str = '',
            supported_settings: Optional[SupportedSettings] = None,
            base_env: Optional[BaseEnv] = None,
            modules: Union[str, List[str], None] = None,
            virtual_env: Optional[Path] = None,
            env: Optional[Dict[str, str]] = None,
            execution_model: ExecutionModel = ExecutionModel.DIRECT,
            executable: Optional[Path] = None,
            args: Union[str, List[str], None] = None,
            script: Union[str, List[str], None] = None,
            can_share_resources: bool = True,
            keeps_state_for_next_use: KeepsStateForNextUse
            = KeepsStateForNextUse.NECESSARY
            ) -> None:
        """Create a Program description.

        A Program normally has an ``executable`` and any other needed arguments, with
        ``script`` set to ``None``. You should specify a script only as a last resort,
        probably after getting some help from the authors of this library. If ``script``
        is specified, all other arguments except for ``name``, ``execution model``,
        ``can_share_resources`` and ``keeps_state_for_next_use`` must be ``None``.

        If script is a list, each string in it is a line, and the lines will be
        concatenated into a single string to put into the script attribute.

        Args:
            name: Name of the program, must be a valid reference
            ports: Ports this program has
            description: Human-readable description of this program
            supported_settings: Settings supported by this program
            base_env: Base environment to start from, defaults to clean
            modules: HPC software modules to load
            virtual_env: Path to a virtual env to activate
            env: Environment variables to set
            execution_model: How to start the executable, see above.
            executable: Full path to executable to run
            args: Arguments to pass to the executable
            script: Script that starts the program
            can_share_resources: Whether this program can share resources (cores) with
                other components or not. See above.
            keeps_state_for_next_use: Does this program keep state for the next
                iteration of the reuse loop. See :class:`KeepsStateForNextUse`.
        """
        super().__init__(name, ports, description, supported_settings)

        if script is not None:
            err_arg = []
            if base_env is not None:
                err_arg.append('"base_env"')
            if modules is not None:
                err_arg.append('"modules"')
            if virtual_env is not None:
                err_arg.append('"virtual_env"')
            if env is not None:
                err_arg.append('"env"')
            if executable is not None:
                err_arg.append('"executable"')
            if args is not None:
                err_arg.append('"args"')
            if err_arg:
                raise RuntimeError(
                        'When creating a Program, script was specified together with'
                        f' arguments {", ".join(err_arg)}, which is not supported, as'
                        ' they are supposed to be inside the script if there is one.'
                        ' Please use either a script or the arguments listed above.')

        if executable is None and script is None:
            raise RuntimeError(
                    f'In {name}, neither a script nor an executable was given. Please'
                    ' specify either a script, or the other parameters.')

        self.base_env = base_env if base_env else BaseEnv.MANAGER

        if isinstance(modules, str):
            self.modules: Optional[List[str]] = modules.split(' ')
        else:
            self.modules = modules

        self.virtual_env = virtual_env

        if env is None:
            env = dict()
        self.env = env

        self.execution_model = execution_model
        self.executable = executable

        if isinstance(args, str):
            self.args: Optional[List[str]] = [args]
        else:
            self.args = args

        if isinstance(script, list):
            self.script: Optional[str] = '\n'.join(script) + '\n'
        else:
            self.script = script

        self.can_share_resources = can_share_resources
        self.keeps_state_for_next_use = keeps_state_for_next_use

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # There's no ambiguity, and we want to allow some leeway
        # and savorize things, so only require that the node is a mapping.
        node.require_mapping()

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.has_attribute('env'):
            env_node = node.get_attribute('env')
            if env_node.is_mapping():
                for _, value_node in env_node.yaml_node.value:
                    if isinstance(value_node, yaml.ScalarNode):
                        if value_node.tag == 'tag:yaml.org,2002:int':
                            value_node.tag = 'tag:yaml.org,2002:str'
                        if value_node.tag == 'tag:yaml.org,2002:float':
                            value_node.tag = 'tag:yaml.org,2002:str'
                        if value_node.tag == 'tag:yaml.org,2002:bool':
                            value_node.tag = 'tag:yaml.org,2002:str'

    _yatiml_defaults = {
        'base_env': 'manager',
        'execution_model': 'direct',
        'keeps_state_for_next_use': 'necessary'}

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.has_attribute('script'):
            script_node = node.get_attribute('script')
            if script_node.is_scalar(str):
                text = cast(str, script_node.get_value())
                if '\n' in text:
                    cast(yaml.ScalarNode, script_node.yaml_node).style = '|'

        node.remove_attributes_with_default_values(cls)
        if node.has_attribute('env'):
            env_attr = node.get_attribute('env')
            if env_attr.is_mapping():
                if env_attr.is_empty():
                    node.remove_attribute('env')
