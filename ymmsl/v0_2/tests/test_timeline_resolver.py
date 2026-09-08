from pathlib import Path

import pytest

import ymmsl
from ymmsl.v0_2 import ConduitFilter, Configuration, Timeline
from ymmsl.v0_2 import Reference as Ref
from ymmsl.v0_2.timeline_resolver import (
    ROOT_TIMELINE,
    ConduitTimelineError,
    CyclicDependency,
    InconsistentTimelines,
    TooManyReducerFilters,
    resolve_timelines,
)


@pytest.fixture()
def timelines_configuration() -> Configuration:
    return ymmsl.load_as(
        Configuration, Path(__file__).parent / "ymmsl1/timelines.ymmsl"
    )


def test_consistent_configuration(timelines_configuration: Configuration) -> None:
    timelines_configuration.check_consistent()


def test_dispatch(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("dispatch")]
    resolve_timelines(model)
    assert model.components[Ref("first")].timeline == ROOT_TIMELINE
    assert model.components[Ref("second")].timeline == ROOT_TIMELINE


def test_macromicro(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("macromicro")]
    resolve_timelines(model)
    assert model.components[Ref("macro")].timeline == ROOT_TIMELINE
    assert model.components[Ref("micro")].timeline == Timeline(":macro")

    # Check that ports have the correct relative timelines:
    macro = model.components[Ref("macro")]
    assert macro.ports["init"].timeline == Timeline("")
    assert macro.ports["out"].timeline == Timeline("macro")
    assert macro.ports["in"].timeline == Timeline("macro")

    for micro_port in model.components[Ref("micro")].ports.values():
        assert micro_port.timeline == Timeline("")


def test_cycle(timelines_configuration: Configuration) -> None:
    with pytest.raises(CyclicDependency, match="cycle in model"):
        resolve_timelines(timelines_configuration.models[Ref("cycle")])


def test_reducer(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("reducer")]
    resolve_timelines(model)
    assert model.components[Ref("first")].timeline == ROOT_TIMELINE
    assert model.components[Ref("second")].timeline == ROOT_TIMELINE


def test_only_reducer(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("reducer")]
    # Remove the conduit first.final -> second.init1 and keep only the reduced conduit
    del model.conduits[0]
    assert model.conduits[0].filters == [ConduitFilter("last")]
    resolve_timelines(model)
    assert model.components[Ref("first")].timeline == ROOT_TIMELINE
    assert model.components[Ref("second")].timeline == ROOT_TIMELINE


def test_too_many_reducers(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("reducer")]
    model.conduits[-1].filters.append(model.conduits[-1].filters[0])
    with pytest.raises(TooManyReducerFilters, match="too many reducer filters"):
        resolve_timelines(model)


def test_inconsistent_timelines(timelines_configuration: Configuration) -> None:
    with pytest.raises(InconsistentTimelines):
        resolve_timelines(timelines_configuration.models[Ref("inconsistent")])


def test_repeaters(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeaters")]
    resolve_timelines(model)
    assert model.components[Ref("macro")].timeline == ROOT_TIMELINE
    assert model.components[Ref("meso")].timeline == Timeline(":macro")
    assert model.components[Ref("micro")].timeline == Timeline(":macro:meso")


def test_too_many_repeaters(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeaters")]
    model.conduits[-2].filters.append(ConduitFilter.REPEAT)
    with pytest.raises(ConduitTimelineError, match="remove a repeater"):
        resolve_timelines(model)


def test_too_few_repeaters(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeaters")]
    model.conduits[-1].filters.pop()
    with pytest.raises(ConduitTimelineError, match="add a repeater"):
        resolve_timelines(model)


def test_repeater_and_too_many_reducers(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeaters")]
    model.conduits[-1].filters.insert(0, ConduitFilter.LAST)
    with pytest.raises(TooManyReducerFilters, match="too many reducer filters"):
        resolve_timelines(model)


def test_repeater_after_reducer(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeater_reducer")]
    resolve_timelines(model)
    assert model.components[Ref("macro1")].timeline == ROOT_TIMELINE
    assert model.components[Ref("macro2")].timeline == ROOT_TIMELINE
    assert model.components[Ref("micro1")].timeline == Timeline(":macro1")
    assert model.components[Ref("micro2")].timeline == Timeline(":macro2")

    # Remove filters on the last conduit to make the incoming timelines inconsistent
    model.conduits[-1].filters = []
    with pytest.raises(InconsistentTimelines, match="different timelines"):
        resolve_timelines(model)


def test_repeater_after_reducer_error(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("repeater_reducer_error")]
    with pytest.raises(ConduitTimelineError, match="remove a repeater and reducer"):
        resolve_timelines(model)
    model.conduits[-1].filters = []
    resolve_timelines(model)
    assert model.components[Ref("macro")].timeline == ROOT_TIMELINE
    assert model.components[Ref("micro1")].timeline == Timeline(":macro")
    assert model.components[Ref("micro2")].timeline == Timeline(":macro")


def test_inconsistent_interact(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("inconsistent_interact")]
    with pytest.raises(ConduitTimelineError, match="missing timeline annotations"):
        resolve_timelines(model)
    model.components[Ref("B")].ports["out"].timeline = Timeline("A")
    model.components[Ref("B")].ports["in"].timeline = Timeline("A")
    resolve_timelines(model)


def test_model_ports(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("model_ports")]
    resolve_timelines(model)


def test_muscle_settings_in(timelines_configuration: Configuration) -> None:
    model = timelines_configuration.models[Ref("qmc")]
    resolve_timelines(model)
