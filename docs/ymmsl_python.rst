Usage
=====

As shown on the previous page, the ``ymmsl-python`` library converts yMMSL from
YAML to Python objects and back. Here, we dive into this a bit deeper and see
how those Python objects can be used.

Generally speaking, the object model used by the ``ymmsl`` library follows the
structure of the YAML document, but there are a few places where some syntactic
sugar has been added to make the files easier to read and write by hand. Let's
have a look at the example again:

.. literalinclude:: example.ymmsl
    :caption: ``docs/example.ymmsl``
    :language: yaml

If you read this into a variable named ``config``, then ``config`` will contain
an object of type :class:`ymmsl.Configuration`. The yMMSL file above is a nested
dictionary (or mapping, in YAML terms) with at the top level the keys
``ymmsl_version``, ``model`` and ``settings``. The ``ymmsl_version`` key is
handled internally by the library, so it does not show up in the
:class:`ymmsl.Configuration` object. The others, `model` and `settings` are
loaded into attributes of ``config``.

Note that `settings` is optional: if it is not given in the YAML file, the
corresponding attribute will be an empty :class:`ymmsl.Settings` object.
Likewise, when saving an empty :class:`ymmsl.Configuration`, the `settings`
section will be omitted.

As a result, ``config.model`` will give you an object representing the model
part of the file, while ``config.settings`` contains an object with the
settings in it. :class:`ymmsl.Configuration` is just a simple record that holds
the two parts together, so this is all it can do.

Models
------

The ``model`` section of the yMMSL document describes the simulation model. It
has the model's name, a list of simulation components, and it describes the
conduits between those components. (Simulation) components are submodels, scale
bridges, mappers, proxies, and any other program that makes up the coupled
simulation. Conduits are the wires between them that are used to exchange
messages.

The ``model`` section is represented in Python by the :class:`ymmsl.Model`
class. It has attributes ``name``, ``components`` and ``conduits``
corresponding to those sections in the file. Attribute `name` is an
:class:`ymmsl.Identifier` object.

Note that conduits are optional, you may have a model that consists of only one
component and no conduits at all. In YAML, you can write this by omitting the
conduits attribute. In Python, you can also omit the conduits argument when
constructing a Model. In both cases, the ``conduits`` attribute will be an empty
list.


.. code-block:: python
    :caption: Accessing the model

    import ymmsl

    with open('example.ymmsl', 'r') as f:
        config = ymmsl.load(f)

    print(config.model.name)        # output: macro_micro_model
    print(len(config.model.components))   # output: 2

An identifier contains the name of an object, like a simulation model,
a component or a port (see below). It is a string containing letters,
digits, and/or underscores which must start with a letter or underscore, and may
not be empty. Identifiers starting with an underscore are reserved for use by
the software (e.g. MUSCLE 3), and may only be used as specified by the software
you are using.

The :class:`ymmsl.Identifier` Python class represents an identifier. It works
almost the same as a normal Python ``str``, but checks that the string it
contains is actually a valid identifier.

Simulation Components
`````````````````````

The ``model`` section contains a subsection ``components``, in which the
components making up the simulation are described. These are the
submodels, and special components like scale bridges, data converters, load
balancers, etc. yMMSL lets you describe components in two ways, a short
one and a longer one:

.. code-block:: yaml
    :caption: ``Macro-meso-micro model components``

    components:
      macro: my.macro_model
      meso:
        implementation: my.meso_model
        multiplicity: 5
      micro:
        implementation: my.micro_model
        multiplicity: [5, 10]


This fragment describes a macro-meso-micro model set-up with a single macro
model instance, five instances of the meso model, and five sets of ten micro
model instances each. If the simulation requires only a single instance of a
component, the short form can be used, as above for the ``macro`` component. It
simply maps the name of the component to an implementation (more on those
in a moment).

The longer form maps the name of the component to a dictionary containing
two attributes, the ``implementation`` and the ``multiplicity``. The
implementation is the name of the implementation as in the short form, while the
multiplicity specifies how many instances of this component exist in the
simulation. Multiplicity is a list of integers (as for ``micro`` in this
example), but may be written as a single integer if it's a one-dimensional set
(as for ``meso``).

All this is a concise and easy to read and write a YAML file, but on the Python
side, all this flexibility would make for complex code. To avoid that, the
ymmsl-python library applies syntactic sugar when converting between YAML and
Python. On the Python side, the ``components`` attribute of
:class:`ymmsl.Model` always contains a list of :class:`ymmsl.Component`
objects, regardless of how the YAML file was written. When this list is written
to a YAML file, the most concise representation is automatically chosen to make
the file easier to read by a human user.

.. code-block:: python
    :caption: Accessing the simulation components

    import ymmsl

    with open('macro_meso_micro.ymmsl', 'r') as f:
        config = ymmsl.load(f)

    cps = config.model.components
    print(cps[0].name)              # output: macro
    print(cps[0].implementation)    # output: my.macro_model
    print(cps[0].multplicity)       # output: []
    print(cps[2].name)              # output: micro
    print(cps[2].implementation)    # output: my.micro_model
    print(cps[2].multplicity)       # output: [5, 10]

(Note that ``macro_meso_micro.ymmsl`` does not come with this documentation, go
ahead and make it yourself using the above listing!)

The :class:`ymmsl.Component` class has three attributes, unsurprisingly
named ``name``, ``implementation`` and ``multiplicity``. Attributes ``name``
and ``implementation`` are of type :class:`ymmsl.Reference`. A reference
is a string consisting of one or more identifiers (as described above),
separated by periods.

Depending on the context, this may represent a name in a namespace (as it is
here), or an attribute of an object (as we will see below with Conduits). The
``multiplicity`` attribute is always a list of ints, but may be omitted or
given as a single int when creating a :class:`ymmsl.Component` object, just
like in the YAML file.

The ``implementation`` attribute of :class:`ymmsl.Component` is intended
to be a reference to some implementation definition in the launcher
configuration, so consult the documentation for that to see what to write here.

Conduits
````````

The final subsection of the ``model`` section is labeled ``conduits``. These
tie the components together by connecting `ports` on those components. Which
ports a component has depends on the component, so you have to look at its
documentation (or the source code, if there isn't any documentation) to see
which ports are available and how they should be used.

As you can see, the conduits are written as a dictionary on the YAML
side, which maps senders to receivers. A sender consists of the name of a
component, followed by a period and the name of a port on that component;
likewise for a receiver. In the YAML file, the sender is always on the left of
the colon, the receiver on the right.

Just like the simulation components, the conduits get converted to a list in
Python, in this case containing :class:`ymmsl.Conduit` objects. The
:class:`ymmsl.Conduit` class has ``sender`` and ``receiver`` attributes, of
type :class:`ymmsl.Reference` (see above), and a number of helper functions to
interpret these fields, e.g. to extract the component and port name parts.
Note that the format allows specifying a slot here, but this is currently not
supported and illegal in MUSCLE 3.

Settings
--------

The settings section contains settings for the simulation to run with. In YAML,
this is a dictionary that maps a setting name (a
:class:`ymmsl.Reference`) to its value. Parameter values may be strings,
integers, floating point numbers, lists of floating point numbers (vectors), or
lists of lists of floating point numbers (arrays).

.. code-block:: yaml
    :caption: ``Settings example``

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
one-dimensional domain, which is named domain, has a length and width of 1.0,
and a grid spacing of 0.01. The macro model has a time step of 10 and a total
run time of 1000 (so it will run for 100 steps), while the micro model has a
time step of 0.01 and a total run time of 1.0. Furthermore, there are some other
model settings, a boolean switch that enables interpolation, a string to select
the interpolation method, and a 2D array specifying a kernel of some kind.

On the Python side, this will be turned into a :class:`ymmsl.Settings` object,
which acts much like a Python dictionary. So for instance, if you have a
:class:`ymmsl.Configuration` object named ``config`` which was loaded from a
file containing the above ``settings`` section, then you could write:

.. code-block:: python

    grid_dx = config.settings['domain.grain']
    kernel = config.settings['kernel']

to obtain a floating point value of 0.1 in ``grid_dx`` and a list of lists
``[[0.8, 0.2], [0.2, 0.8]]`` in ``kernel``.


Examples
--------

All the classes mentioned here are normal Python classes. They have constructors
which you can use to create instances, and their attributes can be changed as
needed.

Here are a few examples:

.. code-block:: python
    :caption: Creating a Configuration and saving it

    import ymmsl

    components = [
        ymmsl.Component('macro', 'my.macro_model'),
        ymmsl.Component('micro', 'my.micro_model')]

    conduits = [
        ymmsl.Conduit('macro.out', 'micro.in'),
        ymmsl.Conduit('micro.out', 'macro.in')]

    model = ymmsl.Model('my_model', components, conduits)

    config = ymmsl.Configuration(model)

    with open('out.ymmsl', 'w') as f:
        ymmsl.save(config, f)

    # Will produce:
    # ymmsl_version: v0.1
    # model:
    #   name: my_model
    #   components:
    #     macro: my.macro_model
    #     micro: my.micro_model
    #   conduits:
    #     macro.out: micro.in
    #     micro.out: macro.in


.. code-block:: python
    :caption: Creating a Configuration and saving it (downside-up version)

    import ymmsl

    config = ymmsl.Configuration(ymmsl.Model('my_model', [], []))

    config.model.components.append(
        ymmsl.Component('macro', 'my.macro_model'))
    config.model.components.append(
        ymmsl.Component('micro', 'my.micro_model'))

    config.model.conduits.append(ymmsl.Conduit('macro.out', 'micro.in'))
    config.model.conduits.append(ymmsl.Conduit('micro.out', 'macro.in'))

    with open('out.ymmsl', 'w') as f:
        ymmsl.save(config, f)

    # Will produce:
    # ymmsl_version: v0.1
    # model:
    #   name: my_model
    #   components:
    #     macro: my.macro_model
    #     micro: my.micro_model
    #   conduits:
    #     macro.out: micro.in
    #     micro.out: macro.in


.. code-block:: python
    :caption: Adding or changing a setting

    import ymmsl

    with open('example.ymmsl', 'r') as f:
        config = ymmsl.load(f)

    config.settings['d'] = 0.12

    with open('out.ymmsl', 'w') as f:
        ymmsl.save(config, f)


For more details about these classes and what you can do with them, we refer to
the API documentation.

