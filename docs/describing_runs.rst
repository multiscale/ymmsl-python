Describing runs
---------------

Once we have a model structure, a configuration for a specific scenario, and programs to
do the calculations, there's only one thing left to configure and that is the run
itself. In yMMSL, we can specify the compute resources to use for each program, and if
the programs support then it we can configure when to checkpoint the simulation.

Resources
`````````

yMMSL allows specifying the amount of resources needed to run an instance of an
implementation. This information is used by MUSCLE3 when it starts each component, to
ensure it has the resources needed to do its calculations. Currently, only the number of
threads or processes can be specified; memory and GPUs are future work.

Resources are specified per component, and apply to each instance of that component. For
single- or multithreaded components, or components that use multiple local processes
(for example with OpenMP, or Python's ``multiprocessing``), you specify the number of
threads. If no resource is defined for a non-MPI component, a default of 1 thread will
be assigned to it at runtime (e.g. by MUSCLE3):

.. code-block:: yaml
    :caption: Resources for threaded processes

    resources:
      macro:
        threads: 1

      micro:
        threads: 8


On the Python side, this is represented by :class:`.ymmsl.v0_2.ThreadedResReq` (short
for ThreadedResourceRequirements), which holds the name of the component it specifies
the resources for in attribute ``name``, and the number of threads or processes
(basically, cores) as ``threads``.

For MPI-based implementations, there are two different ways of specifying the required
resources: core-based and node-based. For core-based resource requirements
(:class:`.ymmsl.v0_2.MPICoresResReq` on the Python side), you specify the number of MPI
processes, and optionally the number of threads per MPI process:

.. code-block:: yaml
    :caption: Core-based resources for MPI components

    resources:
      macro:
        mpi_processes: 32
      micro:
        mpi_processes: 16
        threads_per_mpi_process: 8


On HPC, this allocates each MPI process individually.

Node-based MPI allocations are not yet supported by MUSCLE3, but you can
already specify them as follows:

.. code-block:: yaml
    :caption: Node-based resources for MPI components

    resources:
      macro:
        nodes: 8
        mpi_processes_per_node: 4
        threads_per_mpi_process: 8
      micro:
        nodes: 1
        mpi_processes_per_node: 16


Here, whole nodes are assigned to the implementation, with a specific number of
MPI processes started on each node, and optionally (the default is one) a
certain number of cores per process made available.

More information on how this is interpreted and how MUSCLE3 allocates resources
based on this can be found in the `High-Performance
Computing section in the MUSCLE3 documentation
<https://muscle3.readthedocs.io/en/latest/distributed_execution.html#high-performance-computing>`_.


Checkpoints
```````````

In yMMSL you can specify if you expect the workflow to create checkpoints. Note that all
implementations in your workflow must support checkpointing, MUSCLE3 will generate an
error for you otherwise. See the `documentation for MUSCLE3
<https://muscle3.readthedocs.io/en/latest/>`_ on checkpointing for details on enabling
checkpointing for an implementation.

Checkpoint triggers
^^^^^^^^^^^^^^^^^^^

In yMMSL you have three possible checkpoint triggers:

``at_end``
  Create a checkpoint just before the instance shuts down. This can be a useful
  checkpoint if you intend to resume the workflow at some later point, e.g.  when you
  wish to simulate a longer time span. This trigger is either on or off, specified with
  a boolean ``true`` or ``false`` (default) in the configuration.

``simulation_time``
  Create checkpoints based on the passed simulation time. This can only work properly if
  there is a shared concept of simulated time in the workflow.

``wallclock_time``
  Create checkpoints based on the passed wall clock time (also called `elapsed real time
  <https://en.wikipedia.org/wiki/Elapsed_real_time>`_). This method is not perfect and
  may result in missed checkpoints in certain coupling scenarios. See the MUSCLE3
  documentation for a discussion of the limitations.

When you use any of the time-based triggers, you must also specify at what moments a
checkpoint is expected. MUSCLE3 will then snapshot as soon as possible **after**
reaching the specified times. You may indicate specific moments with ``at``-rules, but
can also create repetitive checkpoints.

.. code-block:: yaml
    :caption: Example checkpoint definition

    checkpoints:
      at_end: true
      simulation_time:
      - at: [1.2, 1.4]
      - every: 1
      wallclock_time:
      - every: 60
        stop: 600
      - every: 600
        start: 600
        stop: 3600
      - every: 1800
        start: 3600

Above example demonstrates all possible checkpoint options. The workflow will create
checkpoints:

- At the end: ``at_end: true``.
- Every second of passed simulated time (``t=0,1,2,...``), and additionally at ``t=1.2``
  and ``t=1.4``.
- Every minute of real elapsed time, for the first 10 minutes; then every 10 minutes for
  the remainder of the first hour; then every 30 minutes until the end.

See the API documentation for :py:class:`~ymmsl.v0_2.CheckpointRangeRule` for more
details on the behaviour of the repetitive checkpoints.

