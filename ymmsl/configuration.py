"""This module contains all the definitions for yMMSL."""
from typing import List, Optional

import yatiml

from ymmsl.document import Document
from ymmsl.execution import Implementation, Resources
from ymmsl.settings import Settings
from ymmsl.model import Model, ModelReference


class Configuration(Document):
    """Top-level class for all information in a yMMSL file.

    Attributes:
        model: A model to run.
        settings: Settings to run the model with.
        implementations: Implementations to use to run the model.
        resources: Resources to allocate for the model components.

    """

    def __init__(self,
                 model: Optional[ModelReference] = None,
                 settings: Optional[Settings] = None,
                 implementations: Optional[List[Implementation]] = None,
                 resources: Optional[List[Resources]] = None
                 ) -> None:
        """Create a Configuration.

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
            self.implementations = list()   # type: List[Implementation]
        else:
            self.implementations = implementations

        if resources is None:
            self.resources = list()     # type: List[Resources]
        else:
            self.resources = resources

    def update(self, overlay: 'Configuration') -> None:
        """Update this configuration with the given overlay.

        This will update the model according to :meth:`Model.update`,
        copy settings from overlay on top of the current settings,
        overwrite implementations with the same name and add
        implementations with a new name, and likewise for resources.

        Args:
            overlay: A Configuration to overlay onto this one.
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

        for newi in overlay.implementations:
            for i, oldi in enumerate(self.implementations):
                if newi.name == oldi.name:
                    self.implementations[i] = newi
                    break
            else:
                self.implementations.append(newi)

        for newr in overlay.resources:
            for i, oldr in enumerate(self.resources):
                if newr.name == oldr.name:
                    self.resources[i] = newr
                    break
            else:
                self.resources.append(newr)

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if not node.has_attribute('settings'):
            node.set_attribute('settings', None)
        node.map_attribute_to_seq('implementations', 'name', 'script')
        node.map_attribute_to_seq('resources', 'name', 'num_cores')

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
                impl.is_sequence() and len(impl.seq_items()) == 0):
            node.remove_attribute('implementations')
        node.seq_attribute_to_map('implementations', 'name', 'script')

        res = node.get_attribute('resources')
        if (
                res.is_scalar(type(None)) or
                res.is_sequence() and len(res.seq_items()) == 0):
            node.remove_attribute('resources')
        node.seq_attribute_to_map('resources', 'name', 'num_cores')
