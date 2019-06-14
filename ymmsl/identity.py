"""This module contains definitions for identity."""
from copy import copy
import logging
import re
from collections import OrderedDict, UserString
from typing import Any, Generator, Iterable, List, Union, overload

import yatiml
from ruamel import yaml


class Identifier(UserString):
    """A custom string type that represents an identifier.

    An identifier may consist of upper- and lowercase characters, digits, and \
    underscores.
    """
    def __init__(self, seq: Any) -> None:
        """Create an Identifier.

        This creates a new identifier object, using the string
        representation of whichever object you pass.

        Raises:
            ValueError: If the argument's string representation does
                    not form a valid Identifier.
        """
        super().__init__(seq)
        logging.debug('Identifier from {}'.format(seq))
        if not re.fullmatch(
                r'[a-zA-Z_]\w*', self.data, flags=re.ASCII):
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

    Reference objects act like a list of Identifiers and ints, you can
    get their length using len(), iterate through the parts using a
    loop, and get sublists or individual items using []. Note that the
    sublist has to be a valid Reference, so it cannot start with an
    int.

    References can be compared for equality to each other or to a
    plain string, and they can be used as dictionary keys. Reference
    objects are immutable (or they're supposed to be anyway), so do not
    try to change any of the elements. Instead, make a new Reference.
    Especially References that are used as dictionary keys must not be
    modified, this will get your dictionary in a very confused state.
    """

    def __init__(self, parts: Union[str, List[ReferencePart]]) -> None:
        """Create a Reference.

        Creates a Reference from either a string, which will be parsed,
        or a list of Identifiers and ints.

        Args:
            parts: Either a list of parts, or a string to parse.

        Raises:
            ValueError: If the argument does not define a valid
                    Reference.
        """
        if isinstance(parts, str):
            self.__parts = self.__string_to_parts(parts)
        elif len(parts) > 0 and not isinstance(parts[0], Identifier):
            raise ValueError('The first part of a Reference must be an Identifier')
        else:
            self.__parts = parts

    def __str__(self) -> str:
        """Convert the Reference to string form.
        """
        return self.__parts_to_string(self.__parts)

    def __repr__(self) -> str:
        """Produce a representation in string form.
        """
        return 'Reference("{}")'.format(str(self))

    def __len__(self) -> int:
        """Return the number of parts in the Reference.
        """
        return len(self.__parts)

    def __hash__(self) -> int:
        """Calculate a hash value for use by dicts.
        """
        return hash(str(self))

    def __eq__(self, other: Any) -> bool:
        """Compare for equality.

        Will compare part-by-part if the other argument is a Reference,
        or string representations if the other argument is a string.

        Args:
            other: Another Reference or a string.
        """
        if isinstance(other, Reference):
            return self.__parts == other.__parts
        if isinstance(other, str):
            return str(self) == other
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        """Compare for equality.

        Will compare part-by-part if the other argument is a Reference,
        or string representations if the other argument is a string.

        Args:
            other: Another Reference or a string.
        """
        if isinstance(other, Reference):
            return self.__parts != other.__parts
        if isinstance(other, str):
            return str(self) != other
        return NotImplemented

    def __iter__(self) -> Generator[ReferencePart, None, None]:
        """Iterate through the parts.

        Yields:
            Each part in turn from left to right.
        """
        for part in self.__parts:
            yield part

    @overload
    def __getitem__(self, key: int) -> ReferencePart:
        ...

    @overload
    def __getitem__(self, key: slice) -> 'Reference':
        ...

    def __getitem__(self, key: Union[int, slice]) -> Union['Reference', ReferencePart]:
        """Get a part or a slice.

        If passed an int, e.g. ref[2], will return that part as an int
        or an Identifier. If passed a slice, e.g. ref[2:], will return
        a Reference comprising those parts. This must be a valid
        Reference, so it must start with an Identifier.

        Args:
            key: Which part to return.

        Returns:
            A part or a sub-Reference.

        Raises:
            ValueError: If the argument is not an int or a slice.
        """
        if isinstance(key, int):
            return self.__parts[key]
        if isinstance(key, slice):
            return Reference(self.__parts[key])
        raise ValueError('Subscript must be either an int or a slice')

    def __setitem__(self, key: Union[int, slice], value: Any) -> None:
        """Does not set the value of a part.

        References are immutable, so they should not be modified, and
        this method just gives an error.

        Raises:
            RuntimeError: Always.
        """
        raise RuntimeError('Reference objects are immutable, please don\'t try'
                           ' to change them.')

    def __add__(self, other: Union['Reference', Iterable[ReferencePart],
                ReferencePart]) -> 'Reference':
        """Concatenates something onto a Reference.

        The object to add on can be another Reference, a list of
        reference parts (either int or Identifier), or an int or an
        Identifier. A new Reference will be created equal to the
        original one with the new part attached on the right.

        Args:
            other: The object to concatenate.

        Returns:
            A new concatenated Reference.
        """
        ret = Reference(copy(self.__parts))
        if isinstance(other, Reference):
            ret.__parts.extend(other.__parts)
        elif isinstance(other, int) or isinstance(other, Identifier):
            ret.__parts.append(other)
        elif hasattr(other, '__iter__'):
            ret.__parts.extend(other)
        return ret

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
        return OrderedDict([('parts', self.__parts)])

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        parts = node.get_attribute('parts').seq_items()
        text = str(parts[0].get_value())
        for part in parts[1:]:
            if part.is_scalar(str):
                text += '.{}'.format(part.get_value())
            elif part.is_scalar(int):
                text += '[{}]'.format(part.get_value())
            else:
                raise RuntimeError('Cannot serialise invalid reference')
        node.set_value(text)

    @classmethod
    def __string_to_parts(cls, text: str) -> List[ReferencePart]:
        """Parse a string into a list of parts.

        Args:
            text: The string to parse.

        Raises:
            ValueError: If the string does not represent a valid
                    Reference.
        """
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
        """Convert a list of parts to its string representation.

        Args:
            parts: The parts to represent.

        Returns:
            Their string form.
        """
        text = str(parts[0])
        for part in parts[1:]:
            if isinstance(part, int):
                text += '[{}]'.format(part)
            else:
                text += '.{}'.format(part)
        return text
