Python API
==========

The yMMSL YAML format is supported by the ymmsl-python library, whose
documentation you are currently reading. This library lets you read and write
yMMSL files, and manipulate their contents using an object-based Python API.

Installation
------------

ymmsl-python is on PyPI, so you can install it using Pip:

.. code-block:: bash

   pip install ymmsl

or you can add it to your dependencies as usual.

Reading yMMSL files
-------------------

yMMSL files are YAML files, so we use a YAML library to read them. Python has
two YAML libraries, the original PyYAML which has security issues and is not
supported very actively, and the fork ruamel.yaml, which is better security-wise
and more actively maintained. We therefore use ruamel.yaml. It is a dependency
of the ``ymmsl`` package, so it should have been installed automatically, but
it's a good idea to add it to your dependencies explicitly, since you'll be
using it explicitly to load yMMSL files.

Here is an example of loading a yMMSL file:

.. code-block:: python

   import ymmsl
   from ruamel import yaml

   with open('example.ymmsl', 'r') as f:
       doc = yaml.load(f, Loader=ymmsl.loader)

This makes ``doc`` an object of type :class:`ymmsl.YmmslDocument`, which is the
top-level class describing a yMMSL document. Note that this is almost completely
identical to the way you would normally load a YAML document, the only
difference is that the ``Loader`` argument is set to ``ymms.loader``. This has a
big effect however, since the value returned from ``yaml.load`` is now not a
dictionary containing more dictionaries, but an object of a class defined by the
``ymmsl`` library.

If the file is valid YAML, but not recognized as a yMMSL file, the library will
raise a :class:`ymmsl.RecognitionError` with a message describing in detail what
is wrong, so that you can easily fix the file.

Note that you can use ``yaml.safe_load`` if you want, but since
``ymmsl.loader`` is a SafeLoader, the input will always be loaded safely
whichever function you use.

Writing yMMSL files
-------------------

To write a yMMSL file with the contents of a :class:`ymmsl.YmmslDocument`, we
use ``yaml.dump``:

.. code-block:: python

   import ymmsl
   from ruamel import yaml

   with open('out.ymmsl', 'w') as f:
       yaml.dump(doc, Dumper=ymmsl.dumper)

This is again the normal way of writing a YAML file, except this time with a
custom dumper that knows how to convert objects from the ``ymmsl`` library to
easy-to-read YAML text.

Working with yMMSL objects
--------------------------

Generally speaking, the object model used by the ``ymmsl`` library follows the
structure of the YAML document, but there are a few places where some syntactic
sugar has been added to make the files easier to read and write by hand.

So, for instance, assuming that you have a variable ``doc`` read from
``example.ymmsl`` as described above, the version of the file will be available
as ``doc.version``, the ``experiment`` part as ``doc.experiment`` and the
``simulation`` part as ``doc.simulation``. Note that both the simulation and the
experiment part are optional, so you'll want to check that they're not ``None``
before doing anything with them.

You will find the first bit of syntactic sugar in
``doc.simulation.compute_elements``. This is a list of compute elements, each of
which have attributes ``name`` and ``implementation`` containing, respectively,
an :class:`ymmsl.Identifier` and a :class:`ymmsl.Reference`. The list is
automatically converted from the dictionary when reading, and converted back on
writing.

Note that an :class:`ymmsl.Identifier` is almost a string, but the class ensures
that the string is a valid identifier, and :class:`ymmsl.Reference` does the
same, and also offers access to individual parts of the reference, which comes
in handy when resolving them.  The other bit of syntactic sugar in the
experiment part is in ``doc.simulation.conduits``, which is a list of
:class:`ymmsl.Conduit` objects (see the API documentation).

On the :class:`ymmsl.Experiment` side, things work similarly, with the model to
be run being reached via ``doc.experiment.model``, which is an object of class
:class:`ymmsl.Reference`. ``doc.experiment.scales`` is a list of
:class:`ymmsl.ScaleSettings` objects, and ``doc.experiment.parameter_values`` a
list of :class:`ymmsl.Setting` objects.

These are all ordinary Python objects, so you can modify the document by
creating new objects and assigning them to attributes of other objects, or
create a document from scratch just by instantiating
:class:`ymmsl.YmmslDocument`.

For details about these classes and what you can do with them, we refer to the
API documentation.
