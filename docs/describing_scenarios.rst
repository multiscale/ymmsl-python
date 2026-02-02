Describing scenarios
--------------------

In yMMSL, a model's structure is described in terms of its components and conduits,
representing the overall structure of the system to be simulated and the interactions
within it. To simulate a specific scenario, this basic structure will need some specific
configuration. yMMSL provides two mechanisms to do this, custom implementations and
settings.

Custom implementations
``````````````````````

Custom implementations modify a model by overriding the implementation of a particular
model component, or filling it in if it didn't have one. This makes it possible to have
optional parts of a model, or to provide a generic model structure for others to plug
programs into.

In yMMSL, this is implemented as a simple mapping from a component name to an
implementation name, in the ``custom_implementations`` section:

.. code-block:: yaml
    :caption: Custom implementations

    custom_implementations:
      component1: program1
      component2.component1: program2

In this example, the model has a component named ``component1``, whose implementation is
set to ``program1``. A second component ``component2`` is implemented using a submodel,
which in turn has a component ``component1``, whose implementation is set to
``program2``.

Note that it is possible to set a model as an implementation also here, but that this is
probably best avoided as it is likely to lead to confusion.

Settings
````````

The settings section contains settings for the simulation to run with. In YAML, this is
a dictionary that maps a setting name (a :class:`.ymmsl.v0_2.Reference`) to its value.
Parameter values may be strings, integers, floating point numbers, lists of integers,
lists of floating point numbers (vectors), or lists of lists of floating point numbers
(arrays).

.. code-block:: yaml
    :caption: Settings example

    settings:
      domain.grain: 0.01
      domain.extent.x: 1.0
      domain.extent.y: 1.0
      macro.timestep: 10.0
      macro.total_time: 1000.0
      micro.timestep: 0.01
      micro.total_time: 1.0

      interpolate: true
      interpolation_method: linear
      kernel:
        - [0.8, 0.2]
        - [0.2, 0.8]


In this example, there is a macro-micro model in which the two models share a
one-dimensional domain, which is named domain, has a length and width of 1.0, and a grid
spacing of 0.01. The macro model has a time step of 10 and a total run time of 1000 (so
it will run for 100 steps), while the micro model has a time step of 0.01 and a total
run time of 1.0. Furthermore, there are some other model settings, a boolean switch that
enables interpolation, a string to select the interpolation method, and a 2D array
specifying a kernel of some kind.

On the Python side, this will be turned into a :class:`.ymmsl.v0_2.Settings` object,
which acts much like a Python dictionary. So for instance, if you have a
:class:`.ymmsl.v0_2.Configuration` object named ``config`` which was loaded from a file
containing the above ``settings`` section, then you could write:

.. code-block:: python

    grid_dx = config.settings['domain.grain']
    kernel = config.settings['kernel']

to obtain a floating point value of 0.1 in ``grid_dx`` and a list of lists
``[[0.8, 0.2], [0.2, 0.8]]`` in ``kernel``.

