"""Loading and saving functions."""
from pathlib import Path
from typing import Any, IO, Union

import yatiml

from ymmsl.configuration import Configuration
from ymmsl.document import Document
from ymmsl.settings import Settings
from ymmsl.identity import Identifier, Reference
from ymmsl.model import Component, Conduit, Model, ModelReference


_load = yatiml.load_function(
        Configuration, Component, Conduit, Document, Identifier, Model,
        ModelReference, Reference, Settings)


def load(source: Union[str, Path, IO[Any]]) -> Configuration:
    """Loads a yMMSL document from a string or a file.

    Args:
        source: A string containing yMMSL data, a pathlib Path to a
                file containing yMMSL data, or an open file-like
                object containing from which yMMSL data can be read.

    Returns:
        A Configuration object corresponding to the input data.

    """
    # This wrapper is just here to render the documentation.
    return _load(source)


_dump = yatiml.dumps_function(
        Conduit, Configuration, Component, Document, Identifier, Model,
        ModelReference, Reference, Settings)


def dump(config: Configuration) -> str:
    """Converts a Ymmsl to a string containing YAML.

    Args:
        config: The configuration to be saved to yMMSL.

    Returns:
        A yMMSL YAML description of the given document.

    """
    # This wrapper is just here to render the documentation.
    return _dump(config)


_save = yatiml.dump_function(
        Conduit, Configuration, Component, Document, Identifier, Model,
        ModelReference, Reference, Settings)


def save(config: Configuration, target: Union[str, Path, IO[Any]]) -> None:
    """Saves a yMMSL document to a file.

    Args:
        config: The configuration to save to yMMSL.
        target: The file to save to, either as a string containing a
            path, as a pathlib Path object, or as an open file-like
            object.

    """
    # This wrapper is just here to render the documentation.
    _save(config, target)
