"""This module contains all the definitions for yMMSL."""
import logging
import re
from collections import OrderedDict, UserString
from typing import Any, Generator, List, Union

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

    def __init__(self, parts: Union[str, List[ReferencePart]]) -> None:
        if isinstance(parts, str):
            self.__parts = self.__string_to_parts(parts)
        elif len(parts) > 0 and not isinstance(parts[0], Identifier):
            raise ValueError('The first part of a Reference must be an Identifier')
        else:
            self.__parts = parts

    def __str__(self) -> str:
        return self.__parts_to_string(self.__parts)

    def __len__(self) -> int:
        return len(self.__parts)

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Reference):
            return self.__parts == other.__parts
        if isinstance(other, str):
            return str(self) == other
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, Reference):
            return self.__parts != other.__parts
        if isinstance(other, str):
            return str(self) != other
        return NotImplemented

    def __iter__(self) -> Generator[ReferencePart, None, None]:
        for part in self.__parts:
            yield part

    def __getitem__(self, key: Union[int, slice]) -> Union['Reference', ReferencePart]:
        if isinstance(key, int):
            return self.__parts[key]
        if isinstance(key, slice):
            return Reference(self.__parts[key])
        raise ValueError('Subscript must be either an int or a slice')

    def __setitem__(self, key: Union[int, slice], value: Any) -> None:
        raise RuntimeError('Reference objects are immutable, please don\'t try'
                           ' to change them.')

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
