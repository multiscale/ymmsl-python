"""Loading and saving functions."""
from pathlib import Path
from typing import Any, IO, Union

import yatiml

import ymmsl.v0_1 as v0_1
from ymmsl.v0_1.document import Document as v0_1_Document
from ymmsl.v0_1.model import MulticastConduit as v0_1_MulticastConduit


_classes = (
        v0_1.PartialConfiguration, v0_1.BaseEnv, v0_1.CheckpointRangeRule,
        v0_1.CheckpointAtRule, v0_1.CheckpointRule, v0_1.Checkpoints, v0_1.Component,
        v0_1.Conduit, v0_1.Configuration, v0_1_Document, v0_1.ExecutionModel,
        v0_1.Identifier, v0_1.Implementation, v0_1.KeepsStateForNextUse, v0_1.Model,
        v0_1.ModelReference, v0_1.MPICoresResReq, v0_1.MPINodesResReq, v0_1.Ports,
        v0_1.Reference, v0_1.ResourceRequirements, v0_1.Settings, v0_1.ThreadedResReq,
        v0_1_MulticastConduit)


_load = yatiml.load_function(*_classes)


def load(source: Union[str, Path, IO[Any]]) -> v0_1.PartialConfiguration:
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


_dump = yatiml.dumps_function(*_classes)


def dump(config: v0_1.PartialConfiguration) -> str:
    """Converts a yMMSL configuration to a string containing YAML.

    Args:
        config: The configuration to be saved to yMMSL.

    Returns:
        A yMMSL YAML description of the given document.

    """
    # This wrapper is just here to render the documentation.
    return _dump(config)


_save = yatiml.dump_function(*_classes)


def save(
        config: v0_1.PartialConfiguration, target: Union[str, Path, IO[Any]]
        ) -> None:
    """Saves a yMMSL configuration to a file.

    Args:
        config: The configuration to save to yMMSL.
        target: The file to save to, either as a string containing a
            path, as a pathlib Path object, or as an open file-like
            object.

    """
    # This wrapper is just here to render the documentation.
    _save(config, target)
