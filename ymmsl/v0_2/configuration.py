import collections.abc as abc
from copy import copy
import itertools
import logging
from pathlib import Path
from typing import (
        Dict, List, MutableMapping, Optional, Sequence, Union, cast)

import yatiml
import yaml

from ymmsl.v0_2.checkpoint import Checkpoints
from ymmsl.v0_2.execution import ExecutionModel
from ymmsl.v0_2.resources import MPICoresResReq, MPINodesResReq, ResourceRequirements
from ymmsl.v0_2.identity import Identifier, Reference
from ymmsl.v0_2.implementation import Implementation    # noqa: F401
from ymmsl.v0_2.imports import ImportStatement
from ymmsl.v0_2.settings import Settings, SettingValue
from ymmsl.v0_2.supported_settings import SettingType
from ymmsl.v0_2.document import Document
from ymmsl.v0_2.program import Program
from ymmsl.v0_2.model import Component, Model


_logger = logging.getLogger(__name__)


class Configuration(Document):
    """Top-level class for all information in a yMMSL file.

    Attributes:
        description: A human-readable description of the configuration
        imports: A list of import statements
        models: Model (with submodels) to run. Dictionary mapping model names (as
            References) to Model objects.
        custom_implementations: Non-default implementations for model components that
            fill in or override what those components specify.
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
            imports: Optional[Sequence[ImportStatement]] = None,
            models: Optional[Union[
                Sequence[Model], MutableMapping[Reference, Model]]] = None,
            custom_implementations: Optional[
                MutableMapping[Reference, Reference]] = None,
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
            imports: A list of import statements
            models: Model (possibly with submodels) to run
            custom_implementations: Non-default implementation for model components
            settings: Settings to run the model with.
            programs: Programs to use when running the model
            resources: Resources to allocate for the model components
            checkpoints: When each component should create a snapshot
            resume: What snapshot each component should resume from
        """
        def check_duplicate_impl_names(
                typs: str, impls: abc.Sequence[Implementation]) -> None:
            for i, impl in enumerate(impls):
                for j in range(i):
                    if impls[j].name == impl.name:
                        raise ValueError(
                                f'Found two {typs} that are both named "{impl.name}"')

        self.description = description

        if imports is None:
            self.imports: List[ImportStatement] = list()
        else:
            self.imports = list(imports)

        if models is None:
            self.models: MutableMapping[Reference, Model] = dict()
        elif isinstance(models, abc.Sequence):
            check_duplicate_impl_names('models', models)
            self.models = {copy(model.name): model for model in models}
        elif isinstance(models, Model):
            self.models = {models.name: models}
        else:
            self.models = models

        _CIType = MutableMapping[Reference, Reference]  # noqa: F841

        if custom_implementations is None:
            self.custom_implementations = {}   # type: _CIType
        else:
            self.custom_implementations = custom_implementations

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

        if programs is None:
            self.programs: MutableMapping[Reference, Program] = dict()
        elif isinstance(programs, abc.Sequence):
            check_duplicate_impl_names('programs', programs)
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

    def update(self, overlay: 'Configuration') -> None:
        """Update this configuration with the given overlay.

        This will copy settings from overlay on top of the current settings, and merge
        in the various parts according to their update() functions.

        Args:
            overlay: A configuration to overlay onto this one.
        """
        if not self.description.strip():
            self.description = overlay.description
        elif overlay.description.strip():
            if not self.description.endswith('\n'):
                self.description += '\n'
            self.description += '\n' + overlay.description

        if not self.imports:
            self.imports = overlay.imports
        else:
            if overlay.imports:
                self.imports.extend(overlay.imports)

        if self.models and overlay.models:
            raise RuntimeError(
                    'Multiple ymmsl files containing models specified. Please'
                    ' use the import functionality instead.')

        self.custom_implementations.update(overlay.custom_implementations)

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

    def check_consistent(self, check_runnable: bool = True) -> None:
        """Checks that the configuration is internally consistent.

        This checks:

            - Whether all models are consistent, via Model.check_consistent()
            - That all implementations (programs and models) have a unique name
            - Whether all given component implementations exist
            - Whether all ports on components are consistent with their implementations
            - Whether all custom implementations have a component they apply to
            - Whether all settings are consistent with supported_settings, if specified
            - That resources have been requested for each component that has an
              implementation

        If any of these requirements is false, this function will raise a RuntimeError
        with an explanation of the problem.

        Args:
            check_runnable: if False, skip the checks for whether component
                implementations exist and whether resources have been requested.
        """
        errors = list()

        for model in self.models.values():
            model_errors = model.check_consistent()
            errors.extend([f'In model {model.name}: {e}' for e in model_errors])

        errors.extend(self._check_duplicate_implementations())

        component_paths = self._component_paths()
        if check_runnable:
            errors.extend(self._check_implementations_exist(component_paths))
        errors.extend(self._check_consistent_ports(component_paths))
        errors.extend(self._check_custom_implementations(component_paths))
        errors.extend(self._check_consistent_settings(component_paths))
        if check_runnable:
            errors.extend(self._check_resources(component_paths))

        if errors:
            raise RuntimeError(
                    'The configuration is internally inconsistent. The following'
                    ' problems were found:\n- '
                    + '\n- '.join(errors))

    def root_model(self, selected_model: Optional[Reference] = None) -> Model:
        """Return the root model of this configuration.

        If there are multiple models that are not used as an implementation in any
        component (root models), and selected_model is given and names one of them, then
        that model is returned, otherwise an exception is raised.

        If there is only a single root model, then it is returned, unless selected_model
        is given and does not match, in which case an exception is raised.

        If there are no models, an exception is raised.

        Args:
            selected_model: Name of the model to return, in case of multiple options

        Returns:
            The sole or selected model that is not used as an implementation in any
            component in the configuration.

        Raises:
            RuntimeError if an error occurs, as described above.
        """
        root_models = self._root_models()
        if not root_models:
            raise RuntimeError('No model was found in this configuration.')

        if selected_model:
            match = [m for m in root_models if m.name == selected_model]
            if match:
                return match[0]

            models = '\n- '.join([str(m.name) for m in root_models])
            raise RuntimeError(
                    f'The selected model "{selected_model}" could not be found in this'
                    ' configuration. The following models are present:\n- {models}')

        if len(root_models) == 1:
            return root_models[0]

        models = '\n- '.join([str(m.name) for m in root_models])
        raise RuntimeError(
                'Multiple models were found in this configuration that are not used'
                f' as implementations:\n\n- {models}')

    def _root_models(self) -> List[Model]:
        """Models in this configuration that are not used as implementations."""
        root_models = copy(self.models)

        for model in self.models.values():
            for component in model.components.values():
                if component.implementation:
                    if component.implementation in root_models:
                        del root_models[component.implementation]

        for impl in self.custom_implementations.values():
            if impl in root_models:
                del root_models[impl]

        return list(root_models.values())

    def _component_paths(self) -> Dict[Reference, Component]:
        """Return component paths for components.

        Component paths are of the form component1.component2, where component1 is a
        component inside the top-level model that has an implementation which is a
        submodel, and component2 is a component inside that submodel.

        The returned dict maps all paths in the configuration that map to a component
        with an implementation. Note that there may be multiple paths mapping to the
        same component object, if a submodel is used multiple times.
        """
        result = dict()
        queue = [(m, Reference([])) for m in self._root_models()]

        while queue:
            model, prefix = queue.pop(0)
            for component in model.components.values():
                path = prefix + component.name
                impl = self.custom_implementations.get(path, component.implementation)
                if impl is not None:
                    if impl in self.models:
                        queue.append((self.models[impl], path))
                    result[path] = component

        return result

    def _check_duplicate_implementations(self) -> List[str]:
        """Check that each implementation has a unique name.

        Duplicates within programs and models are already checked in __init__(), so all
        we need to look for here is conflicts between them.

        Returns a list of errors, or an empty list if all is okay.
        """
        errors = list()
        for program_name in self.programs:
            for model_name in self.models:
                if program_name == model_name:
                    errors.append(
                            f'There is a program named "{program_name}" and also a'
                            f' model named "{model_name}", which is not allowed')
        return errors

    def _check_consistent_ports(
            self, component_paths: Dict[Reference, Component]) -> List[str]:
        """Check that components have implementations with compatible ports.

        This checks that each component declares ports that its implementation also
        declares, if it has an implementation and the implementation has a ports
        declaration.

        Returns a list of errors, or an empty list if all is okay.
        """
        errors = list()

        for path, component in component_paths.items():
            impl_ref = self.custom_implementations.get(path, component.implementation)
            if impl_ref is None:
                continue

            if impl_ref in self.programs:
                impl = self.programs[impl_ref]  # type: Implementation
            elif impl_ref in self.models:
                impl = self.models[impl_ref]
            else:
                continue

            if len(impl.ports) > 0:
                for port_name in component.ports:
                    if port_name not in impl.ports:
                        errors.append(
                                f'Component "{component.name}" declares port'
                                f' "{port_name}" that its implementation'
                                f' "{impl.name}" does not have')
                    else:
                        if component.ports[port_name] != impl.ports[port_name]:
                            errors.append(
                                    f'Component "{component.name}" declares port'
                                    f' "{port_name}" that its implementation'
                                    f' "{impl.name}" has, but with a different'
                                    ' operator or timeline.')

        return errors

    def _check_implementations_exist(
            self, component_paths: Dict[Reference, Component]) -> List[str]:
        """Check that all components with an implementation have a valid one.

        Components with implementation None are not considered broken.

        Args:
            component_paths: The output of _component_paths above.

        Returns a list of errors, or an empty list if all is okay.
        """
        errors = list()
        for path, component in component_paths.items():
            impl = self.custom_implementations.get(path, component.implementation)
            if impl is not None:
                if impl not in self.models and impl not in self.programs:
                    errors.append(
                            f'Component "{path}" has implementation "{impl}", but no'
                            ' program or model with that name was given. Did you forget'
                            ' to import it?')
        return errors

    def _check_custom_implementations(
            self, component_paths: Dict[Reference, Component]) -> List[str]:
        """Check that all custom implementations refer to a correct path.

        Args:
            component_paths: The output of _component_paths above.

        Returns a list of errors, or an empty list if all is okay.
        """
        errors = list()
        for path in self.custom_implementations:
            if path not in component_paths:
                errors.append(
                        f'A custom implementation is specified for component "{path}",'
                        ' but no such component is present in the model.')
        return errors

    def _check_consistent_settings(
            self, component_paths: Dict[Reference, Component]) -> List[str]:
        """Check that setting names and types match supported settings.

        This checks that every implementation with a supported_settings declaration will
        find a setting of the given type, if one has been set.

        Args:
            component_paths: The output of _component_paths above.

        Returns a list of errors, or an empty list if all is okay.
        """
        errors = list()

        for path, component in component_paths.items():
            impl_ref = self.custom_implementations.get(path, component.implementation)
            if impl_ref is None:
                continue

            errs = list()
            if impl_ref in self.programs:
                impl = self.programs[impl_ref]   # type: Implementation
            elif impl_ref in self.models:
                impl = self.models[impl_ref]
            else:
                continue

            if impl.supported_settings:
                for name, sup_set in impl.supported_settings:
                    errs.extend(
                            self._check_supported_setting(
                                component, path, name, sup_set.typ, impl))

            if len(errs) > 7:
                errs = errs[:6]
                n = len(errs) - 6
                errs.append(
                        f'Another {n} inconsistent settings were found. Is "{impl}"'
                        ' the correct implementation for component "{component.name}"?')

            errors.extend(errs)

        return errors

    def _check_supported_setting(
            self, component: Component, component_path: Reference, name: Identifier,
            typ: SettingType, impl: Implementation) -> List[str]:
        """Check that the value of the given setting matches the given type.

        This implements the standard setting lookup, then checks any found setting value
        against the given type. Returns a list containing a single error message if
        there's an issue, or an empty list if the type matches.
        """
        errors = list()
        dims = []
        if component.multiplicity:
            dims = component.multiplicity

        for index in itertools.product(*map(range, dims)):
            instance_path = component_path + index
            for j in range(len(instance_path), -1, -1):
                found_setting = instance_path[:j] + name
                if found_setting in self.settings:
                    val = self.settings[found_setting]
                    if not self._setting_type_matches(val, typ):
                        val_str = str(val)
                        if isinstance(val, str):
                            val_str = f'"{val}"'
                        errors.append(
                                f'Instance "{instance_path}" of component'
                                f' "{component_path}" with implementation "{impl.name}"'
                                f' has a supported setting "{name}" with type'
                                f' {typ.value}, but setting "{found_setting}" has value'
                                f' {val_str}, which does not match that type')
                    break

        return errors

    def _setting_type_matches(self, value: SettingValue, typ: SettingType) -> bool:
        """Check that the type of value matches the given type."""
        if isinstance(value, str):
            return typ == SettingType.STR
        elif isinstance(value, bool):
            return typ == SettingType.BOOL
        elif isinstance(value, int):
            return typ == SettingType.INT
        elif isinstance(value, float):
            return typ == SettingType.FLOAT
        elif isinstance(value, list):
            if len(value) == 0:
                return typ in (SettingType.LIST_INT, SettingType.LIST_FLOAT)

            if isinstance(value[0], int):
                return typ == SettingType.LIST_INT
            elif isinstance(value[0], float):
                return typ == SettingType.LIST_FLOAT
            elif isinstance(value[0], list):
                if len(value[0]) == 0 or isinstance(value[0][0], float):
                    return typ == SettingType.LIST_LIST_FLOAT
        return False

    def _check_resources(
            self, component_paths: Dict[Reference, Component]) -> List[str]:
        """Check that each component path has a corresponding resource request.

        Returns a list of errors, empty if all is ok.
        """
        errors = list()
        for path, component in component_paths.items():
            impl_ref = self.custom_implementations.get(path, component.implementation)
            if impl_ref is None or impl_ref not in self.programs:
                continue

            if path not in self.resources:
                errors.append(f'Component "{path}" is missing a resource request')
            else:
                impl = self.programs[impl_ref]
                em_mpi = impl.execution_model in (
                        ExecutionModel.OPENMPI, ExecutionModel.INTELMPI,
                        ExecutionModel.SRUNMPI)

                em_nompi = impl.execution_model is ExecutionModel.DIRECT

                res_mpi = isinstance(
                        self.resources[path], (MPICoresResReq, MPINodesResReq))

                if em_mpi and not res_mpi:
                    errors.append(
                            f'Component "{path}" has implementation "{impl_ref}",'
                            ' which has an MPI execution model, but the resources'
                            ' requested for it do not ask for MPI processes.')
                elif res_mpi and em_nompi:
                    errors.append(
                            f'Component "{path}" has implementation "{impl_ref}",'
                            ' which has a non-MPI execution model, but the resources'
                            ' requested for it ask for MPI processes.')

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
        node.map_attribute_to_index('models', 'name')
        if not node.has_attribute('settings'):
            node.set_attribute('settings', None)
        node.map_attribute_to_index('programs', 'name')
        node.map_attribute_to_index('resources', 'name')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        descr = node.get_attribute('description')
        if descr.is_scalar(str):
            # output in block style
            ynode = cast(yaml.ScalarNode, descr.yaml_node)
            ynode.style = '|'
            if not ynode.value.endswith('\n'):
                ynode.value += '\n'

        imports = node.get_attribute('imports')
        if imports.is_sequence() and imports.is_empty():
            node.remove_attribute('imports')

        models = node.get_attribute('models')
        if (models.is_scalar(type(None)) or models.is_mapping() and models.is_empty()):
            node.remove_attribute('models')
        node.index_attribute_to_map('models', 'name')

        if node.get_attribute('custom_implementations').is_scalar(type(None)):
            node.remove_attribute('custom_implementations')
        if len(node.get_attribute('custom_implementations').yaml_node.value) == 0:
            node.remove_attribute('custom_implementations')

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
