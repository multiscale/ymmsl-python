"""Python bindings for yMMSL.

This package contains all the classes needed to represent a yMMSL file,
as well as to read and write yMMSL files.
"""

from ymmsl.component import Component, Operator, Port, Ports
from ymmsl.configuration import Configuration, PartialConfiguration
from ymmsl.execution import (
        ExecutionModel, Implementation, MPICoresResReq, MPINodesResReq,
        ResourceRequirements, ThreadedResReq)
from ymmsl.settings import Settings, SettingValue
from ymmsl.identity import Identifier, Reference
from ymmsl.io import load, dump, save
from ymmsl.model import Conduit, Model, ModelReference


__version__ = '0.11.1.dev'
__author__ = 'Lourens Veen'
__email__ = 'l.veen@esciencecenter.nl'


__all__ = [
        'Component', 'Conduit', 'Configuration', 'dump', 'ExecutionModel',
        'Identifier', 'Implementation', 'load', 'Model', 'ModelReference',
        'MPICoresResReq', 'MPINodesResReq', 'Operator', 'PartialConfiguration',
        'Port', 'Ports', 'Reference', 'ResourceRequirements', 'save',
        'Settings', 'SettingValue', 'ThreadedResReq']
