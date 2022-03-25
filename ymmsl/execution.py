"""Definitions for specifying how to start a component."""
from abc import ABC
import logging
from pathlib import Path
from typing import cast, Dict, List, Optional, Union

from ruamel import yaml
import yatiml

from ymmsl.identity import Reference


class Implementation:
    """Describes an installed implementation.

    An Implementation normally has an ``executable`` and any other
    needed attributes, with ``script`` set to None. You should specify
    a script only as a last resort, probably after getting some help
    from the authors of this library. If a script is specified, all
    other attributes except for the name must be ``None``.

    Attributes:
        name: Name of the implementation
        modules: HPC software modules to load
        virtual_env: Path to a virtual env to activate
        env: Environment variables to set
        mpi: Whether the implementation uses MPI
        executable: Full path to executable to run
        args: Arguments to pass to the executable
        script: A script that starts the implementation
    """

    def __init__(
            self,
            name: Reference,
            modules: Union[str, List[str], None] = None,
            virtual_env: Optional[Path] = None,
            env: Optional[Dict[str, str]] = None,
            mpi: Optional[bool] = None,
            executable: Optional[Path] = None,
            args: Union[str, List[str], None] = None,
            script: Union[str, List[str], None] = None
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
            mpi: Whether the implementation uses MPI
            executable: Full path to executable to run
            args: Arguments to pass to the executable
            script: Script that starts the implementation
        """
        if script is not None:
            if (
                    modules is not None or virtual_env is not None or
                    env is not None or mpi is not None or
                    executable is not None or args is not None):
                raise RuntimeError(
                        'When creating an Implementation, script was specified'
                        ' together with another argument, which is not'
                        ' allowed. Please specify either a script or an'
                        ' executable.')

        if executable is not None and script is not None:
            raise RuntimeError(
                    'When creating an Implementation, neither a script nor'
                    ' an executable was given. Please specify either one.')

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
        self.env = env
        self.mpi = mpi
        self.executable = executable

        if isinstance(args, str):
            self.args = [args]  # type: Optional[List[str]]
        else:
            self.args = args

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # There's no ambiguity, and we want to allow some leeway
        # and savorize things, so disable recognition.
        pass

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.has_attribute('env'):
            logging.warning('env')
            env_node = node.get_attribute('env')
            if env_node.is_mapping():
                logging.warning('map')
                for _, value_node in env_node.yaml_node.value:
                    if isinstance(value_node, yaml.ScalarNode):
                        logging.warning('vn: %s', value_node)
                        if value_node.tag == 'tag:yaml.org,2002:int':
                            value_node.tag = 'tag:yaml.org,2002:str'
                        if value_node.tag == 'tag:yaml.org,2002:float':
                            value_node.tag = 'tag:yaml.org,2002:str'
                        if value_node.tag == 'tag:yaml.org,2002:bool':
                            value_node.tag = 'tag:yaml.org,2002:str'

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        script_node = node.get_attribute('script')
        if script_node.is_scalar(str):
            text = cast(str, script_node.get_value())
            if '\n' in text:
                # make a sequence of lines
                lines = text.split('\n')
                start_mark = node.yaml_node.start_mark
                end_mark = node.yaml_node.end_mark
                lines_nodes = [
                        yaml.ScalarNode(
                            'tag:yaml.org,2002:str', line, start_mark,
                            end_mark)
                        for line in lines]
                seq_node = yaml.SequenceNode(
                        'tag:yaml.org,2002:seq', lines_nodes, start_mark,
                        end_mark)
                node.set_attribute('script', seq_node)

        node.remove_attributes_with_default_values(cls)


class ResourceRequirements(ABC):
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
                'Please specify either threads or mpi_processes.')


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
