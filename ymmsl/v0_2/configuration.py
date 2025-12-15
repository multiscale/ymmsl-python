import collections.abc as abc
import logging
from pathlib import Path
from typing import (
        Dict, List, MutableMapping, Optional, Sequence, Union, cast)

import yatiml
import yaml

from ymmsl.v0_1.checkpoint import Checkpoints
from ymmsl.v0_1.execution import ResourceRequirements
from ymmsl.v0_1.identity import Reference
from ymmsl.v0_1.settings import Settings
from ymmsl.v0_2.document import Document
from ymmsl.v0_2.implementation import Implementation
from ymmsl.v0_2.program import Program
from ymmsl.v0_2.model import Component, Model


_logger = logging.getLogger(__name__)


class Configuration(Document):
    """Top-level class for all information in a yMMSL file.

    Attributes:
        description: A human-readable description of the configuration
        models: A list of possibly connected models to run
        settings: Settings to run the models with
        programs: Programs to use to run the model. Dictionary mapping program names (as
            References) to Program objects.
        resources: Resources to allocate for the model components.
            Dictionary mapping component names to ResourceRequirements objects.
        checkpoints: Defines when each model component should create a snapshot
        resume: Defines what snapshot each model component should resume from
    """
    def __init__(
            self, description: str,
            models: Optional[Union[Model, Sequence[Model]]] = None,
            settings: Optional[Settings] = None,
            programs: Optional[Union[
                Sequence[Program], MutableMapping[Reference, Program]]] = None,
            resources: Optional[Union[
                Sequence[ResourceRequirements],
                MutableMapping[Reference, ResourceRequirements]]] = None,
            checkpoints: Optional[Checkpoints] = None,
            resume: Optional[Dict[Reference, Path]] = None
            ) -> None:
        """Create a Configuration.

        Implementations and resources may be either a list of such
        objects, or a dictionary matching the attribute format (see
        above).

        Args:
            description: Human-readable description
            settings: Settings to run the model with.
            resources: Resources to allocate for the model components.
            checkpoints: When each component should create a snapshot
            resume: What snapshot each component should resume from

        """
        self.description = description

        # TODO: imports

        if models is None:
            self.models: Sequence[Model] = list()
        elif isinstance(models, Model):
            self.models = [models]
        else:
            self.models = models

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

        if programs is None:
            self.programs: MutableMapping[Reference, Program] = dict()
        elif isinstance(programs, abc.Sequence):
            self.programs = {prog.name: prog for prog in programs}
        else:
            self.programs = programs

        if resources is None:
            self.resources: MutableMapping[Reference, ResourceRequirements] = dict()
        elif isinstance(resources, abc.Sequence):
            self.resources = {res.name: res for res in resources}
        else:
            self.resources = resources

        if checkpoints is None:
            self.checkpoints = Checkpoints()
        else:
            self.checkpoints = checkpoints

        if resume is None:
            self.resume = dict()    # type: Dict[Reference, Path]
        else:
            self.resume = resume

    def check_consistent(self) -> None:
        """Checks that the configuration is internally consistent.

        This checks:

            - Whether all conduits are connected to existing components or to a model
              port
            - Whether ports on components are consistent with their implementations
            - That resources have been requested for each component that has an
              implementation

        If any of these requirements is false, this function will raise a RuntimeError
        with an explanation of the problem.
        """
        errors = list()

        program_component_paths = self._program_component_paths()
        for model in self.models:
            model.check_consistent()
            for component in model.components:
                if component in program_component_paths:
                    path = program_component_paths[component]

                    if path not in self.resources:
                        errors.append(
                                f'Component {path} is missing a resource request')

                errors.extend(self._check_consistent_ports(component))

                # TODO: check that resources and implementation both do or don't MPI

        if errors:
            raise RuntimeError(
                    'The configuration is internally inconsistent. The following'
                    ' problems were found:\n- '
                    f'{"\n- ".join(errors)}')

    def update(self, overlay: 'Configuration') -> None:
        """Update this configuration with the given overlay.

        This will copy settings from overlay on top of the current settings, and merge
        in the various parts according to their update() functions.

        Args:
            overlay: A configuration to overlay onto this one.
        """
        if not self.description:
            self.description = overlay.description
        elif overlay.description:
            self.description += '\n\n' + overlay.description

        if self.models and overlay.models:
            raise RuntimeError(
                    'Multiple ymmsl files containing models specified. Please'
                    ' use the import functionality instead.')

        self.settings.update(overlay.settings)

        overlap = [p for p in self.programs if p in overlay.programs]
        if any(overlap):
            raise RuntimeError(
                    'Multiple programs with the same name were found. Please ensure'
                    ' that all programs have a unique name. The duplicate names were:'
                    f' {", ".join(map(str, overlap))}.')
        self.programs.update(overlay.programs)

        self.resources.update(overlay.resources)

        self.checkpoints.update(overlay.checkpoints)
        self.resume.update(overlay.resume)

    def _top_models(self) -> List[Model]:
        """Models in this configuration that are not used as implementations."""
        top_models = {model.name: model for model in self.models}

        for model in self.models:
            for component in model.components:
                if component.implementation in top_models:
                    del top_models[component.implementation]

        return list(top_models.values())

    def _program_component_paths(self) -> Dict[Component, Reference]:
        """Return component paths for program-implemented components.

        Component paths are of the form component1.component2, where component1 is a
        component inside the top-level model that has an implementation which is a
        submodel, and component2 is a component inside that submodel.

        The returned dict contains only components that have a program for their
        implementation; components with no implementation or whose implementation is a
        model are not included.
        """
        models_by_name = {model.name: model for model in self.models}

        result = dict()
        queue = [(m, Reference([])) for m in self._top_models()]

        while queue:
            model, prefix = queue.pop(0)
            for component in model.components:
                if component.implementation in models_by_name:
                    queue.append((
                        models_by_name[component.implementation],
                        prefix + component.name))
                elif component.implementation is not None:
                    result[component] = prefix + component.name

        return result

    def _check_consistent_ports(self, component: Component) -> List[str]:
        """Check that components have implementations with compatible ports.

        This checks that each component declares ports that its implementation also
        declares, if it has an implementation and the implementation has a ports
        declaration.

        Returns a list of errors, or an empty list if all is okay.
        """
        def check_ports(cmp: Component, impl: Implementation, op: str) -> List[str]:
            """Check two sets of ports, return errors"""
            cmp_ports = set(getattr(cmp.ports, op))
            impl_ports = set(getattr(impl.ports, op))
            missing_ports = cmp_ports - impl_ports
            if missing_ports:
                return [
                        f'Component {cmp.name} declares {op} ports'
                        f' ({", ".join(map(str, missing_ports))}) that its'
                        f' implementation {impl.name} does not have.']

            return []

        errors = list()

        if component.implementation is not None:
            if component.implementation in self.programs:
                impl = self.programs[component.implementation]
                if list(impl.ports.all_ports()):
                    errors += check_ports(component, impl, 'f_init')
                    errors += check_ports(component, impl, 'o_i')
                    errors += check_ports(component, impl, 's')
                    errors += check_ports(component, impl, 'o_f')

        return errors

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # Because of the syntactic sugar below, the YAML doesn't match the types
        # declared above. So we override recognition, and since the attributes are
        # almost all optional, we have nothing to check except that it's a valid
        # (v0.2) Document.
        Document._yatiml_recognize(node)

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if not node.has_attribute('settings'):
            node.set_attribute('settings', None)
        node.map_attribute_to_index('programs', 'name')
        node.map_attribute_to_index('resources', 'name')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        descr = node.get_attribute('description')
        if descr.is_scalar(str) and '\n' in cast(str, descr.get_value()):
            # output multi-line string in literal mode
            cast(yaml.ScalarNode, descr.yaml_node).style = '|'

        models = node.get_attribute('models')
        if models.is_sequence() and models.is_empty():
            node.remove_attribute('models')

        if node.get_attribute('settings').is_scalar(type(None)):
            node.remove_attribute('settings')
        if len(node.get_attribute('settings').yaml_node.value) == 0:
            node.remove_attribute('settings')

        progs = node.get_attribute('programs')
        if (progs.is_scalar(type(None)) or progs.is_mapping() and progs.is_empty()):
            node.remove_attribute('programs')
        node.index_attribute_to_map('programs', 'name')

        res = node.get_attribute('resources')
        if (
                res.is_scalar(type(None)) or
                res.is_mapping() and res.is_empty()):
            node.remove_attribute('resources')
        node.index_attribute_to_map('resources', 'name')

        cp = node.get_attribute('checkpoints')
        if (
                cp.is_scalar(type(None)) or
                cp.is_mapping() and cp.is_empty()):
            node.remove_attribute('checkpoints')

        resu = node.get_attribute('resume')
        if (
                resu.is_scalar(type(None)) or
                resu.is_mapping() and resu.is_empty()):
            node.remove_attribute('resume')
