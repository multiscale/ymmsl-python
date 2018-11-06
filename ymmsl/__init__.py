"""Python bindings for yMMSL

This package contains all the classes needed to represent a yMMSL file,
as well as to read and write yMMSL files.
"""

__version__ = '0.0.0.dev0'

__author__ = 'Lourens Veen'
__email__ = 'l.veen@esciencecenter.nl'


import yatiml
from typing import Type

from ymmsl.experiment import Setting, Experiment
from ymmsl.identity import Identifier, Reference
from ymmsl.simulation import ComputeElementDecl, Conduit, Simulation
from ymmsl.ymmsl import YmmslDocument


def _loader() -> Type:
    class YmmslLoader(yatiml.Loader):
        pass
    yatiml.add_to_loader(YmmslLoader,
                         [ComputeElementDecl, Conduit, Experiment, Identifier,
                          Reference, Setting, Simulation,
                          YmmslDocument])
    yatiml.set_document_type(YmmslLoader, YmmslDocument)
    return YmmslLoader


def _dumper() -> Type:
    class YmmslDumper(yatiml.Dumper):
        pass
    yatiml.add_to_dumper(YmmslDumper,
                         [ComputeElementDecl, Conduit, Experiment, Identifier,
                          Reference, Setting, Simulation,
                          YmmslDocument])
    return YmmslDumper


loader = _loader()
"""A loader class for yMMSL, for use with yaml.load.

Usage:
    doc = yaml.load(text, Loader=ymmsl.loader)
"""
dumper = _dumper()
"""A dumper class for yMMSL, for use with yaml.dump.

Usage:
    text = yaml.dump(doc, Dumper=ymmsl.dumper)
"""


__all__ = ['ComputeElementDecl', 'Conduit', 'Experiment', 'Identifier',
           'Reference', 'Setting', 'Simulation',
           'YmmslDocument', 'loader', 'dumper']
