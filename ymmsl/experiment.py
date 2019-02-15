"""This module contains all the definitions for yMMSL."""
from typing import List, Optional, Union

import yatiml

from ymmsl.identity import Reference


ParameterValue = Union[str, int, float, bool, List[float], List[List[float]]]


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
        parameter_values: The parameter values to initialise the models \
                with.
    """

    def __init__(self, model: Reference,
                 parameter_values: Optional[List[Setting]] = None) -> None:
        self.model = model
        self.parameter_values = parameter_values if parameter_values else list()

    @classmethod
    def yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        pass

    @classmethod
    def yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.map_attribute_to_seq('parameter_values', 'parameter', 'value')

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if len(node.get_attribute('parameter_values').seq_items()) == 0:
            node.remove_attribute('parameter_values')
        else:
            node.seq_attribute_to_map('parameter_values', 'parameter', 'value')
