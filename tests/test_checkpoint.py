import pytest
import yatiml

from ymmsl.checkpoint import CheckpointRange, CheckpointRules


def test_checkpointrange():
    dumps = yatiml.dumps_function(CheckpointRange)
    load = yatiml.load_function(CheckpointRange)

    cp_range = CheckpointRange(1)
    assert cp_range.start is None
    assert cp_range.stop is None
    assert cp_range.step == 1
    cp_range = load(dumps(cp_range))
    assert cp_range.start is None
    assert cp_range.stop is None
    assert cp_range.step == 1

    cp_range = CheckpointRange(start=1, step=2, stop=99)
    assert cp_range.start == 1
    assert cp_range.step == 2
    assert cp_range.stop == 99
    cp_range = load(dumps(cp_range))
    assert cp_range.start == 1
    assert cp_range.step == 2
    assert cp_range.stop == 99

    with pytest.raises(ValueError):
        CheckpointRange(step=0)
    with pytest.raises(ValueError):
        CheckpointRange(step=-1.5)

    with pytest.raises(ValueError):
        CheckpointRange(start=10, stop=9, step=1)
    # start == stop is allowed:
    CheckpointRange(start=10, stop=10, step=1)


def test_checkpointrules():
    dumps = yatiml.dumps_function(CheckpointRules, CheckpointRange)
    load = yatiml.load_function(CheckpointRules, CheckpointRange)

    rules = CheckpointRules(every=100)
    assert rules.every == 100
    assert rules.at == []
    assert rules.ranges == []
    rules = load(dumps(rules))
    assert rules.every == 100
    assert rules.at == []
    assert rules.ranges == []

    rules = CheckpointRules(at=[4, 1, 3])
    assert rules.at == [1, 3, 4]  # test sorting
    assert rules.every is None
    assert rules.ranges == []
    rules = load(dumps(rules))
    assert rules.at == [1, 3, 4]
    assert rules.every is None
    assert rules.ranges == []

    rules = CheckpointRules(ranges=[
        CheckpointRange(start=300, stop=500, step=1),
        CheckpointRange(start=0, stop=100, step=3),
        CheckpointRange(start=100, stop=300, step=2)])
    assert rules.every is None
    assert rules.at == []
    assert rules.ranges[0].start == 0
    assert rules.ranges[1].start == 100
    assert rules.ranges[2].start == 300
    assert rules.ranges[0].step == 3
    assert rules.ranges[1].step == 2
    assert rules.ranges[2].step == 1
    assert rules.ranges[0].stop == 100
    assert rules.ranges[1].stop == 300
    assert rules.ranges[2].stop == 500
    rules = load(dumps(rules))
    assert rules.every is None
    assert rules.at == []
    assert rules.ranges[0].start == 0
    assert rules.ranges[1].start == 100
    assert rules.ranges[2].start == 300
    assert rules.ranges[0].step == 3
    assert rules.ranges[1].step == 2
    assert rules.ranges[2].step == 1
    assert rules.ranges[0].stop == 100
    assert rules.ranges[1].stop == 300
    assert rules.ranges[2].stop == 500

    with pytest.raises(RuntimeError):
        CheckpointRules(every=1, ranges=[CheckpointRange(10)])
