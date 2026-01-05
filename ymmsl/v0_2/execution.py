from enum import Enum
from typing import cast

import yatiml

from ymmsl.v0_1.execution import BaseEnv, KeepsStateForNextUse  # noqa: F401


class ExecutionModel(Enum):
    """Describes how to start a model component."""
    DIRECT = 1
    """Start directly on the allocated core(s), without MPI."""
    OPENMPI = 2
    """Start using OpenMPI's mpirun."""
    INTELMPI = 3
    """Start using Intel MPI's mpirun."""
    SRUNMPI = 4
    """Start MPI implementation using srun."""
    MANUAL = 5
    """Let the user start it by hand."""

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.is_scalar(str):
            val = cast(str, node.get_value())
            node.set_value(val.upper())

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        val = node.get_value()
        if isinstance(val, str):
            node.set_value(val.lower())
