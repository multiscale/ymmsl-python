from copy import copy
import logging
import os
import sys
from collections.abc import MutableMapping
from difflib import get_close_matches
from pathlib import Path
from textwrap import indent
from typing import Dict, List, Optional, Set, Tuple, TypeVar, Union

from yatiml import RecognitionError

import ymmsl
from ymmsl.v0_2.configuration import Configuration
from ymmsl.v0_2.identity import Identifier, Reference
from ymmsl.v0_2.implementation import Implementation
from ymmsl.v0_2.imports import ImportKind, ImportStatement
from ymmsl.v0_2.model import Model
from ymmsl.v0_2.program import Program

if sys.version_info < (3, 10):
    from importlib_metadata import EntryPoint, entry_points
else:
    from importlib.metadata import EntryPoint, entry_points

_logger = logging.getLogger(__name__)


ModuleSource = Union[Path, EntryPoint]
"""Source file (Path) or EntryPoint for a yMMSL module"""


class ResolutionContext:
    """Keeps track of where in the resolution process we are.

    An object of this class is used to track the stack of included files, so that we can
    generate descriptive error messages. It also contains a pre-parsed version of the
    ymmsl search path for convenience.
    """
    def __init__(self) -> None:
        """Create a ResolutionContext."""
        if 'YMMSL_PATH' in os.environ:
            self.ymmsl_path = list(map(Path, os.environ['YMMSL_PATH'].split(':')))
        else:
            self.ymmsl_path = list()

        # _modules is a list of (file_path or entry_point, module_name)
        self._modules: List[Tuple[ModuleSource, Reference]] = list()
        self._imports: List[ImportStatement] = list()

    def push_module(self, file: ModuleSource, module: Reference) -> None:
        """Push a file/module onto the stack."""
        self._modules.append((file, module))

    def pop_module(self) -> None:
        """Pop the topmost file/module off of the stack."""
        self._modules.pop()

    def push_import(self, imp_st: ImportStatement) -> None:
        """Push an import statement onto the stack."""
        self._imports.append(imp_st)

    def pop_import(self) -> None:
        """Pop the topmost import statement off of the stack."""
        self._imports.pop()

    def trace(self) -> str:
        """Return a description of the current context."""
        # _imports may be one shorter than _files, or the same length, assuming that
        # push_file and push_import are called alternatingly starting with push_file.

        result: List[str] = list()

        for i, (file_path, _) in enumerate(self._modules):
            if i < len(self._imports):
                imp_mod = self._imports[i].module
                imp_name = self._imports[i].name
                result.append(
                        f'While importing {imp_name} from {imp_mod} in {file_path}:')
            else:
                result.append(f'In {file_path}:')

        return '\n'.join(result) + '\n'

    def search_paths(self, rel_path: Path, indent_depth: int) -> str:
        """Return a description of the search path.

        Returns a multiline string indented by indent_depth spaces.
        """
        return '\n'.join([
                ' ' * indent_depth + f'{p / rel_path}'
                for p in self.ymmsl_path])


def resolve(module: Reference, config: Configuration) -> None:
    """Resolve imports for the given configuration.

    This updates the given configuration in place, removing all import statements and
    adding in the imported objects. Implementation names are updated to their absolute
    names by prefixing them with the given module, so they end up a.b.c.z instead of
    just z.

    Args:
        module: The module corresponding to this configuration
        config: The configuration to resolve

    Raises:
        RuntimeError: if an error occurs due to an invalid configuration. This will
            leave config in a broken state, so reload it if you want to try again.
    """
    overwritten_implementations = do_resolve(
            Path('<main>'), module, config, ResolutionContext())

    used_implementations = {
            c.implementation for m in config.models.values()
            for c in m.components.values()}

    for m in list(config.models.keys()):
        if m in overwritten_implementations and m not in used_implementations:
            del config.models[m]


def do_resolve(
        file: ModuleSource, module: Reference, config: Configuration,
        ctx: ResolutionContext) -> Set[Reference]:
    """Implementation of resolve().

    This is separate so we don't keep parsing YMMSL_PATH over and over again. When we
    gain the ability to import other things they'll be added here, for now it's just
    implementations.

    Args:
        file: The file that config was loaded from
        module: The module corresponding to this configuration
        config: The configuration to resolve
    """
    ctx.push_module(file, module)
    overwritten_implementations = resolve_impls(module, config, ctx)
    ctx.pop_module()
    return overwritten_implementations


def resolve_impls(
        module: Reference, config: Configuration, ctx: ResolutionContext
        ) -> Set[Reference]:
    """Resolve implementations.

    This resolves imports of implementations and then applies any local custom
    implementations.

    Args:
        module: Module this configuration is for
        config: Configuration to resolve implementations for
        ctx: Context for better error messages
    """
    # translation table from old to new implementation name
    ylocals: Dict[Reference, Reference] = dict()
    rename_local_impls(config.programs, module, ylocals)
    rename_local_impls(config.models, module, ylocals)
    resolve_impl_imports(config, ylocals, ctx)
    update_local_implementations(config, ylocals)
    config.imports = [i for i in config.imports if i.kind != ImportKind.IMPLEMENTATION]

    return apply_custom_implementations(config, module, ylocals, ctx)


T = TypeVar('T', bound='Implementation')


def rename_local_impls(
        impls: MutableMapping[Reference, T], module: Reference,
        ylocals: Dict[Reference, Reference]) -> None:
    """Rename local implementations to their full name.

    Update the given dict of implementations, changing names from p, q and r to a.b.c.p,
    a.b.c.q, and a.b.c.r where a.b.c is the name of the current module (ymmsl file).
    Then add p -> a.b.c.p to ylocals for all implementations so we can translate
    references to them later.
    """
    new_impls = dict()
    for name, impl in impls.items():
        impl.name = module + impl.name
        new_impls[impl.name] = impl
        ylocals[name] = impl.name

    impls.clear()
    impls.update(new_impls)


def resolve_impl_imports(
        config: Configuration, ylocals: Dict[Reference, Reference],
        ctx: ResolutionContext) -> None:
    """Resolve any imports of implementations.

    This takes all import statements in config that import implementations, loads the
    corresponding files, and adds the imported implementation and all its dependencies
    to programs and models, using full names that include the module. It adds the
    directly imported implementations to ylocals, mapping their local to full name.
    """
    for imp_st in config.imports:
        ctx.push_import(imp_st)
        if imp_st.kind == ImportKind.IMPLEMENTATION:
            imp_cfg, loaded_file = load_resolve_module(
                    imp_st.module, imp_st.module_path(), ctx)

            ctx.push_module(loaded_file, imp_st.module)

            impls = find_impls(imp_cfg, imp_st.full_name(), ctx)
            for impl in impls:
                if isinstance(impl, Model):
                    config.models[impl.name] = impl
                elif isinstance(impl, Program):
                    config.programs[impl.name] = impl

            if imp_st.name in ylocals:
                msg = ctx.trace()
                msg += f'    Implementation {imp_st.name} is both defined and'
                msg += ' imported. Please remove\n'
                msg += '    or rename one of the definitions to avoid ambiguity.'
                raise RuntimeError(msg)

            ylocals[Reference([imp_st.name])] = imp_st.full_name()
            ctx.pop_module()

        ctx.pop_import()


def update_local_implementations(
        config: Configuration, ylocals: Dict[Reference, Reference]) -> None:
    """Updates names of local implementations to their full names."""
    for model in config.models.values():
        for cmp in model.components.values():
            if cmp.implementation:
                if cmp.implementation in ylocals:
                    cmp.implementation = ylocals[cmp.implementation]


def apply_custom_implementations(
        config: Configuration, module: Reference, ylocals: Dict[Reference, Reference],
        ctx: ResolutionContext) -> Set[Reference]:
    """Applies custom implementations and removes them.

    Custom implementations are keyed by the model plus full component path, and map to
    a local implementation name.

    After this, the configuration will not have any entries in custom_implementations.

    Args:
        config: The configuration to modify
        module: Name of the module it is in
        ylocals: Map from local to global names
    """
    def impl_hint_msg(
            unknown: Reference, known_impls: Optional[List[str]] = None) -> str:
        if known_impls is None:
            known_impls = [str(k) for k in ylocals.keys()]
        matches = get_close_matches(str(unknown), known_impls)
        if len(matches) == 1:
            msg = f'Did you mean {matches[0]}?\n'
        elif len(matches) > 1:
            msg = 'Did you mean any of these?\n'
            msg += indent('- ' + '\n- '.join(matches), 8 * ' ')
        else:
            msg = 'Possible values are:\n'
            msg += indent('- ' + '\n- '.join(known_impls), 8 * ' ')
        return msg

    overwritten_implementations = set()
    copied_paths = set()

    for key, value in config.custom_implementations.items():
        base_model_name = Reference([key[0]])
        if ylocals.get(base_model_name) not in config.models:
            raise RuntimeError(
                    ctx.trace() +
                    f'    Unknown model "{base_model_name}" in custom_implementations'
                    f' "{key}: {value}". {impl_hint_msg(base_model_name)}')

        if value is not None and value not in ylocals:
            raise RuntimeError(
                    ctx.trace() +
                    f'    Unknown implementation "{value}" in custom_implementations'
                    f' "{key}: {value}". {impl_hint_msg(value)}')

        path = key[1:]
        new_impl = ylocals[value] if value is not None else None

        # Before modifying it, we copy the model from its original a.b.c.Model to
        # <module>.Model so that the changes don't affect other uses of it, or the
        # cached version.
        orig_name = ylocals[base_model_name]
        orig_model = config.models[orig_name]
        new_name = module + base_model_name
        if orig_name != new_name:
            m = copy(orig_model)
            m.components = copy(m.components)
            m.name = new_name

            config.models[new_name] = m
            ylocals[base_model_name] = m.name
            overwritten_implementations.add(orig_name)
        else:
            m = orig_model

        # Now we can walk down the components and copy-and-rename the models along the
        # path, again to avoid making unintended changes elsewhere
        for i, c in enumerate(path[:-1]):
            if not isinstance(c, Identifier):
                raise RuntimeError(
                        ctx.trace() +
                        f'    Invalid path in custom_implementations "{key}". Only'
                        ' component names are allowed here.')
            component = Reference([c])
            if component not in m.components:
                raise RuntimeError(
                        ctx.trace() +
                        f'    In custom_implementations {key}: {value}:'
                        f' {base_model_name + path[:i]} is implemented by {m.name},'
                        f' which does not have a component named {str(component)}.')

            orig_impl = m.components[component].implementation
            if orig_impl is None or orig_impl not in config.models:
                raise RuntimeError(
                        ctx.trace() +
                        f'    In custom_implementations "{key}: {value}":'
                        f' {base_model_name + path[:i+1]} has implementation'
                        f' {orig_impl}, which does not have a component named'
                        f' {path[i+1]} in it.')

            if (base_model_name + path[:i+1]) not in copied_paths:
                new_name = module + Identifier((
                        str(orig_impl) + '__customised_for__' +
                        str(ylocals[base_model_name] + path[:i+1])
                        ).replace('.', '_'))
                new_submodel = copy(config.models[orig_impl])
                new_submodel.components = copy(new_submodel.components)
                new_submodel.name = new_name
                config.models[new_name] = new_submodel
                m.components[component] = copy(m.components[component])
                m.components[component].implementation = new_name
                overwritten_implementations.add(orig_impl)
                m = new_submodel
                copied_paths.add(base_model_name + path[:i+1])
            else:
                m = config.models[orig_impl]

        if not isinstance(path[-1], Identifier):
            raise RuntimeError(
                    ctx.trace() +
                    f'    In custom_implementations "{key}: {value}":'
                    f' [i] instance selectors are invalid in custom_implementations.')

        if path[-1] not in m.components:
            raise RuntimeError(
                    ctx.trace() +
                    f'    In custom_implementations "{key}: {value}":'
                    f' {base_model_name + path[:-1]} is implemented by {m.name}, which'
                    f' does not have a component named {path[-1]}. ' +
                    impl_hint_msg(
                        Reference([path[-1]]), [str(k) for k in m.components.keys()])
                    )

        component = Reference([path[-1]])
        new_component = copy(m.components[component])
        if new_component.implementation is not None:
            if new_component.implementation in config.models:
                overwritten_implementations.add(new_component.implementation)
        new_component.implementation = new_impl
        m.components[component] = new_component

    config.custom_implementations.clear()
    return overwritten_implementations


def find_impls(
        config: Configuration, name: Reference, ctx: ResolutionContext
        ) -> List[Implementation]:
    """Find and return an implementation and its dependencies.

    This searches config for the implementation with the given name, and returns it and
    all its dependencies in config.
    """
    impls = [find_impl(config, name, ctx)]

    result = list()
    while impls:
        impl = impls.pop(0)
        if isinstance(impl, Model):
            for cmp in impl.components.values():
                if cmp.implementation:
                    impls.append(find_impl(config, cmp.implementation, ctx))

        result.append(impl)

    return result


def find_impl(
        config: Configuration, name: Reference, ctx: ResolutionContext
        ) -> Implementation:
    """Find a model or program in a configuration."""
    if name in config.programs:
        return config.programs[name]
    elif name in config.models:
        return config.models[name]
    else:
        impls = [
                str(k[-1])
                for k in list(config.models.keys()) + list(config.programs.keys())]
        matches = get_close_matches(str(name[-1]), impls)
        msg = ctx.trace()
        msg += f'    Implementation {name[-1]} not found.'
        if matches:
            if len(matches) == 1:
                msg += f' Did you mean {matches[0]}?\n'
            else:
                msg += ' Did you mean any of these?\n'
                msg += indent('- ' + '\n- '.join(matches), 8 * ' ')

        raise RuntimeError(msg)


ymmsl_cache: Dict[Path, Tuple[Configuration, ModuleSource]] = dict()


def _load_from_entrypoints(
        module: Reference) -> Optional[Tuple[Configuration, EntryPoint]]:
    # Find entry point
    entrypoints = entry_points(group="ymmsl.module", name=str(module))
    if not entrypoints:
        return None
    if len(entrypoints) > 1:
        _logger.warning(
            "Multiple entry points found for yMMSL import module '%s'. "
            "Taking the first of %s",
            module,
            ", ".join(
                f"'{ep.value}' (from {ep.dist.name if ep.dist else '<unknown>'})"
                for ep in entrypoints
            )
        )
    entrypoint = next(iter(entrypoints))

    # Load entry point
    try:
        ymmsl_txt = entrypoint.load()
    except Exception as exc:
        raise RuntimeError(
            f"Error while loading the entrypoint '{entrypoint.value}' "
            f"(from {entrypoint.dist.name if entrypoint.dist else '<unknown>'})"
        ) from exc
    if not isinstance(ymmsl_txt, str):
        raise TypeError(f"Entrypoint {entrypoint.value} is not a string")

    config = ymmsl.load_as(Configuration, ymmsl_txt)
    return config, entrypoint


def _load_from_ymmsl_path(
        module_path: Path, ymmsl_path: list[Path]
        ) -> Optional[Tuple[Configuration, Path]]:
    for yp in ymmsl_path:
        try:
            loaded_file = yp / module_path
            config = ymmsl.load_as(Configuration, loaded_file)
            return config, loaded_file
        except FileNotFoundError:
            pass
    return None


def load_resolve_module(
        module: Reference, module_path: Path, ctx: ResolutionContext
        ) -> Tuple[Configuration, ModuleSource]:
    """Load and resolve an imported ymmsl file.

    Caches the result, without functools.lru_cache because ctx shouldn't hash.

    Returns:
        The loaded configuration and the path it was loaded from.

    Raises:
        RuntimeError if there was an error in the file or it could not be found
    """
    if module_path not in ymmsl_cache:
        # TODO: relative to working directory?
        try:
            config_and_loaded_file = (
                _load_from_entrypoints(module)
                or _load_from_ymmsl_path(module_path, ctx.ymmsl_path)
            )
            if config_and_loaded_file is None:
                msg = ctx.trace()
                msg += f'    Failed to find a file {module_path} for module {module}.\n'
                msg += '    Based on the YMMSL_PATH environment variable and Python'
                msg += ' entry points. I\'ve searched at:\n'
                msg += ctx.search_paths(module_path, 8)
                msg += '\n    and in entry points:\n'
                msg += '\n'.join(
                    8*' ' + ep.name for ep in entry_points(group="ymmsl.module"))
                raise RuntimeError(msg)

            config, loaded_file = config_and_loaded_file
            do_resolve(loaded_file, module, config, ctx)
            ymmsl_cache[module_path] = config, loaded_file

        except RecognitionError as e:
            msg = ctx.trace()
            msg += indent(str(e), ' ' * 4)
            raise RuntimeError(msg)

    return ymmsl_cache[module_path]
