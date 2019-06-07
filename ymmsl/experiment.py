"""This module contains all the definitions for yMMSL."""
from typing import Dict, List, Optional, Union

import yatiml

from ymmsl.identity import Reference


ParameterValue = Union[str, int, float, bool,
                       List[float], List[List[float]], yatiml.bool_union_fix]


class Setting:
    """Settings for arbitrary parameters.

    Attributes:
        parameter: Reference to the parameter to set.
        value: The value to set it to.
    """

    def __init__(self, parameter: str, value: ParameterValue) -> None:
        # TODO: Expression
        self.parameter = Reference(parameter)
        self.value = value

    @classmethod
    def yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_mapping()


    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        # format lists and arrays nicely
        value = node.get_attribute('value')
        if value.is_sequence():
            if len(value.seq_items()) > 0:
                if not value.seq_items()[0].is_sequence():
                    value.yaml_node.flow_style = True
                else:
                    value.yaml_node.flow_style = False
                    for row in value.seq_items():
                        row.yaml_node.flow_style = True

class Experiment:
    """Settings for doing an experiment.

    An experiment is done by running a model with particular settings, \
    for the submodel scales and other parameters.

    Attributes:
        model: The identifier of the model to run.
        parameter_values: The parameter values to initialise the models \
                with, as a list of Settings.
    """

    def __init__(
            self, model: str,
            parameter_values: Optional[
                Union[Dict[str, ParameterValue], List[Setting]]] = None
            ) -> None:
        """Create an Experiment.

        Args:
            model: Identifier of the model to run.
            parameter_values: The parameter values to initialise the models
                    with, as a list of Settings or as a dictionary.
        """
        self.model = Reference(model)
        self.parameter_values = list()  # type: List[Setting]

        if parameter_values:
            if isinstance(parameter_values, dict):
                for key, value in parameter_values.items():
                    self.parameter_values.append(Setting(key, value))
            else:
                self.parameter_values = parameter_values

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
