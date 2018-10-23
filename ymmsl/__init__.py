"""yMMSL Python bindings"""

__version__ = '0.0.0.dev0'

__author__ = 'Lourens Veen'
__email__ = 'l.veen@esciencecenter.nl'


import yatiml
from typing import Type

from ymmsl.ymmsl import (ComputeElementDecl, Conduit, Experiment, Identifier,
                         Reference, ScaleSettings, Setting, Simulation, Ymmsl)


def _loader() -> Type:
    class YmmslLoader(yatiml.Loader):
        pass
    yatiml.add_to_loader(YmmslLoader, [ComputeElementDecl, Conduit, Experiment,
        Identifier, Reference, ScaleSettings, Setting, Simulation, Ymmsl])
    yatiml.set_document_type(YmmslLoader, Ymmsl)
    return YmmslLoader


def _dumper() -> Type:
    class YmmslDumper(yatiml.Dumper):
        pass
    yatiml.add_to_dumper(YmmslDumper, [ComputeElementDecl, Conduit, Experiment,
        Identifier, Reference, ScaleSettings, Setting, Simulation, Ymmsl])
    return YmmslDumper


loader = _loader()
dumper = _dumper()


__all__ = ['ComputeElementDecl', 'Conduit', 'Experiment', 'Identifier',
           'Reference', 'ScaleSettings', 'Setting', 'Simulation', 'Ymmsl',
           'loader', 'dumper']
