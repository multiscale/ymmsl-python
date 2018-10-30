"""This module contains all the definitions for yMMSL."""
import logging
from typing import List, Optional, Union

import yatiml

from ymmsl.identity import Reference


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

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if float(str(node.get_attribute('origin').get_value())) == 0.0:
            node.remove_attribute('origin')


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
                 parameter_values: Optional[List[Setting]] = None) -> None:
        self.model = model
        self.scales = scales
        self.parameter_values = parameter_values if parameter_values else list()

    @classmethod
    def yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        pass

    @classmethod
    def yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.map_attribute_to_seq('scales', 'scale')
        node.map_attribute_to_seq('parameter_values', 'parameter', 'value')

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.seq_attribute_to_map('scales', 'scale')
        if len(node.get_attribute('parameter_values').seq_items()) == 0:
            node.remove_attribute('parameter_values')
        else:
            node.seq_attribute_to_map('parameter_values', 'parameter', 'value')
