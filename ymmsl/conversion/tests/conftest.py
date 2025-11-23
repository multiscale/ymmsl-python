from pathlib import Path

import pytest

import ymmsl.v0_1 as v0_1


@pytest.fixture
def empty_config() -> v0_1.PartialConfiguration:
    return v0_1.PartialConfiguration()


@pytest.fixture
def full_config() -> v0_1.PartialConfiguration:
    # TODO: return a Configuration once we have everything in here

    description = 'Testing a full configuration'
    settings = v0_1.Settings({'a': 42, 'b': 'Test'})
    resources = [
            v0_1.ThreadedResReq(v0_1.Reference('A'), 8),
            v0_1.MPICoresResReq(v0_1.Reference('B'), 4, 8)]

    checkpoints = v0_1.Checkpoints(
            True, [
                v0_1.CheckpointRangeRule(0.0, 7200.0, 900.0),
                v0_1.CheckpointAtRule([10.0, 4.0]),
                ],
            [
                v0_1.CheckpointAtRule([3.0, 14.0]),
                v0_1.CheckpointRangeRule(0.0, 720.0, 90.0)
                ])

    resume = {
            v0_1.Reference('A'): Path('/path/to/snapshot_A.pack'),
            v0_1.Reference('B'): Path('/path/to/snapshot_B.pack')}

    return v0_1.PartialConfiguration(
            None, settings, None, resources, description, checkpoints, resume)
