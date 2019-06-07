import yatiml
from typing import Type

from ymmsl.compute_element import Operator, Port
from ymmsl.experiment import Setting, Experiment, ParameterValue
from ymmsl.identity import Identifier, Reference
from ymmsl.io import load, dump, save
from ymmsl.simulation import ComputeElementDecl, Conduit, Simulation
from ymmsl.ymmsl import YmmslDocument


"""Python bindings for yMMSL

This package contains all the classes needed to represent a yMMSL file,
as well as to read and write yMMSL files.
"""

__version__ = '0.6.0'
__author__ = 'Lourens Veen'
__email__ = 'l.veen@esciencecenter.nl'


__all__ = ['ComputeElementDecl', 'Conduit', 'dump', 'Experiment', 'Identifier',
           'load', 'Operator', 'ParameterValue', 'Port', 'Reference',
           'Setting', 'Simulation', 'YmmslDocument', 'save']
