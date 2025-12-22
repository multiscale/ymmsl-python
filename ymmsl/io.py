"""Loading and saving functions."""
from pathlib import Path
from typing import Any, IO, Type, TypeVar, Union

import yatiml

from ymmsl.conversion.converter import convert_to
from ymmsl.document import Document

import ymmsl.v0_1 as v0_1
from ymmsl.v0_1.document import Document as v0_1_Document
from ymmsl.v0_1.model import MulticastConduit as v0_1_MulticastConduit

import ymmsl.v0_2 as v0_2


_classes = (
        Document,
        v0_1.BaseEnv, v0_1.CheckpointRangeRule, v0_1.CheckpointAtRule,
        v0_1.CheckpointRule, v0_1.Checkpoints, v0_1.Component, v0_1.Conduit,
        v0_1.Configuration, v0_1_Document, v0_1.ExecutionModel, v0_1.Identifier,
        v0_1.Implementation, v0_1.KeepsStateForNextUse, v0_1.Model, v0_1.ModelReference,
        v0_1.MPICoresResReq, v0_1.MPINodesResReq, v0_1.PartialConfiguration, v0_1.Ports,
        v0_1.Reference, v0_1.ResourceRequirements, v0_1.Settings, v0_1.ThreadedResReq,
        v0_1_MulticastConduit,
        v0_2.BaseEnv, v0_2.CheckpointRangeRule, v0_2.CheckpointAtRule,
        v0_2.CheckpointRule, v0_2.Checkpoints, v0_2.Component, v0_2.Configuration,
        v0_2.Document, v0_1.ExecutionModel, v0_2.Identifier, v0_2.ImportKind,
        v0_2.ImportStatement, v0_2.KeepsStateForNextUse, v0_2.Model,
        v0_2.MPICoresResReq, v0_2.MPINodesResReq, v0_2.Ports, v0_2.Program,
        v0_2.Reference, v0_2.ResourceRequirements, v0_2.Settings, v0_2.ThreadedResReq)


_load = yatiml.load_function(*_classes)


def load(source: Union[str, Path, IO[Any]]) -> Document:
    """Loads a yMMSL document from a string or a file.

    Args:
        source: A string containing yMMSL data, a pathlib Path to a
                file containing yMMSL data, or an open file-like
                object containing from which yMMSL data can be read.

    Returns:
        A PartialConfiguration object corresponding to the input data.

    """
    # This wrapper is just here to render the documentation.
    return _load(source)


T = TypeVar('T', bound=Document)


def load_as(as_type: Type[T], source: Union[str, Path, IO[Any]]) -> T:
    """Loads and converts a yMMSL document from a string or a file.

    If the file is of a version older than the specified version, then it will be
    converted automatically. If it is of a newer version, then an exception will be
    raised.

    Currently supported values for `as_type` are `ymmsl.v0_1.PartialConfiguration`,
    and `ymmsl.v0_2.Configuration`. Only the final one makes sense at the moment, as
    there's no point in converting from v0.1 to v0.1.

    Args:
        as_type: Configuration class to return, as above
        source: A string containing yMMSL data, a pathlib Path to a
                file containing yMMSL data, or an open file-like
                object containing from which yMMSL data can be read.

    Returns:
        A configuration object corresponding to the input data and the requested
        version.

    Raises:
        DowngradeError: If the requested version is older than the version of the input.

    """
    return convert_to(as_type, _load(source))


_dump = yatiml.dumps_function(*_classes)


def dump(config: Document) -> str:
    """Converts a yMMSL configuration to a string containing YAML.

    The argument should be either a v0_1.PartialConfiguration, a v0_1.Configuration, or
    a v0_2.Configuration.

    Args:
        config: The configuration to be saved to yMMSL.

    Returns:
        A yMMSL YAML description of the given document.

    """
    # This wrapper is just here to render the documentation.
    return _dump(config)


_save = yatiml.dump_function(*_classes)


def save(
        config: Document, target: Union[str, Path, IO[Any]]
        ) -> None:
    """Saves a yMMSL configuration to a file.

    The `config` argument should be either a v0_1.PartialConfiguration, a
    v0_1.Configuration, or a v0_2.Configuration.

    Args:
        config: The configuration to save to yMMSL.
        target: The file to save to, either as a string containing a
            path, as a pathlib Path object, or as an open file-like
            object.

    """
    # This wrapper is just here to render the documentation.
    _save(config, target)
