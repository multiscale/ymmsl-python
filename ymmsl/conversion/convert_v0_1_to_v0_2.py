from copy import deepcopy
from typing import Dict, Optional
import warnings

import ymmsl.v0_1 as v0_1
import ymmsl.v0_2 as v0_2


def convert_v0_1_to_v0_2(config: v0_1.PartialConfiguration) -> v0_2.Configuration:
    """Convert a v0.1 ymmsl object to v0.2.

    Args:
        config: An input configuration in yMMSL v0.1 format

    Returns:
        The corresponding configuration expressed in yMMSL v0.2.
    """
    description = 'Please add a description'
    if config.description:
        description = config.description
    models = [convert_model(config.model)] if config.model is not None else None
    settings = deepcopy(config.settings)
    programs = [
            convert_implementation(impl) for impl in config.implementations.values()]
    resources = deepcopy(config.resources)
    checkpoints = deepcopy(config.checkpoints)
    resume = deepcopy(config.resume)

    return v0_2.Configuration(
            description, None, models, None, settings, programs, resources, checkpoints,
            resume)


def convert_component(component: v0_1.Component) -> v0_2.Component:
    """Convert a v0.1 Component object to a v0.2 Component."""
    ports = component.ports if component.ports else v0_1.Ports()
    description = 'Please add a description'
    implementation: Optional[str] = None
    if component.implementation is not None:
        implementation = str(component.implementation)

    return v0_2.Component(
            str(component.name), convert_ports(ports), description, False,
            implementation, component.multiplicity)


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
    description = 'Please add a description'
    if isinstance(model, v0_1.Model):
        return v0_2.Model(
                str(model.name), None, description, None,
                list(map(convert_component, model.components)),
                list(map(convert_conduit, model.conduits)))
    else:
        return v0_2.Model(str(model.name), None, description, None, [], [])


def convert_implementation(impl: v0_1.Implementation) -> v0_2.Program:
    """Convert a v0.1 Implementation object to a v0.2 Program.

    Note that v0.2 also has an Implementation, but that is now a base class of Program
    and Model, because in v0.2 models can be implementations too.

    Args:
        impl: An Implementation to convert

    Returns:
        The corresponding program expressed in yMMSL v0.2.
    """
    warnings.warn(
            'In yMMSL v0.2 implementations have become programs, and you can now'
            ' specify the ports of a program in the yMMSL description. If your program'
            ' has fixed ports then you should do this, because it will make incorrect'
            ' wiring easier to debug. While there, add a description too!')

    description = 'Please add a description'
    base_env: Optional[v0_1.BaseEnv] = impl.base_env
    env: Optional[Dict[str, str]] = impl.env

    execution_model = v0_2.ExecutionModel[impl.execution_model.name]

    if impl.script is not None:
        if base_env == v0_1.BaseEnv.MANAGER:
            base_env = None
        if not env:
            env = None

    return v0_2.Program(
                str(impl.name), None, description, None, base_env, impl.modules,
                impl.virtual_env, env, execution_model, impl.executable, impl.args,
                impl.script, impl.can_share_resources, impl.keeps_state_for_next_use)


def convert_ports(ports: v0_1.Ports) -> v0_2.Ports:
    """Convert a v0.1 Ports object to a v0.2 Ports.

    Args:
        ports: A Ports to convert

    Returns:
        The corresponding ports expressed in yMMSL v0.2.
    """
    return v0_2.Ports(
            list(map(str, ports.f_init)),
            list(map(str, ports.o_i)),
            list(map(str, ports.s)),
            list(map(str, ports.o_f)))
