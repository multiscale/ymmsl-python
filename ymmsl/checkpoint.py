"""Definitions for describing checkpoints."""

from typing import List, Optional, Union

import yatiml


class CheckpointRange:
    def __init__(self,
                 step: Union[float, int],
                 start: Optional[Union[float, int]] = None,
                 stop: Optional[Union[float, int]] = None) -> None:
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
    def __init__(self,
                 every: Optional[Union[float, int]] = None,
                 at: Optional[List[Union[float, int]]] = None,
                 ranges: Optional[List[CheckpointRange]] = None) -> None:
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
    def __init__(self,
                 wallclocktime: Optional[CheckpointRules] = None,
                 simulationtime: Optional[CheckpointRules] = None) -> None:
        self.wallclocktime = wallclocktime
        self.simulationtime = simulationtime

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute("wallclocktime").is_scalar(type(None)):
            node.remove_attribute("wallclocktime")

        if node.get_attribute("simulationtime").is_scalar(type(None)):
            node.remove_attribute("simulationtime")
