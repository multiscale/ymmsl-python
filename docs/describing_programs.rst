Describing programs
-------------------

Components are abstract objects. For an actual simulation to run, we need
computer programs that implement the components of the simulation. As we've seen
above, components refer to implementations, and those implementations can be either more
models, or programs.

Where the model structure depends on the system being simulated, and the model
configuration on the particular scenario that we want to simulate, the information in
the programs section derives from the properties of the programs used in the simulation
and how they are installed on the local machine.

A good way to organise this is to have a separate yMMSL file for each installed program,
which could be adapted from a template describing the program's fixed properties and
adapted to the specific way its been compiled and installed.

Programs
````````

Programs are defined in the ``programs`` section of a yMMSL file:

.. code-block:: yaml
    :caption: Defining programs

    programs:
      simplest:
        executable: /home/user/models/my_model

      python_script:
        virtual_env: /home/user/envs/my_env
        executable: python3
        args: /home/user/models/my_model.py

      with_env_and_args:
        env:
          LD_LIBRARY_PATH: /home/user/muscle3/lib
          ENABLE_AWESOME_SCIENCE: 1
        executable: /home/user/models/my_model
        args:
          - --some-lengthy-option
          - --some-other-lengthy-option=some-lengthy-value


As you can see, there are quite a few different ways of describing an implementation,
but all implementations have a name, which is the key in the dictionary, by which a
component can refer to it.

The ``simplest`` implementation only has an executable. This could be a (probably
statically linked) executable, or a script that sets up an environment and starts the
model.

If your model or other component is a Python script, then you may want to load a virtual
environment before starting it, to make the dependencies available. This is done using
the ``virtual_env`` attribute. If the script does not have a ``#!/usr/bin/env python``
line at the top (in which case you could set it as the executable) then you need to
start the Python interpreter directly, and pass the location of the script as an
argument.

Environment variables can be set through the ``env`` attribute, which contains a
dictionary mapping variable names to values, as shown for the ``with_env_and_args``
example. This also shows that you can pass the arguments as a list, if that makes things
easier to read.

.. code-block:: yaml
    :caption: MPI and HPC programs

    programs:
      mpi_implementation:
        executable: /home/user/models/my_model
        execution_model: openmpi

      on_hpc_cluster:
        modules: GCC/14.1.0 OpenMPI/5.0.3
        executable: /home/user/models/my_model
        execution_model: openmpi

      with_script:
        script: |
          #!/bin/bash

          . /home/user/muscle3/bin/muscle3.env
          export ENABLE_AWESOME_SCIENCE=1

          /home/user/models/my_model -v -x


MPI programs are a bit special, as they need to be started via ``mpirun``.  However,
``mpirun`` assumes that the program to start is going to use all of the available
resources. For a coupled simulation with multiple components, that is usually not what
you want. It is possible to tell ``mpirun`` to only use some of the resources, but of
course we don't know which ones will be available while writing this file.

So, in yMMSL, you simply specify the path to the executable, and set the
``execution_model`` attribute to ``openmpi``, ``srunmpi`` or ``intelmpi`` depending on
the MPI implementation and HPC machine you're using. When executing with MUSCLE3, the
MUSCLE Manager will then start the component on its designated subset of the resources
as required.

The ``on_hpc_cluster`` program demonstrates loading environment modules, as
commonly needed on HPC machines. They're all in one line here, but if the modules have
long names, then like with the arguments you can make a list to keep things readable.

Finally, if you need to do something complicated, you can write an inline script
to start the program. This currently only works for non-MPI programs
however.

Programs are represented by :class:`.ymmsl.v0_2.Program` in Python.

Keeps state for next use
````````````````````````

Implementations may indicate if they carry state between reuses. This is currently only
used for :ref:`Checkpoints`, but might see further use in the future (e.g. for load
balancers). There are three possible values an implementation may indicate.

Necessary
  This implementation remembers state between consecutive iterations of the reuse loop.
  That state is required for the proper execution of the implementation.

  This is the default value when not specified.

  **Example:** A micro model simulating an enclosed volume, where every reuse the
  boundary conditions are updated by the connected macro model. This micro model must
  keep track of the state inside the simulated volume between iterations of the reuse
  loop.

No
  This implementation has no state between consecutive iterations of the reuse loop.

  **Example:** A data converter that receives on an ``F_INIT`` port, transforms the data
  and outputs it on an ``O_F`` port. The transformation is only dependent on the
  information of the ``F_INIT`` message.

Helpful
  This implementation remembers state between consecutive iterations of the reuse loop.
  However, this state is not required for proper execution.

  **Example:** A simulation of a fluid in a pipe with obstacles. The simulation
  converges much faster when starting from the solution of the previous iteration.
  However, the same solution can still be found when starting from scratch.
