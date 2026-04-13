from ymmsl.v0_2.timelines import TimelineTree
from pathlib import Path
import ymmsl
from ymmsl.v0_2 import Configuration, Reference as Ref, Timeline, ConduitFilter

import pytest

ROOT_TIMELINE = Timeline(":")


@pytest.fixture()
def timelines_configuration() -> Configuration:
    return ymmsl.load_as(
        Configuration, Path(__file__).parent / "ymmsl1/timelines.ymmsl"
    )


def test_consistent_configuration(timelines_configuration: Configuration) -> None:
    timelines_configuration.check_consistent()


def test_dispatch(timelines_configuration: Configuration) -> None:
    tltree = TimelineTree(timelines_configuration.models[Ref("dispatch")])
    assert tltree.component_timeline(Ref("first")) == ROOT_TIMELINE
    assert tltree.component_timeline(Ref("second")) == ROOT_TIMELINE


def test_macromicro(timelines_configuration: Configuration) -> None:
    tltree = TimelineTree(timelines_configuration.models[Ref("macromicro")])
    assert tltree.component_timeline(Ref("macro")) == ROOT_TIMELINE
    assert tltree.component_timeline(Ref("micro")) == Timeline(":macro")


def test_cycle(timelines_configuration: Configuration) -> None:
    with pytest.raises(RuntimeError, match="Cycle detected"):
        TimelineTree(timelines_configuration.models[Ref("cycle")])


def test_reducer(timelines_configuration: Configuration) -> None:
    tltree = TimelineTree(timelines_configuration.models[Ref("reducer")])
    assert tltree.component_timeline(Ref("first")) == ROOT_TIMELINE
    assert tltree.component_timeline(Ref("second")) == ROOT_TIMELINE


def test_too_many_reducers(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("reducer")]
    model.conduits[-1].filters.append(model.conduits[-1].filters[0])
    with pytest.raises(ValueError, match="Too many reducer filters"):
        TimelineTree(model)


def test_inconsistent_timelines(timelines_configuration: Configuration) -> None:
    with pytest.raises(ValueError, match="Inconsistent timelines"):
        TimelineTree(timelines_configuration.models[Ref("inconsistent")])


def test_repeaters(timelines_configuration: Configuration) -> None:
    tltree = TimelineTree(timelines_configuration.models[Ref("repeaters")])
    assert tltree.component_timeline(Ref("macro")) == ROOT_TIMELINE
    assert tltree.component_timeline(Ref("meso")) == Timeline(":macro")
    assert tltree.component_timeline(Ref("micro")) == Timeline(":macro:meso")


def test_too_many_repeaters(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeaters")]
    model.conduits[-2].filters.append(ConduitFilter.REPEAT)
    with pytest.raises(ValueError, match="Too many repeater filters"):
        TimelineTree(model)


def test_too_few_repeaters(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeaters")]
    model.conduits[-1].filters.pop()
    with pytest.raises(ValueError, match="Inconsistent timelines"):
        TimelineTree(model)


def test_repeater_and_too_many_reducers(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeaters")]
    model.conduits[-1].filters.insert(0, ConduitFilter.LAST)
    with pytest.raises(ValueError, match="Too many reducer filters"):
        TimelineTree(model)


def test_repeater_after_reducer(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeater_reducer")]
    tltree = TimelineTree(model)
    assert tltree.component_timeline(Ref("macro1")) == ROOT_TIMELINE
    assert tltree.component_timeline(Ref("macro2")) == ROOT_TIMELINE
    assert tltree.component_timeline(Ref("micro1")) == Timeline(":macro1")
    assert tltree.component_timeline(Ref("micro2")) == Timeline(":macro2")

    # Removing the filters on the last conduit is a problem
    model.conduits[-1].filters = []
    with pytest.raises(ValueError, match="Inconsistent timelines"):
        TimelineTree(model)


def test_repeater_after_reducer_error(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeater_reducer_error")]
    with pytest.raises(ValueError, match="repeater after reducer"):
        TimelineTree(model)
    model.conduits[-1].filters = []
    tltree = TimelineTree(model)
    assert tltree.component_timeline(Ref("macro")) == ROOT_TIMELINE
    assert tltree.component_timeline(Ref("micro1")) == Timeline(":macro")
    assert tltree.component_timeline(Ref("micro2")) == Timeline(":macro")
