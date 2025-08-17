"""Python bindings for yMMSL.

This package contains all the classes needed to represent a yMMSL file,
as well as to read and write yMMSL files.
"""
from ymmsl.document import Document
from ymmsl.io import dump, load, save

# Below imports are for backwards compatibility only, and deprecated
from ymmsl.v0_1.checkpoint import (
        CheckpointRule, CheckpointRangeRule, CheckpointAtRule, Checkpoints)
from ymmsl.v0_1.component import Component, Operator, Port, Ports
from ymmsl.v0_1.configuration import Configuration, PartialConfiguration
from ymmsl.v0_1.execution import (
        BaseEnv, ExecutionModel, Implementation, MPICoresResReq,
        MPINodesResReq, ResourceRequirements, ThreadedResReq,
        KeepsStateForNextUse)
from ymmsl.v0_1.settings import Settings, SettingValue
from ymmsl.v0_1.identity import Identifier, Reference
from ymmsl.v0_1.model import Conduit, Model, ModelReference

__version__ = '0.14.1-dev'
__author__ = 'Lourens Veen'
__email__ = 'l.veen@esciencecenter.nl'


__all__ = [
        'BaseEnv', 'CheckpointRule', 'CheckpointRangeRule', 'CheckpointAtRule',
        'Checkpoints', 'Component', 'Conduit', 'Configuration', 'Document', 'dump',
        'ExecutionModel', 'Identifier', 'Implementation',
        'KeepsStateForNextUse', 'load', 'Model', 'ModelReference',
        'MPICoresResReq', 'MPINodesResReq', 'Operator', 'PartialConfiguration',
        'Port', 'Ports', 'Reference', 'ResourceRequirements', 'save',
        'Settings', 'SettingValue', 'ThreadedResReq']
