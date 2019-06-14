import yatiml
from typing import Type

from ymmsl.compute_element import Operator, Port
from ymmsl.settings import Settings, ParameterValue
from ymmsl.identity import Identifier, Reference
from ymmsl.io import load, dump, save
from ymmsl.model import ComputeElement, Conduit, Model, ModelReference
from ymmsl.ymmsl import YmmslDocument


"""Python bindings for yMMSL

This package contains all the classes needed to represent a yMMSL file,
as well as to read and write yMMSL files.
"""

__version__ = '0.7.0'
__author__ = 'Lourens Veen'
__email__ = 'l.veen@esciencecenter.nl'


__all__ = ['ComputeElement', 'Conduit', 'dump', 'Identifier', 'load', 'Model',
           'ModelReference', 'Operator', 'ParameterValue', 'Port', 'Reference',
           'Settings', 'YmmslDocument', 'save']
