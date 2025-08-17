from pathlib import Path

from ymmsl.conversion.convert_v0_1_to_v0_2 import convert_v0_1_to_v0_2

import ymmsl.v0_1 as v0_1
import ymmsl.v0_2 as v0_2


Ref1 = v0_1.Reference


Ref2 = v0_2.Reference


def test_convert_simple_config(empty_config: v0_1.PartialConfiguration) -> None:
    v2 = convert_v0_1_to_v0_2(empty_config)
    assert v2.description == ''
    assert isinstance(v2.settings, v0_2.Settings)
    assert len(v2.settings) == 0
    assert v2.resources == {}
    assert isinstance(v2.checkpoints, v0_2.Checkpoints)
    assert v2.checkpoints.at_end is False
    assert len(v2.checkpoints.wallclock_time) == 0
    assert len(v2.checkpoints.simulation_time) == 0
    assert v2.resume == {}


def test_convert_full_config(full_config: v0_1.Configuration) -> None:
    v2 = convert_v0_1_to_v0_2(full_config)
    assert v2.description == 'Testing a full configuration'

    assert v2.settings is not full_config.settings
    assert len(v2.settings) == 2
    assert v2.settings['a'] == 42
    assert v2.settings['b'] == 'Test'

    assert v2.resources is not full_config.resources
    assert len(v2.resources) == 2

    ra = v2.resources[Ref2('A')]
    assert ra is not full_config.resources[Ref1('A')]
    assert isinstance(ra, v0_2.ThreadedResReq)
    assert ra.name == 'A'
    assert ra.threads == 8

    rb = v2.resources[Ref2('B')]
    assert rb is not full_config.resources[Ref1('B')]
    assert isinstance(rb, v0_2.MPICoresResReq)
    assert rb.name == 'B'
    assert rb.mpi_processes == 4
    assert rb.threads_per_mpi_process == 8

    assert v2.checkpoints.at_end is True
    wt = v2.checkpoints.wallclock_time
    assert wt is not full_config.checkpoints.wallclock_time
    assert isinstance(wt, list)
    assert len(wt) == 2
    assert wt[0] is not full_config.checkpoints.wallclock_time[0]
    assert isinstance(wt[0], v0_2.CheckpointRangeRule)
    assert wt[0].start == 0.0
    assert wt[0].stop == 7200.0
    assert wt[0].every == 900.0
    assert isinstance(wt[1], v0_2.CheckpointAtRule)
    assert wt[1].at == [4.0, 10.0]

    st = v2.checkpoints.simulation_time
    assert isinstance(st, list)
    assert len(st) == 2
    assert st[0] is not full_config.checkpoints.simulation_time[0]
    assert isinstance(st[0], v0_2.CheckpointAtRule)
    assert st[0].at == [3.0, 14.0]

    assert st[1] is not full_config.checkpoints.simulation_time[1]
    assert isinstance(st[1], v0_2.CheckpointRangeRule)
    assert st[1].start == 0.0
    assert st[1].stop == 720.0
    assert st[1].every == 90.0

    assert isinstance(v2.resume, dict)
    assert v2.resume[Ref2('A')] is not full_config.resume[Ref1('A')]
    assert v2.resume[Ref2('A')] == Path('/path/to/snapshot_A.pack')
    assert v2.resume[Ref2('B')] is not full_config.resume[Ref1('B')]
    assert v2.resume[Ref2('B')] == Path('/path/to/snapshot_B.pack')
