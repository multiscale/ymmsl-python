from pathlib import Path

import pytest

import ymmsl.v0_1 as v0_1


@pytest.fixture
def empty_config() -> v0_1.PartialConfiguration:
    return v0_1.PartialConfiguration()


@pytest.fixture
def full_config() -> v0_1.PartialConfiguration:
    # TODO: return a Configuration once we have everything in here

    components = [
            v0_1.Component(
                'macro', 'macro_impl', 10, v0_1.Ports(o_i=['out'], s=['in'])),
            v0_1.Component(
                'micro', 'micro_impl', 10, v0_1.Ports(f_init=['init'], o_f=['final']))]

    conduits = [
            v0_1.Conduit('macro.out', 'micro.init'),
            v0_1.Conduit('micro.final', 'macro.in')]

    model = v0_1.Model('test_model', components, conduits)
    settings = v0_1.Settings({'a': 42, 'b': 'Test'})
    resources = [
            v0_1.ThreadedResReq(v0_1.Reference('A'), 8),
            v0_1.MPICoresResReq(v0_1.Reference('B'), 4, 8)]

    description = 'Testing a full configuration'

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
           model, settings, None, resources, description,
           checkpoints, resume)
