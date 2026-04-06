from pathlib import Path
from ymmsl.v0_2 import (
        Component, Conduit, Configuration, ExecutionModel, Model, MPICoresResReq, Ports,
        Program, ThreadedResReq)
from ymmsl import save

components = [
    Component(
            'macro', Ports(o_i='out', s='in'), 'Macro model',
            implementation='macro_model'),
    Component(
            'micro', Ports(f_init='in', o_f='out'), 'Micro model',
            implementation='micro_model')]

conduits = [
    Conduit('macro.out', 'micro.in'),
    Conduit('micro.out', 'macro.in')]

model = Model(
        'my_model', description='Example model created in Python',
        components=components, conduits=conduits)

programs = [
    Program(
        'macro_model', description='Program implementing the macro model',
        executable='/home/user/model'),
    Program(
        'micro_model', description='Micro model program',
        modules='GCC/14.1.0 OpenMPI/5.0.3',
        execution_model=ExecutionModel.OPENMPI, executable='/home/user/model2')]

resources = [
    ThreadedResReq('macro', 1),
    MPICoresResReq('micro', 8)]

config = Configuration(
        'Example configuration', models=[model], programs=programs,
        resources=resources)

save(config, Path('out.ymmsl'))
