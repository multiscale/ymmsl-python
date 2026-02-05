from copy import deepcopy
from typing import Dict, List, Optional
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
    if programs:
        warnings.warn(
                'In yMMSL v0.2 implementations have become programs, and you can now'
                ' specify the ports of a program in the yMMSL description. If your'
                ' program has fixed ports then you should do this, because it will make'
                ' incorrect wiring easier to debug. While there, add a description too!'
                )

    resources = deepcopy(config.resources)
    checkpoints = deepcopy(config.checkpoints)
    resume = deepcopy(config.resume)

    warnings.warn(
            'Comments can unfortunately not be read by this converter, and so have been'
            ' ignored. Please copy them into an appropriate description field.')

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
            str(component.name), convert_ports(ports), description, implementation,
            False, component.multiplicity)


def convert_conduit(conduit: v0_1.Conduit) -> v0_2.Conduit:
    """Convert a v0.1 Conduit to a v0.2 Conduit."""
    return v0_2.Conduit(str(conduit.sender), str(conduit.receiver))


def infer_ports(components: List[v0_2.Component], conduits: List[v0_2.Conduit]) -> None:
    """Infer component ports from conduits where absent.

    This can create an incorrect result, because we have to guess at the operators. We
    assume that they're F_INIT for receiving ports and O_F for sending ports, but this
    can be wrong. Only the user knows, so we'll warn them that they have to check.
    """
    changed_components = list()
    for component in components:
        if len(component.ports) == 0:
            for conduit in conduits:
                if conduit.sending_component() == component.name:
                    component.ports[conduit.sending_port()] = v0_2.Port(
                            conduit.sending_port(), v0_2.Operator.O_F,
                            v0_2.Timeline(''))
                    if component.name not in changed_components:
                        changed_components.append(component.name)

                if conduit.receiving_component() == component.name:
                    component.ports[conduit.receiving_port()] = v0_2.Port(
                            conduit.receiving_port(), v0_2.Operator.F_INIT,
                            v0_2.Timeline(''))
                    if component.name not in changed_components:
                        changed_components.append(component.name)

    if changed_components:
        ch_comp_list = '\n - ' + '\n - '.join(map(str, changed_components))
        warnings.warn(
                'In yMMSL v0.2 components are required to declare their ports. The'
                ' following components did not have a ports declaration, so one has'
                ' been added based on the connected conduits. THIS MAY BE WRONG,'
                ' because the operators have all been set to F_INIT and O_F, while they'
                ' may really be O_I or S. Please check these components and adjust'
                f' as needed: {ch_comp_list}')


def convert_model(model: v0_1.ModelReference) -> v0_2.Model:
    """Convert a v0.1 ModelReference object to a v0.2 Model.

    Args:
        model: A ModelReference or Model to convert

    Returns:
        The corresponding configuration expressed in yMMSL v0.2.
    """
    description = 'Please add a description'

    if isinstance(model, v0_1.Model):
        components = list(map(convert_component, model.components))
        conduits = list(map(convert_conduit, model.conduits))
        infer_ports(components, conduits)
        return v0_2.Model(
                str(model.name), None, description, None, components, conduits)
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
