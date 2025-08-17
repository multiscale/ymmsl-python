from collections import OrderedDict
import collections.abc as abc
import logging
from pathlib import Path
from typing import (
        Dict, MutableMapping, Optional, Sequence, Union, cast)

import yatiml
import yaml

from ymmsl.v0_2.document import Document
from ymmsl.v0_2 import (
        Checkpoints, Reference, ResourceRequirements, Settings)


_logger = logging.getLogger(__name__)


_ResType = MutableMapping[Reference, ResourceRequirements]


class Configuration(Document):
    """Top-level class for all information in a yMMSL file.

    Attributes:
        description: A human-readable description of the configuration
        settings: Settings to run the model with
        resources: Resources to allocate for the model components.
            Dictionary mapping component names to ResourceRequirements objects.
        checkpoints: Defines when each model component should create a snapshot
        resume: Defines what snapshot each model component should resume from
    """
    def __init__(
            self, description: str, settings: Optional[Settings] = None,
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

        # TODO: models

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

        # TODO: programs

        # TODO: installations

        if resources is None:
            self.resources = dict()     # type: _ResType
        elif isinstance(resources, abc.Sequence):
            self.resources = OrderedDict([
                (res.name, res) for res in resources])
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
        if not self.description:
            self.description = overlay.description
        elif overlay.description:
            self.description += '\n\n' + overlay.description

        self.settings.update(overlay.settings)

        self.resources.update(overlay.resources)

        self.checkpoints.update(overlay.checkpoints)
        self.resume.update(overlay.resume)

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
        node.map_attribute_to_index('resources', 'name')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        descr = node.get_attribute('description')
        if descr.is_scalar(str) and '\n' in cast(str, descr.get_value()):
            # output multi-line string in literal mode
            cast(yaml.ScalarNode, descr.yaml_node).style = '|'

        if node.get_attribute('settings').is_scalar(type(None)):
            node.remove_attribute('settings')
        if len(node.get_attribute('settings').yaml_node.value) == 0:
            node.remove_attribute('settings')

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

    def check_consistent(self) -> None:
        """Checks that the configuration is internally consistent.

        This checks whether all conduits are connected to existing
        components, that there's an implementation for every component,
        and that resources have been requested for each component.

        If any of these requirements is false, this function will
        raise a RuntimeError with an explanation of the problem.

        """
        # TODO
