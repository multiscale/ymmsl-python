from copy import deepcopy
from typing import Optional

import ymmsl.v0_1 as v0_1
import ymmsl.v0_2 as v0_2


def convert_v0_1_to_v0_2(config: v0_1.PartialConfiguration) -> v0_2.Configuration:
    """Convert a v0.1 ymmsl object to v0.2.

    Args:
        config: An input configuration in yMMSL v0.1 format

    Returns:
        The corresponding configuration expressed in yMMSL v0.2.
    """
    description = '' if config.description is None else config.description
    model = convert_model(config.model) if config.model is not None else None
    settings = deepcopy(config.settings)
    resources = deepcopy(config.resources)
    checkpoints = deepcopy(config.checkpoints)
    resume = deepcopy(config.resume)

    return v0_2.Configuration(
            description, model, settings, resources, checkpoints, resume)


def convert_component(component: v0_1.Component) -> v0_2.Component:
    """Convert a v0.1 Component object to a v0.2 Component."""
    ports = component.ports if component.ports else v0_1.Ports()
    implementation: Optional[str] = None
    if component.implementation is not None:
        implementation = str(component.implementation)

    return v0_2.Component(
            str(component.name), ports, implementation, component.multiplicity)


def convert_conduit(conduit: v0_1.Conduit) -> v0_2.Conduit:
    """Convert a v0.1 Conduit to a v0.2 Conduit."""
    return v0_2.Conduit(str(conduit.sender), str(conduit.receiver))


def convert_model(model: v0_1.ModelReference) -> v0_2.Model:
    """Convert a v0.1 ModelReference object to a v0.2 Model.

    Args:
        model: A ModelReference or Model to convert

    Returns:
        The corresponding configuration expressed in yMMSL v0.2.
    """
    if isinstance(model, v0_1.Model):
        return v0_2.Model(
                str(model.name), None, list(map(convert_component, model.components)),
                list(map(convert_conduit, model.conduits)))
    else:
        return v0_2.Model(str(model.name), None, [], [])
