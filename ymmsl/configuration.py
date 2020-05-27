"""This module contains all the definitions for yMMSL."""
from typing import Optional

from ruamel import yaml
import yatiml

from ymmsl.document import Document
from ymmsl.settings import Settings
from ymmsl.model import ModelReference


class Configuration(Document):
    """Top-level class for all information in a yMMSL file.

    Args:
        model: A description of the model to run.
        settings: Settings to run the model with.

    Attributes:
        model: A model to run.
        settings: Settings to run the model with.
    """

    def __init__(self,
                 model: Optional[ModelReference] = None,
                 settings: Optional[Settings] = None
                 ) -> None:
        self.model = model

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if not node.has_attribute('settings'):
            node.set_attribute('settings', None)

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute('settings').is_scalar(type(None)):
            node.remove_attribute('settings')
        if len(node.get_attribute('settings').yaml_node.value) == 0:
            node.remove_attribute('settings')
        if node.get_attribute('model').is_scalar(type(None)):
            node.remove_attribute('model')
