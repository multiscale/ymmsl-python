Describing models
-----------------

Coupled simulations consist of multiple computer programs that each simulate some part
of or process in the overall system being modelled. To simulate the whole system,
including interactions between the parts, we need to describe all the components and the
connections between them. This is done in the ``models`` section of the YAML file:

.. literalinclude:: example_model.ymmsl
   :caption: ``docs/example_model.ymmsl``
   :language: yaml

If you read this into a variable named ``config``, then ``config`` will contain
an object of type :class:`.ymmsl.v0_2.Configuration`. The yMMSL file above is a nested
dictionary (or mapping, in YAML terms) with at the top level the keys
``ymmsl_version``, and ``models``. The ``ymmsl_version`` key is
handled internally by the library, so it does not show up in the
:class:`.ymmsl.v0_2.Configuration` object. `models` is loaded into ``config.models``
likewise a dictionary mapping model names (as a :class:`.ymmsl.v0_2.Reference`) to
:class:`.ymmsl.v0_2.Model` objects:


.. code-block:: python
    :caption: Accessing the model

    from pathlib import Path
    import ymmsl

    config = ymmsl.load(Path('example_model.ymmsl'))
    model = config.models['macro_micro_model']

    print(model.name)                     # output: macro_micro_model
    print(len(model.supported_settings)   # output: 6


Note that ``model.name`` is filled automatically from the key, it doesn't have to be
specified twice.


Models
``````

The ``models`` section of the yMMSL document describes the simulation model. It has the
model's name, a list of simulation components, and it describes the conduits between
those components. Components include submodels (either programs or nested models, see
below) and helper components like scale bridges, data converters, caches, and any other
bits that make up the coupled simulation. Conduits are the wires between them that are
used to exchange messages.

Models are represented in Python by the :class:`.ymmsl.v0_2.Model` class. It has
attributes ``name``, ``ports``, ``description``, ``supported_settings``, ``components``
and ``conduits`` corresponding to those sections in the file. Only ``name`` and
``description`` are required, although a model without components and conduits isn't
very useful.

Attribute ``name`` is an :class:`.ymmsl.v0_2.Identifier` object containing the name of
the model.  An identifier contains the name of an object, like a simulation model, a
component or a port (see below). It is a string containing letters, digits, and/or
underscores which must start with a letter or underscore, and may not be empty.
Identifiers starting with an underscore are reserved for use by the software (e.g.
MUSCLE3), and may only be used as specified by the software you are using.

The :class:`.ymmsl.v0_2.Identifier` Python class represents an identifier. It works
almost the same as a normal Python ``str``, but checks that the string it contains is
actually a valid identifier.

Attribute ``description`` contains a longer description of the model, preferably
formatted using Markdown. Model ports are used when nesting models, and are explained
below.


Supported settings
``````````````````

Under ``supported_settings``, a description can be given of which settings the model
supports, so that any settings specified by the user can be checked and errors
identified before they can affect the simulation results. Each setting has a name, a
type (one of ``int``, ``str``, ``bool``, ``float``, ``[int]``, ``[float]``, or
``[[float]]`` where the latter three represent list-of-int, list-of-float, and
list-of-list-of-float respectively), and a description. Note that in the YAML, the
description is separated from the type by whitespace, and that it is not a comment.

Supported settings are stored in a :class:`.ymmsl.v0_2.SupportedSettings` object, which
acts like a dictionary mapping the setting name to a
:class:`.ymmsl.v0_2.SupportedSetting` object, which in turn has name, type and
description attributes. Types are represented by :class:`.ymmsl.v0_2.SettingType`.


Simulation Components
`````````````````````

Models may contain a subsection ``components``, in which the components making up the
simulation are described. More or less information may be given:

.. literalinclude:: macro_meso_micro.ymmsl
   :caption: ``docs/macro_meso_micro.ymmsl``
   :language: yaml

This fragment describes a macro-meso-micro model set-up with a single macro model
instance, a single meso model instance, and five micro model instances. For ``macro``,
only the required attributes are given: the name, ports (there aren't any), and a
description (which is empty).

Ports are the connectors on the component to which conduits attach to connect it to
other components, so a component with no ports, while allowed, is not very useful in a
coupled simulation. The meso model therefore has some ports and at least a short
description The ports are organised by operator; we refer to the MUSCLE3 documentation
for more on how they are used. The meso model also has an implementation, allowing it to
be run.

The micro model description shows how to write a longer description, which is always a
good thing to do to help remind other users (including your future self!) of what this
component does. The multiplicity specifies how many instances of this component exist in
the simulation. Multiplicity is a list of integers (e.g. ``[5, 10]`` for five sets of
ten instances), but may be written as a single integer if it's a one-dimensional set, as
shown here for ``micro``.

On the Python side, the ``components`` attribute of :class:`.ymmsl.v0_2.Model` always
contains a list of :class:`.ymmsl.v0_2.Component` objects:

.. literalinclude:: macro_meso_micro.py
   :caption: Accessing the components (``docs/macro_meso_micro.py``)

The ``implementation`` attribute of :class:`.ymmsl.v0_2.Component` refers to an
implementation definition. It should contain the name of a program or of another model,
which is used to implement this component, and which has all of the ports that the
component specifies.

Attributes ``name`` and ``implementation`` are of type :class:`.ymmsl.v0_2.Reference`. A
reference is a string consisting of one or more identifiers (as described above),
separated by periods. Depending on the context, this may represent a name in a namespace
or an attribute of an object (as we will see below with Conduits).


Conduits
````````

The final subsection of the ``model`` section is labeled ``conduits``. Conduits
tie the components together by connecting ports on those components. Only ports
specified by the component can be connected to, and hopefully its description explains
what kind of data the component expects to send or receive on each of its ports.

As you can see, the conduits are written as a dictionary on the YAML side, which maps
senders to receivers. A sender consists of the name of a component, followed by a period
and the name of a port on that component; likewise for a receiver. In the YAML file, the
sender is always on the left of the colon, the receiver on the right.

Just like the simulation components, the conduits get converted to a list in
Python, in this case containing :class:`.ymmsl.v0_2.Conduit` objects. The
:class:`.ymmsl.v0_2.Conduit` class has ``sender`` and ``receiver`` attributes, of
type :class:`.ymmsl.v0_2.Reference` (see above), and a number of helper functions to
interpret these fields, e.g. to extract the component and port name parts.

Note that the format allows specifying a slot here, but this is currently not
supported and illegal in MUSCLE3.

Multicast conduits
^^^^^^^^^^^^^^^^^^

In yMMSL you can specify that an output port is connected to multiple input
ports. When a message is sent on the output port, it is copied and delivered to
all connected input ports. This is called multicast and is expressed as
follows:

.. code-block:: yaml
    :caption: Specifying multicast in yMMSL

    conduits:
      sender.port:
      - receiver1.port
      - receiver2.port

This multicast conduit is converted to a a list of conduits sharing the same
sender:

.. code-block:: python
    :caption: Multicast conduits in python code

    from pathlib import Path
    import ymmsl

    config = ymmsl.load(Path('multicast.ymmsl'))

    conduits = config.model.conduits
    print(len(conduits))    # output: 2
    print(conduits[0])      # output: Conduit(sender.port -> receiver1.port)
    print(conduits[1])      # output: Conduit(sender.port -> receiver2.port)

Nesting models
``````````````

The yMMSL language describes coupled simulations as graphs. For large systems with many
components and conduits, this gets rather unwieldy. In that case, it's best to subdivide
the model graph into submodels that are also graphs, which in turn contain programs, or
maybe even more graphs.

This is enabled in yMMSL by two features: model ports and models as implementations.

Like components, models can have ports:

.. code-block:: yaml
    :caption: A model with ports

    models:
      macro_micro:
        ports:
          f_init: initial_state_in
          o_f: final_state_out
        description:
          A macro micro model that can take an initial state from somewhere outside of
          the model, and send a final state to it
        components:
          macro:
            ports:
              f_init: initial_state_in
              o_i: bc_out
              s: bc_in
              o_f: final_state_out
            description: Macro model, implemented by a program
            # ...
          micro:
            # ...
        conduits:
          initial_state_in: macro.initial_state_in
          macro.final_state_out: final_state_out
          # ... other conduits connecting macro and micro

Model ports have the same operators as ports on components and ports on programs, and
they work in the same way. Conduits can connect model ports to ports on components and
vice versa. Note that these conduits connect an input port to an input port, and an
output port to an output port. They essentially function like extension cables for the
conduit outside the model that is connected to the model port.

Like programs, models can be used as implementations:

.. code-block:: yaml
    :caption: A nested model

    models:
      # ... continued from above
      uq:
        description:
          A model that runs an uncertainty quantification ensemble of the above model
        components:
          uq_driver:
            ports:
              o_i: initial_state_out
              s: final_state_in
            description: |
              This component creates a sample of initial states for the simulation, then
              sends them on initial_state-out to the model to be run. It then collects the
              final state for analysis on final_state_in.
            implementation: uq_driver

          uq_model:
            ports:
              f_init: initial_state_in
              o_f: final_state_out
            description: The model to be run
            implementation: macro_micro

In this example, the ``uq_model`` component is implemented using the ``macro_micro``
model shown previously. Each port specified for ``uq_model`` is present as a model port
in ``macro_micro``, allowing ``macro_micro`` to be used like this.

Multiple files and imports
``````````````````````````

A yMMSL file can contain multiple models that refer to each other, as shown above. For a
large system, especially if it is designed collaboratively by different people, it can
be useful to organise the models into different yMMSL files. The same goes for programs,
which are often written by different people and then reused in the coupled simulation.
It's convenient for each of these programs to come with its own yMMSL file describing
it (see :ref:`Describing programs`).

If the submodels and programs used in a model are not present in the same yMMSL file,
then they must be imported. Import statements go at the top of the yMMSL file, and look
like this:

.. code-block:: yaml
    :caption: Example import statements

    ymmsl_version: v0.2

    description: |
      An example yMMSL file with some import statements

    imports:
      - from utils.uq import implementation uq_driver
      - from models.macro_micro import implementation macro_micro

The first import statement would look for a file named ``uq.ymmsl`` in the ``utils/``
directory, and load a model program named ``uq_driver`` from it. The second one would
look in ``models/`` for a file named ``macro_micro.ymmsl`` and load a program or model
named ``macro_micro`` from it. Once imported, ``uq_driver`` and ``macro_micro`` can then
be used as implementation of a component.

To find files, ymmsl-python will look in two places:

1. Installed Python packages can provide "Entry Points" to provide importable yMMSL
   components.
2. The ``YMMSL_PATH`` environment variable can contain directories with importable yMMSL
   files.

These mechanisms are described in more detail below.


YMMSL Path
^^^^^^^^^^

Ymmsl-python will inspect the ``YMMSL_PATH`` environment variable for
directories to search. This should contain one or more colon-separated paths pointing to
directories with yMMSL files, in the same way that ``PATH`` points to directories with
executables and ``PYTHONPATH`` to directories with Python files to be imported.

For example, if ``YMMSL_PATH`` equals ``/home/user/ymmsl:/home/user/my_project`` then the
first import statement would first look for ``/home/user/ymmsl/utils/uq.ymmsl`` and then
for ``/home/user/my_project/utils/uq.ymmsl`` if that did not exist.


Python Entry Points
^^^^^^^^^^^^^^^^^^^

Installed Python packages can provide entry points for ymmsl-python to advertise that
they provide importable yMMSL components.
For example, the first import statement above would look for an entry point named
``utils.uq`` and try to load that configuration.

If you are a developer of a Python package and want to use the entry point mechanism so
users can import your component, you will need to:

1. Configure the entry point in your ``pyproject.toml`` (or ``setup.py``) file.
2. Provide the yMMSL configuration as a string inside your python distribution.

Below code listings provide an example how to do this.

.. code-block:: toml
    :caption: Entry point configuration in ``pyproject.toml``

    # Indicate you want to provide an entry point for "ymmsl.module":
    [project.entry-points."ymmsl.module"]
    # Provide one or more "name = value" entries, pointing to a valid yMMSL
    # configuration string (see next code listing). For more details, see
    # https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-syntax
    "utils.uq" = "my_package.utils.uq:YMMSL_CONFIG"

.. code-block:: python
    :caption: yMMSL configuration string in ``my_package/utils/uq.py``

    import sys

    YMMSL_CONFIG = f"""
    ymmsl_version: v0.2
    description: Uncertainty Quantification utilities from my_package
    programs:
      uq_driver:
        description: |
          This component creates a sample of initial states for the simulation, then
          sends them on initial_state-out to the model to be run. It then collects the
          final state for analysis on final_state_in.
        executable: {sys.executable}
        args: -m my_package.utils.uq
        ports:
          o_i: initial_state_out
          s: final_state_in
    """


.. seealso::
  - User guide on Entry Points from setuptools:
    https://setuptools.pypa.io/en/latest/userguide/entry_point.html
  - The Entry Points specification:
    https://packaging.python.org/en/latest/specifications/entry-points/
