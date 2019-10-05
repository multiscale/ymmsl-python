"""This module contains all the definitions for yMMSL."""
from typing import Optional

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
        self.settings = settings

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute('settings').is_scalar(type(None)):
            node.remove_attribute('settings')
        if node.get_attribute('model').is_scalar(type(None)):
            node.remove_attribute('model')
