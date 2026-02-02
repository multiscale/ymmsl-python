Basic usage
===========

A yMMSL file is a YAML file that looks approximately like this:

.. literalinclude:: example_model.ymmsl
    :caption: ``docs/example_model.ymmsl``
    :language: yaml

yMMSL files can contain descriptions of multiscale and multiphysics coupled models (as
above), settings to configure the models, programs to use to run them, and other
information needed to run a simulation like compute resources to use and when to
checkpoint.

The yMMSL YAML format is supported by the ymmsl-python library, whose documentation you
are currently reading. This library lets you read and write yMMSL files, and manipulate
their contents using an object-based Python API.

Installation
------------

ymmsl-python is on PyPI, so you can install it using Pip:

.. code-block:: bash

   pip install ymmsl

or you can add it to your dependencies as usual, e.g. in your ``setup.py`` or your
``pyproject.toml``, depending on how you've set up your project.

Reading yMMSL files
-------------------

Here is an example of loading a yMMSL file:

.. code-block:: python

   from pathlib import Path
   import ymmsl

   config = ymmsl.load(Path('docs/example_model.ymmsl'))

This makes ``config`` an object of type :class:`.ymmsl.v0_2.Configuration`, which is the
top-level class describing a yMMSL document. More on these objects in the next section.
The :func:`ymmsl.load` function can also load from an open file or from a string
containing YAML data.

If the file is not recognized as a yMMSL file, the library will raise a
:class:`yatiml.RecognitionError` with a message describing in detail what is wrong, so
that you can easily fix the file.

Note that the :func:`ymmsl.load` function uses the safe loading functionality of the
underlying YAML library, so that you can safely load files from untrusted sources.

Writing yMMSL files
-------------------

To write a yMMSL file with the contents of a :class:`.ymmsl.v0_2.Configuration`, we use
``ymmsl.save``:

.. code-block:: python

   from pathlib import Path
   from ymmsl.v0_2 import Component, Configuration, Model, Ports, Settings
   import ymmsl

   model = Model(
       'example_model', components=[Component('macro', Ports(), 'The macro model')])
   settings = Settings({'example_parameter': 42})
   config = Configuration(model, settings)

   ymmsl.save(config, Path('out.ymmsl'))

Here, we create a model named ``example_model``, containing a single component named
``macro``, and no conduits. For the settings, we create a Settings object, which is a
container for a dictionary of settings.

Finally, we combine the model and the settings into a :class:`.ymmsl.v0_2.Configuration`
object, which we then save to a file. If you want to have the YAML as a string, use
:func:`ymmsl.dump` instead.

As the format develops over time, files are required to carry a version, in this case
v0.2, which is currently the latest version of yMMSL.

When you read in a yMMSL file as described above, you get a collection of Python
objects describing its contents. The next section explains how those work.
