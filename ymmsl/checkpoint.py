"""Definitions for describing checkpoints."""

from typing import List, Optional, Union

import yatiml


class CheckpointRange:
    """Defines a range of checkpoint moments.

    Equivalent an "at" rule ``[start, start + step, start + 2*step, ...]`` for
    as long as ``start + i*step <= stop``.

    Stop may be omitted, in which case the range is infinite.

    Start may be omitted, in which case the range is equivalent to an "at" rule
    ``[..., -n*step, ..., -step, 0, step, 2*step, ...]`` for as long as
    ``i*step <= stop``.

    Attributes:
        start: start of the range (or None if omitted)
        stop: stopping criterium of the range (or None if omitted)
        step: step size
    """

    def __init__(self,
                 step: Union[float, int],
                 start: Optional[Union[float, int]] = None,
                 stop: Optional[Union[float, int]] = None) -> None:
        """Create a checkpoint range.

        Args:
            step: step size, must be larger than 0.
            start: start of the range. Defaults to None.
            stop: stop criterium of the range. Defaults to None.
        """
        if step <= 0:
            raise ValueError(f"Invalid step {step} in checkpoint range:"
                             " must be larger than 0")
        if start is not None and stop is not None and start > stop:
            raise ValueError(f"Invalid start {start} and stop {stop} in"
                             "checkpoint range: stop cannot be smaller than"
                             " start")
        self.start = start
        self.stop = stop
        self.step = step

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute("start").is_scalar(type(None)):
            node.remove_attribute("start")

        if node.get_attribute("stop").is_scalar(type(None)):
            node.remove_attribute("stop")


class CheckpointRules:
    """Defines a combination of checkpoint rules.

    Different types of checkpoint rules exist. Every creates a snapshot every
    specified interval: ``[0, every, 2*every, 3*every, ...]``. At creates a
    snapshot at the specified moments. Ranges specify checkpoint ranges, see
    :class:`CheckpointRanges` for further details.

    Note: every is equivalent to a range with start=None, stop=None and
    step=every. It also supports negative simulation times.

    Attributes:
        every: interval for every rule (or None if not defined)
        at: list of checkpoints
        range: list of checkpoint ranges
    """

    def __init__(self,
                 every: Optional[Union[float, int]] = None,
                 at: Optional[List[Union[float, int]]] = None,
                 ranges: Optional[List[CheckpointRange]] = None) -> None:
        """Create checkpoint rules.

        Args:
            every: interval for every rule. Defaults to None.
            at: list of checkpoints. Defaults to None.
            ranges: list of checkpoint ranges. Defaults to None.
        """
        if every is not None and ranges is not None:
            raise RuntimeError("Cannot combine 'every' and 'ranges' rules")
        if at is None:
            at = []
        if ranges is None:
            ranges = []
        self.every = every
        self.at = at
        self.at.sort()
        self.ranges = ranges
        self.ranges.sort(key=lambda cpr: (cpr.start, cpr.stop))

    def __bool__(self) -> bool:
        """Evaluate to true iff any rules are defined"""
        return self.every is not None or bool(self.at) or bool(self.ranges)

    def update(self, overlay: 'CheckpointRules') -> None:
        """Update these checkpointrules with the given overlay.

        The every rule is overwritten if defined. At and ranges are combined.
        """
        if overlay.every is not None:
            self.every = overlay.every
        self.at.extend(overlay.at)
        self.at.sort()
        self.ranges.extend(overlay.ranges)
        self.ranges.sort(key=lambda cpr: (cpr.start, cpr.stop))

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute("every").is_scalar(type(None)):
            node.remove_attribute("every")

        at = node.get_attribute("at")
        if at.is_scalar(type(None)) or (at.is_sequence() and at.is_empty()):
            node.remove_attribute("at")

        ran = node.get_attribute("ranges")
        if ran.is_scalar(type(None)) or (ran.is_sequence() and ran.is_empty()):
            node.remove_attribute("ranges")


class Checkpoints:
    """Defines checkpoints in a configuration.

    There exist two checkpoint triggers: `wallclocktime` and `simulationtime`.
    The `wallclocktime` trigger is based on the elapsed real time since
    starting the muscle_manager in seconds. The `simulationtime` trigger is
    based on the time in the simulation as reported by the instances.

    Note that the `simulationtime` trigger assumes a shared concept of time
    among all components of the model.

    Attributes:
        wallclocktime: checkpoint rules for the wallclocktime trigger
        simulationtime: checkpoint rules for the simulationtime trigger
    """
    def __init__(self,
                 wallclocktime: Optional[CheckpointRules] = None,
                 simulationtime: Optional[CheckpointRules] = None) -> None:
        """Create checkpoint definitions

        Args:
            wallclocktime: checkpoint rules for the wallclocktime trigger.
            simulationtime: checkpoint rules for the simulationtime trigger.
        """
        self.wallclocktime = wallclocktime
        self.simulationtime = simulationtime

    def __bool__(self) -> bool:
        """Evaluate to true iff any rules are defined"""
        return bool(self.wallclocktime) or bool(self.simulationtime)

    def update(self, overlay: 'Checkpoints') -> None:
        """Update this checkpoints with the given overlay.

        See :meth:`CheckpointRules.update`.
        """
        if self.wallclocktime is None:
            self.wallclocktime = overlay.wallclocktime
        elif overlay.wallclocktime is not None:
            self.wallclocktime.update(overlay.wallclocktime)

        if self.simulationtime is None:
            self.simulationtime = overlay.simulationtime
        elif overlay.simulationtime is not None:
            self.simulationtime.update(overlay.simulationtime)

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute("wallclocktime").is_scalar(type(None)):
            node.remove_attribute("wallclocktime")

        if node.get_attribute("simulationtime").is_scalar(type(None)):
            node.remove_attribute("simulationtime")
