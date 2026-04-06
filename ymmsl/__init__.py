"""Python bindings for yMMSL.

This package contains all the classes needed to represent a yMMSL file,
as well as to read and write yMMSL files.
"""
from ymmsl.conversion.converter import convert_to, DowngradeError
from ymmsl.document import Document
from ymmsl.io import dump, load, load_as, save

# For backwards compatibility of programs
from ymmsl.v0_2 import Operator, Settings


__version__ = '0.15.1-dev'
__author__ = 'Lourens Veen'
__email__ = 'l.veen@esciencecenter.nl'


__all__ = [
        'convert_to', 'Document', 'dump', 'DowngradeError', 'load', 'load_as',
        'Operator', 'save', 'Settings']
