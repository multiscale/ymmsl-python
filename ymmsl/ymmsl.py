"""This module contains all the definitions for yMMSL."""
import logging
import re
from collections import OrderedDict, UserString
from typing import Any, cast, Dict, List, Optional, Union

import yatiml
from ruamel import yaml


class Identifier(UserString):
    """A custom string type that represents an identifier.

    An identifier may consist of upper- and lowercase characters, digits, and \
    underscores.
    """

    def __init__(self, seq: Any) -> None:
        super().__init__(seq)
        logging.debug('Identifier from {}'.format(seq))
        if not re.fullmatch(
                '[a-zA-Z_]\w*', self.data, flags=re.ASCII):  # type: ignore
            raise ValueError('Identifiers must consist only of'
                             ' lower- and uppercase letters, digits and'
                             ' underscores, must start with a letter or'
                             ' an underscore, and must not be empty.')


ReferencePart = Union[Identifier, int]


class Reference:
    """A reference to an object in the MMSL execution model.

    References in string form are written as either:

    -  an Identifier,
    -  a Reference followed by a period and an Identifier, or
    -  a Reference followed by an integer enclosed in square brackets.

    In object form, they consist of a list of Identifiers and ints. The \
    first list item is always an Identifier. For the rest of the list, \
    an Identifier represents a period operator with that argument, \
    while an int represents the indexing operator with that argument.

    Attributes:
        parts: List of parts, as described above.
    """

    def __init__(self, parts: List[ReferencePart]) -> None:
        if len(parts) > 0 and not isinstance(parts[0], Identifier):
            raise ValueError('The first part of a Reference must be an Identifier')
        self.parts = parts

    @classmethod
    def from_string(cls, text: str) -> 'Reference':
        result = Reference(list())
        result.parts = cls.__string_to_parts(text)
        return result

    def __str__(self) -> str:
        return self.__parts_to_string(self.parts)

    def __getitem__(self, key: Union[int, slice]) -> 'Reference':
        if isinstance(key, int):
            return Reference([self.parts[key]])
        elif isinstance(key, slice):
            return Reference(self.parts[key])
        else:
            raise ValueError('Subscript must be either an int or a slice')

    @classmethod
    def yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_scalar(str)

    @classmethod
    def yatiml_savorize(cls, node: yatiml.Node) -> None:
        text = str(node.get_value())
        parts = cls.__string_to_parts(text)

        # We need to make a yaml.SequenceNode by hand here, since
        # set_attribute doesn't take lists as an argument.
        start_mark = node.yaml_node.start_mark
        end_mark = node.yaml_node.end_mark
        item_nodes = list()
        for part in parts:
            if isinstance(part, Identifier):
                new_node = yaml.ScalarNode('!Identifier', str(part),
                                           start_mark, end_mark)
            elif isinstance(part, int):
                new_node = yaml.ScalarNode('tag:yaml.org,2002:int', str(part),
                                           start_mark, end_mark)
            item_nodes.append(new_node)

        ynode = yaml.SequenceNode('tag:yaml.org,2002:seq', item_nodes,
                                  start_mark, end_mark)
        node.make_mapping()
        node.set_attribute('parts', ynode)

    def yatiml_attributes(self) -> OrderedDict:
        return OrderedDict([('parts', self.parts)])

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        parts_nodes = node.get_attribute('parts').seq_items()
        parts_list = list(map(yatiml.Node.get_value, parts_nodes))
        text = str(parts_list[0])
        for part in parts_list[1:]:
            if isinstance(part, str):
                text += '.{}'.format(part)
            elif isinstance(part, int):
                text += '[{}]'.format(part)
            else:
                raise RuntimeError('Cannot serialise invalid reference')
        node.set_value(text)

    @classmethod
    def __string_to_parts(cls, text: str) -> List[ReferencePart]:
        def find_next_op(text: str, start: int) -> int:
            next_bracket = text.find('[', start)
            if next_bracket == -1:
                next_bracket = len(text)
            next_period = text.find('.', start)
            if next_period == -1:
                next_period = len(text)
            return min(next_period, next_bracket)

        end = len(text)
        cur_op = find_next_op(text, 0)
        parts = [Identifier(text[0:cur_op])]  # type: List[ReferencePart]
        while cur_op < end:
            if text[cur_op] == '.':
                next_op = find_next_op(text, cur_op + 1)
                parts.append(Identifier(text[cur_op + 1:next_op]))
                cur_op = next_op
            elif text[cur_op] == '[':
                close_bracket = text.find(']', cur_op)
                if close_bracket == -1:
                    raise ValueError('Missing closing bracket in Reference {}'
                                     ''.format(text))
                try:
                    index = int(text[cur_op + 1:close_bracket])
                except ValueError:
                    raise ValueError('Invalid index \'{}\' in {}, expected an'
                                     ' int'.format(
                                         text[cur_op + 1:close_bracket], text))
                parts.append(index)
                cur_op = close_bracket + 1
            else:
                raise ValueError('Invalid character \'{}\' encountered in'
                                 ' Reference {}'.format(text[cur_op], text))
        return parts

    @classmethod
    def __parts_to_string(cls, parts: List[ReferencePart]) -> str:
        text = str(parts[0])
        for part in parts[1:]:
            if isinstance(part, int):
                text += '[{}]'.format(part)
            else:
                text += '.{}'.format(part)
        return text


class ComputeElementDecl:
    """An object declaring a compute element.

    Compute elements are things like submodels, scale bridges, proxies, \
    and any other program that makes up a simulation. This class \
    represents a declaration of an array of instances of a compute \
    element, and it's used to describe which instances are needed to \
    perform a certain simulation.

    Attributes:
        name: The name of this compute element.
        implementation: A reference to the implementation to use.
        count: The number of instances that execute simultaneously.
    """

    def __init__(self, name: Identifier, implementation: Reference, count: int = 1) -> None:
        self.name = name
        self.implementation = implementation
        self.count = count

        for part in self.implementation.parts:
            if isinstance(part, int):
                raise ValueError('Compute element implementation {} contains a'
                                 ' subscript which is not allowed.'.format(self.name))

    def __str__(self) -> str:
        return '{}[{}]'.format(self.name, self.count)


class Conduit:
    """A conduit transports data between compute elements.

    The references to the sender and receiver must be of one of the \
    following forms:

    - submodel.port
    - namespace.submodel.port (or several namespace prefixes)
    - submodel[3].port (for any value of 3)
    - submodel.port[5] (for any value of 5)

    Or a combination, e.g. namespace.submodel[3].port[4]

    Attributes:
        sender: The sending port that this conduit is connected to. Of \
                the form 'submodel.port_name'.
        receiver: The receiving port that this conduit is connected to. \
                Of the form 'submodel.port_name'.
    """
    def __init__(self, sender: Reference,
                 receiver: Reference) -> None:
        self.sender = sender
        self.receiver = receiver

        self.__check_reference(sender)
        self.__check_reference(receiver)

    def __check_reference(self, ref: Reference) -> None:
        # find last Identifier
        i = len(ref.parts) - 1
        while i >= 0 and isinstance(ref.parts[i], int):
            i -= 1

        # check port subscript, if any
        if len(ref.parts) - 1 - i > 1:
            raise ValueError('In reference {}: Ports can only have a single'
                             ' subscript.'.format(ref))

        # move to before last Identifier
        i -= 1

        # skip model subscripts, if any
        while i >= 0 and isinstance(ref.parts[i], int):
            i -= 1

        if i < 0:
            raise ValueError('Reference {} does not reference any compute'
                             ' element. You need both a compute element part'
                             ' and a port name part.'.format(ref))

        # check that model designator is a list of only identifiers
        while i >= 0:
            if not isinstance(ref.parts[i], Identifier):
                raise ValueError('Reference {} contains a subscript inside the'
                                 ' compute element part.'.format(ref))
            i -= 1

    def sending_compute_element(self) -> Reference:
        """Returns a reference to the sending compute element."""
        return self.__compute_element_part(self.sender)

    def sending_port(self) -> Reference:
        """Returns a reference to the sending port.

        This is either a single Identifier, or an Identifier followed \
        by an int, if a particular slot in the port was referred to.
        """
        return self.__port_name_part(self.sender)

    def receiving_compute_element(self) -> Reference:
        """Returns a reference to the receiving compute element."""
        return self.__compute_element_part(self.receiver)

    def receiving_port(self) -> Reference:
        """Returns the identity of the receiving port.

        This is either a single Identifier, or an Identifier followed \
        by an int, if a particular slot in the port was referred to.
        """
        return self.__port_name_part(self.receiver)

    def __compute_element_part(self, ref: Reference) -> Reference:
        return ref[0:self.__port_name_index(ref)]

    def __port_name_part(self, ref: Reference) -> Reference:
        return ref[self.__port_name_index(ref):]

    def __port_name_index(self, ref: Reference) -> int:
        # last identifier is the port name
        i = len(ref.parts) - 1
        while i >= 0 and isinstance(ref.parts[i], int):
            i -= 1
        return i


class Simulation:
    """Describes a simulation model.

    A model consists of a number of compute elements connected by \
    conduits.

    Attributes:
        name: The name by which this simulation model is known to \
                the system.
        compute_elements: A list of compute elements making up the \
                simulation.
        conduits: A list of conduits connecting the compute elements.
    """
    def __init__(self, name: Identifier,
                 compute_elements: List[ComputeElementDecl],
                 conduits: List[Conduit]) -> None:
        self.name = name
        self.compute_elements = compute_elements
        self.conduits = conduits

    @classmethod
    def yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        pass

    @classmethod
    def yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.map_attribute_to_seq('compute_elements', 'name')

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.seq_attribute_to_map('compute_elements', 'name')


class ScaleSettings:
    """Settings for a spatial or temporal scale.

    Attributes:
        scale: Reference to the scale these values are for.
        grain: The step size, grid spacing or resolution.
        extent: The overall size.
    """

    def __init__(self, scale: Reference, grain: float, extent: float, origin: float = 0.0) -> None:
        self.scale = scale
        self.grain = grain
        self.extent = extent
        self.origin = origin


ParameterValue = Union[str, int, float, List[float], List[List[float]]]


class Setting:
    """Settings for arbitrary parameters.

    Attributes:
        parameter: Reference to the parameter to set.
        value: The value to set it to.
    """

    def __init__(self, parameter: Reference, value: ParameterValue) -> None:
        # TODO: Expression
        self.parameter = parameter
        self.value = value

    @classmethod
    def yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_mapping()


class Experiment:
    """Settings for doing an experiment.

    An experiment is done by running a model with particular settings, \
    for the submodel scales and other parameters.

    Attributes:
        model: The identifier of the model to run.
        scale: The scales to run the submodels at.
        parameter_values: The parameter values to initialise the models \
                with.
    """

    def __init__(self, model: Reference, scales: List[ScaleSettings],
                 parameter_values: List[Setting]) -> None:
        self.model = model
        self.scales = scales
        self.parameter_values = parameter_values


class Ymmsl:
    """A yMMSL document.

    This is the top-level class for yMMSL data.

    Attributes:
        experiment: An experiment to run.
    """

    def __init__(self,
            version: str,
            experiment: Optional[Experiment] = None,
            simulation: Optional[Simulation] = None
            ) -> None:
        self.version = version
        self.experiment = experiment
        self.simulation = simulation

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute('experiment').is_scalar(type(None)):
            node.remove_attribute('experiment')
        if node.get_attribute('simulation').is_scalar(type(None)):
            node.remove_attribute('simulation')
