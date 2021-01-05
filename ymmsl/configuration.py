"""This module contains all the definitions for yMMSL."""
from collections import OrderedDict
from typing import Dict, List, Optional, Union

import yatiml

from ymmsl.document import Document
from ymmsl.identity import Reference
from ymmsl.execution import Implementation, Resources
from ymmsl.settings import Settings
from ymmsl.model import Model, ModelReference


# This should be a local definition, but that triggers a mypy issue:
# https://github.com/python/mypy/issues/7281
_ImplType = Dict[Reference, Implementation]


class PartialConfiguration(Document):
    """Top-level class for all information in a yMMSL file.

    Attributes:
        model: A model to run.
        settings: Settings to run the model with.
        implementations: Implementations to use to run the model.
            Dictionary mapping implementation names (as References) to
            Implementation objects.
        resources: Resources to allocate for the model components.
            Dictionary mapping component names to Resources objects.
    """
    def __init__(self,
                 model: Optional[ModelReference] = None,
                 settings: Optional[Settings] = None,
                 implementations: Optional[Union[
                     List[Implementation],
                     Dict[Reference, Implementation]]] = None,
                 resources: Optional[Union[
                     List[Resources],
                     Dict[Reference, Resources]]] = None
                 ) -> None:
        """Create a Configuration.

        Implementations and resources may be either a list of such
        objects, or a dictionary matching the attribute format (see
        above).

        Args:
            model: A description of the model to run.
            settings: Settings to run the model with.
            implementations: Implementations to choose from.
            resources: Resources to allocate for the model components.

        """
        self.model = model

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

        if implementations is None:
            self.implementations = dict()   # type: _ImplType
        elif isinstance(implementations, list):
            self.implementations = OrderedDict([
                (impl.name, impl) for impl in implementations])
        else:
            self.implementations = implementations

        if resources is None:
            self.resources = dict()     # type: Dict[Reference, Resources]
        elif isinstance(resources, list):
            self.resources = OrderedDict([
                (res.name, res) for res in resources])
        else:
            self.resources = resources

    def update(self, overlay: 'PartialConfiguration') -> None:
        """Update this configuration with the given overlay.

        This will update the model according to :meth:`Model.update`,
        copy settings from overlay on top of the current settings,
        overwrite implementations with the same name and add
        implementations with a new name, and likewise for resources.

        Args:
            overlay: A configuration to overlay onto this one.
        """
        if self.model is None or not isinstance(self.model, Model):
            self.model = overlay.model
        elif not isinstance(overlay.model, Model):
            # Hmm. Let's do it like this for now.
            # None is taken care of above, but mypy doesn't get that.
            self.model.name = overlay.model.name    # type: ignore
        else:
            self.model.update(overlay.model)

        self.settings.update(overlay.settings)

        for newi_name, newi in overlay.implementations.items():
            self.implementations[newi_name] = newi

        for newr_name, newr in overlay.resources.items():
            self.resources[newr_name] = newr

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # Because of the syntactic sugar below, the YAML doesn't match
        # the types declared above. So we override recognition, and
        # since the attributes are all optional, we have nothing to
        # check except that it's a valid Document (with a version tag).
        Document._yatiml_recognize(node)

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if not node.has_attribute('settings'):
            node.set_attribute('settings', None)
        node.map_attribute_to_index('implementations', 'name', 'script')
        node.map_attribute_to_index('resources', 'name', 'num_cores')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute('model').is_scalar(type(None)):
            node.remove_attribute('model')

        if node.get_attribute('settings').is_scalar(type(None)):
            node.remove_attribute('settings')
        if len(node.get_attribute('settings').yaml_node.value) == 0:
            node.remove_attribute('settings')

        impl = node.get_attribute('implementations')
        if (
                impl.is_scalar(type(None)) or
                impl.is_mapping() and impl.is_empty()):
            node.remove_attribute('implementations')
        node.index_attribute_to_map('implementations', 'name', 'script')

        res = node.get_attribute('resources')
        if (
                res.is_scalar(type(None)) or
                res.is_mapping() and res.is_empty()):
            node.remove_attribute('resources')
        node.index_attribute_to_map('resources', 'name', 'num_cores')


class Configuration(PartialConfiguration):
    """Configuration that includes all information for a simulation.

    Configuration has some optional attributes, because we want to
    allow configuration files which only contain some of the
    information needed to run a simulation. At some point however,
    you need all the bits, and this class requires them.

    When loading a yMMSL file, you will automatically get an object
    of this class if all the required components are there; if the
    file is incomplete, you'll get a Configuration instead.

    Attributes:
        model: A model to run.
        settings: Settings to run the model with.
        implementations: Implementations to use to run the model.
            Dictionary mapping implementation names (as References) to
            Implementation objects.
        resources: Resources to allocate for the model components.
            Dictionary mapping component names to Resources objects.
    """
    def __init__(self,
                 model: Model,
                 settings: Optional[Settings] = None,
                 implementations: Union[
                     List[Implementation],
                     Dict[Reference, Implementation]] = [],
                 resources: Union[
                     List[Resources],
                     Dict[Reference, Resources]] = []
                 ) -> None:
        """Create a Configuration.

        Implementations and resources may be either a list of such
        objects, or a dictionary matching the attribute format (see
        above).

        Args:
            model: A description of the model to run.
            settings: Settings to run the model with.
            implementations: Implementations to choose from.
            resources: Resources to allocate for the model components.

        """
        # mypy doesn't get it when we call super().__init__ here, so
        # it's duplicated.
        self.model = model  # type: Model

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

        if implementations is None:
            self.implementations = dict()   # type: _ImplType
        elif isinstance(implementations, list):
            self.implementations = OrderedDict([
                (impl.name, impl) for impl in implementations])
        else:
            self.implementations = implementations

        if resources is None:
            self.resources = dict()     # type: Dict[Reference, Resources]
        elif isinstance(resources, list):
            self.resources = OrderedDict([
                (res.name, res) for res in resources])
        else:
            self.resources = resources

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_attribute('model', Model)
        node.require_attribute('implementations')
        node.require_attribute('resources')
