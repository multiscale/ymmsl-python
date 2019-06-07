from pathlib import Path
from typing import Any, IO, Type, Union

from ruamel import yaml
import yatiml

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

def load(source: Union[str, Path, IO[Any]]) -> YmmslDocument:
    """Loads a yMMSL document from a string or a file.

    Args:
        source: A string containing yMMSL data, a pathlib Path to a
                file containing yMMSL data, or an open file-like
                object containing from which yMMSL data can be read.

    Returns:
        A YmmslDocument object corresponding to the input data.
    """
    if isinstance(source, Path):
        with source.open('r') as f:
            return yaml.load(f, Loader=loader)
    return yaml.load(source, Loader=loader)


def dump(ymmsl: YmmslDocument) -> str:
    """Converts a Ymmsl to a string containing YAML.

    Args:
        ymmsl: The document to be saved.

    Returns:
        A yMMSL YAML description of the given document.
    """
    return yaml.dump(ymmsl, Dumper=dumper)


def save(ymmsl: YmmslDocument, target: Union[str, Path, IO[Any]]) -> None:
    """Saves a yMMSL document to a file.

    Args:
        ymmsl: The yMMSL document to save.
        target: The file to save to, either as a string containing a
            path, as a pathlib Path object, or as an open file-like
            object.
    """
    if isinstance(target, str):
        with open(target, 'w') as f:    # type: IO[Any]
            f.write(dump(ymmsl))
    elif isinstance(target, Path):
        with target.open('w') as f:
            f.write(dump(ymmsl))
    else:
        target.write(dump(ymmsl))
