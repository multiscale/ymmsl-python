"""Definitions for specifying how to start a component."""
from typing import cast, List, Union

from ruamel import yaml
import yatiml

from ymmsl.identity import Reference


class Implementation:
    """Describes an installed implementation.

    Attributes:
        name: Name of the implementation
        script (str): A script that starts the implementation.
    """

    def __init__(
            self, name: Reference, script: Union[str, List[str]]) -> None:
        """Create an Implementation description.

        If script is a list, each string in it is a line, and the
        lines will be concatenated into a single string to put into
        the script attribute.

        Args:
            name: Name of the implementation
            script: Script that starts the implementation
        """
        self.name = name

        if isinstance(script, list):
            self.script = '\n'.join(script)
        else:
            self.script = script

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


class Resources:
    """Describes resources to allocate for components.

    Attributes:
        name: Name of the component to configure.
        num_cores: Number of CPU cores to reserve.
    """

    def __init__(self, name: Reference, num_cores: int) -> None:
        """Create a Resources description.

        Args:
            name: Name of the component to configure
            num_cores: Number of CPU cores to reserve.
        """
        self.name = name
        self.num_cores = num_cores
