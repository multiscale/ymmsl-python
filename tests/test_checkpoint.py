from typing import cast

import pytest
import yatiml

from ymmsl.checkpoint import (
        CheckpointRangeRule, CheckpointAtRule, CheckpointRule, Checkpoints)


def test_checkpointrange():
    dumps = yatiml.dumps_function(CheckpointRangeRule)
    load = yatiml.load_function(CheckpointRangeRule)

    with pytest.raises(ValueError):
        CheckpointRangeRule()

    cp_range = CheckpointRangeRule(every=1)
    assert cp_range.start is None
    assert cp_range.stop is None
    assert cp_range.every == 1
    cp_range = load(dumps(cp_range))
    assert cp_range.start is None
    assert cp_range.stop is None
    assert cp_range.every == 1

    cp_range = CheckpointRangeRule(start=1, stop=99, every=2)
    assert cp_range.start == 1
    assert cp_range.every == 2
    assert cp_range.stop == 99
    cp_range = load(dumps(cp_range))
    assert cp_range.start == 1
    assert cp_range.every == 2
    assert cp_range.stop == 99

    with pytest.raises(ValueError):
        CheckpointRangeRule(every=0)
    with pytest.raises(ValueError):
        CheckpointRangeRule(every=-1.5)

    with pytest.raises(ValueError):
        CheckpointRangeRule(start=10, stop=9, every=1)
    # start == stop is allowed:
    CheckpointRangeRule(start=10, stop=10, every=1)


def test_checkpoints():
    dumps = yatiml.dumps_function(CheckpointRangeRule)
    load = yatiml.load_function(CheckpointRangeRule)


def test_checkpointrules_update():
    load = yatiml.load_function(
            Checkpoints, CheckpointRangeRule, CheckpointAtRule, CheckpointRule)
    rule1 = load("simulation_time: [{every: 300}]")
    rule2 = load("wallclock_time: [{at: [10, 20]}]")
    rule3 = load("wallclock_time: [{at: [15, 5]}]")
    rule4 = load("wallclock_time: [{start: 0, stop: 50, every: 10}]")
    rule5 = load("simulation_time: [{start: 50, stop: 100, every: 10}]")
    rule6 = load("at_end: true")

    rule2.update(rule3)
    assert rule2.simulation_time == []
    assert len(rule2.wallclock_time) == 2
    assert isinstance(rule2.wallclock_time[0], CheckpointAtRule)
    assert isinstance(rule2.wallclock_time[1], CheckpointAtRule)
    assert cast(CheckpointAtRule, rule2.wallclock_time[0]).at == [10, 20]
    assert cast(CheckpointAtRule, rule2.wallclock_time[1]).at == [5, 15]

    rule1.update(rule2)
    assert len(rule1.simulation_time) == 1
    assert len(rule1.wallclock_time) == 2

    assert rule1.at_end is False
    rule1.update(rule6)
    assert rule1.at_end is True

    rule1.update(rule5)
    rule1.update(rule4)
    assert len(rule1.wallclock_time) == 3
    assert len(rule1.simulation_time) == 2
    assert rule1.at_end is True


def test_checkpointrules_scalar_at():
    load = yatiml.load_function(CheckpointAtRule)

    rule = load("at: 5")
    assert rule.at == [5]

    rule = load("at: 1e-12")
    assert rule.at == [1e-12]
