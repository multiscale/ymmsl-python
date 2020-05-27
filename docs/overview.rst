Overview
========

A yMMSL file is a YAML file that looks approximately like this:

.. literalinclude:: example.ymmsl
    :caption: ``docs/example.ymmsl``
    :language: yaml

This file describes a macro-micro coupled simulation model with time-scale
separation and domain overlap. It describes both the model itself and an
experiment to be run with this model, and contains the minimal information
needed for MUSCLE 3 to be able to coordinate model execution. We'll go into
more detail on this file in a moment.

The yMMSL YAML format is supported by the ymmsl-python library, whose
documentation you are currently reading. This library lets you read and write
yMMSL files, and manipulate their contents using an object-based Python API.

Installation
------------

ymmsl-python is on PyPI, so you can install it using Pip:

.. code-block:: bash

   pip install ymmsl

or you can add it to your dependencies as usual, e.g. in your ``setup.py`` or
your ``requirements.txt``, depending on how you've set up your project.

Reading yMMSL files
-------------------

Here is an example of loading a yMMSL file:

.. code-block:: python

   import ymmsl

   with open('example.ymmsl', 'r') as f:
       config = ymmsl.load(f)

This makes ``config`` an object of type :class:`ymmsl.Configuration`, which is
the top-level class describing a yMMSL document. More on these objects in the
next section.

If the file is valid YAML, but not recognized as a yMMSL file, the library will
raise a :class:`ymmsl.RecognitionError` with a message describing in detail what
is wrong, so that you can easily fix the file.

Note that the ``load()`` function uses the safe loading functionality of the
underlying YAML library, so you can safely load files from untrusted sources.

Writing yMMSL files
-------------------

To write a yMMSL file with the contents of a :class:`ymmsl.Configuration`, we
use ``ymmsl.save``:

.. code-block:: python

   from ymmsl import Component, Configuration, Model, Settings

   model = Model('test_model', [Component('macro')])
   settings = Settings(OrderedDict([('test_parameter', 42)]))
   config = Configuration(model, settings)

   with open('out.ymmsl', 'w') as f:
       ymmsl.save(config, f)

Here, we create a model named ``test_model``, containing a single component
named ``macro``, and no conduits. For the settings, we create a Settings
object, which is a container for an ordered dictionary of settings. Note that
normal Python dictionaries are unordered, which is why YAML documents saved
from Python are often in a random order and hard to read. We avoid that problem
in yMMSL by using an ``OrderedDict`` here. You have to pass it a list of
tuples, because using dictionary syntax with curly brackets will lose the
ordering.

Finally, we combine the model and the settings into a
:class:`yammsl.Configuration` object, which we then save to a file. If you
want to have the YAML as a string, use :func:`ymmsl.dump(doc)` instead.

As the format may develop over time, files are required to carry a version, in
this case v0.1, which is currently the only version of yMMSL.

When you read in a yMMSL file as described above, you get a collection of Python
objects describing its contents. The next section explains how those work.

