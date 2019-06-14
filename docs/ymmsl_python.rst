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

Here is an example of loading a yMMSL file:

.. code-block:: python

   import ymmsl

   with open('example.ymmsl', 'r') as f:
       doc = ymmsl.load(f)

This makes ``doc`` an object of type :class:`ymmsl.YmmslDocument`, which is the
top-level class describing a yMMSL document.

If the file is valid YAML, but not recognized as a yMMSL file, the library will
raise a :class:`ymmsl.RecognitionError` with a message describing in detail what
is wrong, so that you can easily fix the file.

Note that the ``load()`` function uses the safe loading functionality of the
underlying YAML library, so you can safely load files from untrusted sources.

Writing yMMSL files
-------------------

To write a yMMSL file with the contents of a :class:`ymmsl.YmmslDocument`, we
use ``ymmsl.save``:

.. code-block:: python

   import ymmsl

   doc = ymmsl.Ymmsl('v0.1', [], [])

   with open('out.ymmsl', 'w') as f:
       ymmsl.save(doc, f)

This produces a text file with a YAML description of the given object. If you
want to have the YAML as a string, use ``ymmsl.dump(doc)`` instead.

Working with yMMSL objects
--------------------------

Generally speaking, the object model used by the ``ymmsl`` library follows the
structure of the YAML document, but there are a few places where some syntactic
sugar has been added to make the files easier to read and write by hand.

So, for instance, assuming that you have a variable ``doc`` read from
``example.ymmsl`` as described above, the version of the file will be available
as ``doc.version``, the ``model`` part as ``doc.model`` and the
``settings`` part as ``doc.settings``. Note that both the model and the
settings part are optional, so you'll want to check that they're not ``None``
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

On the settings side, the settings are described as a dictionary
(or mapping, in YAML-speak) in the YAML file, and they are a
:class:`ymmsl.Settings` object on the Python side, which is a custom class that
behaves like a dictionary.

These are all ordinary Python objects, so you can modify the document by
creating new objects and assigning them to attributes of other objects, or
create a document from scratch just by instantiating
:class:`ymmsl.YmmslDocument`.

For details about these classes and what you can do with them, we refer to the
API documentation.
