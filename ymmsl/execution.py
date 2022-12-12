"""Definitions for specifying how to start a component."""
from enum import Enum
from pathlib import Path
from typing import cast, Dict, List, Optional, Union

from ruamel import yaml
import yatiml

from ymmsl.identity import Reference


class ImplementationState(Enum):
    """Describes whether an implementation has internal state.

    See also :ref:`Implementation state`.
    """

    STATEFUL = 1
    """The implementation has an internal state that is required for continuing
    the implementation."""
    STATELESS = 2
    """The implementation has no internal state."""
    WEAKLY_STATEFUL = 3
    """The implementation has an internal state, which can be regenerated.
    However, doing so may be expensive."""

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.is_scalar(str):
            val = cast(str, node.get_value())
            node.set_value(val.upper())

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        val = node.get_value()
        if isinstance(val, str):
            node.set_value(val.lower())


class ExecutionModel(Enum):
    """Describes how to start a model component."""
    DIRECT = 1
    """Start directly on the allocated core(s), without MPI."""
    OPENMPI = 2
    """Start using OpenMPI's mpirun."""
    INTELMPI = 3
    """Start using Intel MPI's mpirun."""
    SRUNMPI = 4
    """Start MPI implementation using srun."""

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.is_scalar(str):
            val = cast(str, node.get_value())
            node.set_value(val.upper())

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        val = node.get_value()
        if isinstance(val, str):
            node.set_value(val.lower())


class Implementation:
    """Describes an installed implementation.

    An Implementation normally has an ``executable`` and any other
    needed attributes, with ``script`` set to None. You should specify
    a script only as a last resort, probably after getting some help
    from the authors of this library. If a script is specified, all
    other attributes except for the name must be ``None``.

    For ``execution_model``, the following values are supported:

    direct
      The program will be executed directly. Use this for non-MPI
      programs.

    openmpi
      For MPI programs that should be started using OpenMPI's mpirun.

    intelmpi
      For MPI programs that should be started using Intel MPI's
      mpirun.

    The ``can_share_resources`` attribute describes whether this
    implementation can share resources (cores) with other components
    in a macro-micro coupling. Set this to ``False`` if the
    implementation does significant computing inside of its time
    update loop after having sent messages on its O_I port(s) but
    before receiving messages on its S port(s). In the unlikely case
    that it's doing significant computing before receiving for F_INIT
    or after sending its O_F messages, likewise set this to ``False``.

    Setting this to ``False`` unnecessarily will waste core hours,
    setting it to ``True`` incorrectly will slow down your simulation.

    Attributes:
        name: Name of the implementation
        modules: HPC software modules to load
        virtual_env: Path to a virtual env to activate
        env: Environment variables to set
        execution_model: How to start the executable
        executable: Full path to executable to run
        args: Arguments to pass to the executable
        script: A script that starts the implementation
        can_share_resources: Whether this implementation can share
            resources (cores) with other components or not
        stateful: Is this implementation stateful, see
            :class:`ImplementationState`
        supports_checkpoint: Does this implementation support the checkpointing
            API
    """

    def __init__(
            self,
            name: Reference,
            modules: Union[str, List[str], None] = None,
            virtual_env: Optional[Path] = None,
            env: Optional[Dict[str, str]] = None,
            execution_model: ExecutionModel = ExecutionModel.DIRECT,
            executable: Optional[Path] = None,
            args: Union[str, List[str], None] = None,
            script: Union[str, List[str], None] = None,
            can_share_resources: bool = True,
            stateful: ImplementationState = ImplementationState.STATEFUL,
            ) -> None:
        """Create an Implementation description.

        An Implementation normally has an ``executable`` and any other
        needed arguments, with ``script`` set to ``None``. You should
        specify a script only as a last resort, probably after getting
        some help from the authors of this library. If ``script`` is
        specified, all other arguments except for ``name`` must be
        ``None``.

        If script is a list, each string in it is a line, and the
        lines will be concatenated into a single string to put into
        the script attribute.

        Args:
            name: Name of the implementation
            modules: HPC software modules to load
            virtual_env: Path to a virtual env to activate
            env: Environment variables to set
            execution_model: How to start the executable, see above.
            executable: Full path to executable to run
            args: Arguments to pass to the executable
            script: Script that starts the implementation
            can_share_resources: Whether this implementation can share
                    resources (cores) with other components or not.
                    See above.
            stateful: Is this implementation stateful, see
                :class:`ImplementationState`
            supports_checkpoint: Does this implementation support the
                checkpointing API
        """
        if script is not None:
            if (
                    modules is not None or virtual_env is not None or
                    env is not None or
                    execution_model is not ExecutionModel.DIRECT or
                    executable is not None or args is not None):
                raise RuntimeError(
                        'When creating an Implementation, script was specified'
                        ' together with another argument, which is not'
                        ' supported. Please specify either a script or an'
                        ' executable.')

        if executable is not None and script is not None:
            raise RuntimeError(
                    f'In {name}, both a script and an executable were given.'
                    ' Please specify either a script, or the other parameters.'
                    )

        if executable is None and script is None:
            raise RuntimeError(
                    f'In {name}, neither a script nor an executable was given.'
                    ' Please specify either a script, or the other parameters.'
                    )

        self.name = name

        if isinstance(script, list):
            self.script = '\n'.join(script) + '\n'  # type: Optional[str]
        else:
            self.script = script

        if isinstance(modules, str):
            self.modules = modules.split(' ')   # type: Optional[List[str]]
        else:
            self.modules = modules
        self.virtual_env = virtual_env
        if env is None:
            env = dict()
        self.env = env
        self.execution_model = execution_model
        self.executable = executable

        if isinstance(args, str):
            self.args = [args]  # type: Optional[List[str]]
        else:
            self.args = args

        self.can_share_resources = can_share_resources
        self.stateful = stateful

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # There's no ambiguity, and we want to allow some leeway
        # and savorize things, so disable recognition.
        pass

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

    _yatiml_defaults = {'execution_model': 'direct', 'stateful': 'stateful'}

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


class ResourceRequirements:
    """Describes resources to allocate for components.

    Attributes:
        name: Name of the component to configure.
    """
    def __init__(self, name: Reference) -> None:
        """Create a ResourceRequirements description.

        Args:
            name: Name of the component to configure.
        """
        self.name = name

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        raise yatiml.RecognitionError(
                'Please specify either "threads" or "mpi_processes".')


class ThreadedResReq(ResourceRequirements):
    """Describes resources for threaded implementations.

    This includes singlethreaded and multithreaded implementations
    that do not support MPI. As many cores as specified will be
    allocated on a single node, for each instance.

    Attributes:
        name: Name of the component to configure.
        threads: Number of threads/cores per instance.
    """

    def __init__(self, name: Reference, threads: int) -> None:
        """Create a ThreadedResourceRequirements description.

        Args:
            name: Name of the component to configure.
            threads: Number of threads (cores) per instance.
        """
        super().__init__(name)
        self.threads = threads


class MPICoresResReq(ResourceRequirements):
    """Describes resources for simple MPI implementations.

    This allocates individual cores or sets of cores on the same node
    for a given number of MPI processes per instance.

    Attributes:
        name: Name of the component to configure.
        mpi_processes: Number of MPI processes to start.
        threads_per_mpi_process: Number of threads/cores per process.
    """

    def __init__(
            self, name: Reference, mpi_processes: int,
            threads_per_mpi_process: int = 1) -> None:
        """Create a ThreadedMPIResourceRequirements description.

        Args:
            name: Name of the component to configure.
            mpi_processes: Number of MPI processes to start.
            threads_per_mpi_process: Number of threads/cores per
                    process. Defaults to 1.
        """
        super().__init__(name)
        self.mpi_processes = mpi_processes
        self.threads_per_mpi_process = threads_per_mpi_process

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.remove_attributes_with_default_values(cls)


class MPINodesResReq(ResourceRequirements):
    """Describes resources for node based MPI implementations.

    This allocates resources for an MPI process in terms of nodes and
    cores, processes and threads on them.

    Attributes:
        name: Name of the component to configure.
        nodes: Number of nodes to reserve.
        mpi_processes_per_node: Number of MPI processes to start on
                each node.
        threads_per_mpi_process: Number of threads/cores per process.
    """

    def __init__(
            self, name: Reference, nodes: int,
            mpi_processes_per_node: int, threads_per_mpi_process: int = 1
            ) -> None:
        """Create a NodeBasedMPIResourceRequirements description.

        Args:
            name: Name of the component to configure.
            nodes: Number of nodes to reserve.
            mpi_processes_per_node: Number of MPI processes to start
                    on each node.
            threads_per_mpi_process: Number of threads/cores per
                    process. Defaults to 1.
        """
        super().__init__(name)
        self.nodes = nodes
        self.mpi_processes_per_node = mpi_processes_per_node
        self.threads_per_mpi_process = threads_per_mpi_process

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.remove_attributes_with_default_values(cls)
