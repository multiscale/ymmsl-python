"""This module contains all the definitions for yMMSL."""
from typing import Optional

import yatiml

from ymmsl.experiment import Experiment
from ymmsl.simulation import Simulation


class YmmslDocument:
    """A yMMSL document.

    This is the top-level class for yMMSL data.

    Attributes:
        experiment: An experiment to run.
    """

    def __init__(self,
                 version: str,
                 experiment: Optional[Experiment] = None,
                 simulation: Optional[Simulation] = None
                 ) -> None:
        self.version = version
        self.experiment = experiment
        self.simulation = simulation

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute('experiment').is_scalar(type(None)):
            node.remove_attribute('experiment')
        if node.get_attribute('simulation').is_scalar(type(None)):
            node.remove_attribute('simulation')
