from pathlib import Path
from typing import Any, IO, Union
from typing_extensions import Type

from ruamel import yaml
import yatiml

from ymmsl.configuration import Configuration
from ymmsl.document import Document
from ymmsl.settings import Settings
from ymmsl.identity import Identifier, Reference
from ymmsl.model import Component, Conduit, Model, ModelReference


def _loader() -> Type:
    class YmmslLoader(yatiml.Loader):
        pass
    yatiml.add_to_loader(YmmslLoader,
                         [Component, Conduit, Configuration, Document,
                          Identifier, Model, ModelReference, Reference,
                          Settings])
    yatiml.set_document_type(YmmslLoader, Configuration)
    return YmmslLoader


def _dumper() -> Type:
    class YmmslDumper(yatiml.Dumper):
        pass
    yatiml.add_to_dumper(YmmslDumper,
                         [Component, Conduit, Configuration, Document,
                          Identifier, Model, ModelReference, Reference,
                          Settings])
    return YmmslDumper


loader = _loader()
"""A loader class for yMMSL, for use with yaml.load.

Usage:
    config = yaml.load(text, Loader=ymmsl.loader)
"""
dumper = _dumper()
"""A dumper class for yMMSL, for use with yaml.dump.

Usage:
    text = yaml.dump(config, Dumper=ymmsl.dumper)
"""

def load(source: Union[str, Path, IO[Any]]) -> Configuration:
    """Loads a yMMSL document from a string or a file.

    Args:
        source: A string containing yMMSL data, a pathlib Path to a
                file containing yMMSL data, or an open file-like
                object containing from which yMMSL data can be read.

    Returns:
        A Configuration object corresponding to the input data.
    """
    if isinstance(source, Path):
        with source.open('r') as f:
            return yaml.load(f, Loader=loader)
    return yaml.load(source, Loader=loader)


def dump(config: Configuration) -> str:
    """Converts a Ymmsl to a string containing YAML.

    Args:
        config: The configuration to be saved to yMMSL.

    Returns:
        A yMMSL YAML description of the given document.
    """
    return yaml.dump(config, Dumper=dumper)


def save(config: Configuration, target: Union[str, Path, IO[Any]]) -> None:
    """Saves a yMMSL document to a file.

    Args:
        config: The configuration to save to yMMSL.
        target: The file to save to, either as a string containing a
            path, as a pathlib Path object, or as an open file-like
            object.
    """
    if isinstance(target, str):
        with open(target, 'w') as f:    # type: IO[Any]
            f.write(dump(config))
    elif isinstance(target, Path):
        with target.open('w') as f:
            f.write(dump(config))
    else:
        target.write(dump(config))
