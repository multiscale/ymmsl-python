"""This module contains all the definitions for yMMSL."""
import re
from collections import UserString
from typing import Any, Dict, List, Union

import yatiml


class Identifier(UserString):
    """A custom string type that represents an identifier.

    An identifier may consist of upper- and lowercase characters, digits, and \
    underscores.
    """

    def __init__(self, seq: Any) -> None:
        super().__init__(seq)
        if not re.fullmatch(
                '[a-zA-Z_]\w*', self.data, flags=re.ASCII):  # type: ignore
            raise ValueError('Identifiers must consist only of'
                             ' lower- and uppercase letters, digits and'
                             ' underscores, must start with a letter or'
                             ' an underscore, and must not be empty.')


class ComputeElementIdentifier:
    """An identifier in yMMSL.

    Identifiers consist of an initial Identifier, followed by zero or \
    more square-bracket enclosed integers.

    Attributes:
        base: The initial base identifier string.
        indexes: A list of indexes.
    """

    def __init__(self, text: str) -> None:
        name_indexes = text.split('[')
        self.base = Identifier(name_indexes[0])

        self.indexes = list()  # type: List[int]
        for idx_str in name_indexes[1:]:
            if idx_str[-1] != ']':
                raise ValueError(
                    'Missing closing bracket in identifier {}'.format(text))
            try:
                self.indexes.append(int(idx_str[:-1]))
            except ValueError:
                raise ValueError(
                    'Non-integer index in identifier {}'.format(text))

    def __str__(self) -> str:
        def enclose(val: int) -> str:
            return '[{}]'.format(val)

        return '{}{}'.format(self.base, ''.join(map(enclose, self.indexes)))


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

    def __init__(self, text: str) -> None:
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
        self.parts = [Identifier(
            text[0:cur_op])]  # type: List[Union[Identifier, int]]
        while cur_op < end:
            if text[cur_op] == '.':
                next_op = find_next_op(text, cur_op + 1)
                self.parts.append(Identifier(text[cur_op + 1:next_op]))
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
                self.parts.append(index)
                cur_op = close_bracket + 1
            else:
                raise ValueError('Invalid character \'{}\' encountered in'
                                 ' Reference {}'.format(text[cur_op], text))

    def __str__(self) -> str:
        result = ''
        for part in self.parts:
            if isinstance(part, int):
                result += '[{}]'.format(part)
            elif isinstance(part, Identifier):
                if result == '':
                    result = str(part)
                else:
                    result += '.{}'.format(part)
        return result


class ScaleValues:
    """Settings for a spatial or temporal scale.

    Attributes:
        scale: Reference to the scale these values are for.
        grain: The step size, grid spacing or resolution.
        extent: The overall size.
    """

    def __init__(self, scale: Reference, grain: float, extent: float) -> None:
        self.scale = scale
        self.grain = grain
        self.extent = extent


class Setting:
    """Settings for arbitrary parameters.

    Attributes:
        parameter: Reference to the parameter to set.
        value: The value to set it to.
    """

    def __init__(self, parameter: Reference,
                 value: Union[str, int, float]) -> None:
        # TODO: Expression, (nested) lists
        self.parameter = parameter
        self.value = value


class Experiment:
    """Settings for doing an experiment.

    An experiment is done by running a model with particular settings, \
    for the submodel scales and other parameters.

    Attributes:
        model: The identifier of the model to run.
        scale_valuess: The scales to run the submodels at.
        parameter_values: The parameter values to initialise the models \
                with.
    """

    def __init__(self, model: Reference, scale_values: List[ScaleValues],
                 parameter_values: List[Setting]) -> None:
        self.model = model
        self.scale_values = scale_values
        self.parameter_values = parameter_values


class Ymmsl:
    """A yMMSL document.

    This is the top-level class for yMMSL data.

    Attributes:
        experiment: An experiment to run.
    """

    def __init__(self, experiment: Experiment) -> None:
        self.experiment = experiment
