Upgrading to v0.2
-----------------

Since ymmsl-python 0.15.0, a new version v0.2 of the yMMSL format has been available.
While the main concepts have not changed relative to v0.1, a number of incompatible
changes have been made to enable new features. To use the new format, existing yMMSL
files and existing Python code will have to be upgraded. This page explains how to do
this.

Upgrading yMMSL files
`````````````````````

As of ymmsl-python 0.15.0, the package comes with a ``ymmsl`` utility command that can
be used to convert yMMSL files from v0.1 to v0.2. Its ``convert`` subcommand will
convert files:

.. code-block:: bash
   :caption: Upgrading a yMMSL file, result as a new file

   ymmsl convert model.ymmsl model_v0.2.ymmsl

Or, to replace the existing file:

.. code-block:: bash
   :caption: Upgrading a yMMSL file in place

   ymmsl convert model.ymmsl

A backup called ``model.ymmsl.bak`` will be made automatically in this case, if it did
not exist already. To see more options, run ``ymmsl convert --help``.

While the converter helps, it does have some technical limitations, it cannot add
information that's not present in the source file, and cannot automatically use the new
features in v0.2. Some manual work may therefore be required to fully translate from
v0.1 to v0.2.

For some of these issues, warnings will be printed when the conversion is done. Please
read these carefully, and edit the new file accordingly to ensure that your models
continue to work correctly. Not everything can be detected however, so please read the
below carefully.

Comments, descriptions, and supported settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

YAML supports comments, which are lines or parts of lines that start with a ``#``. It's
good practice to add some to your v0.1 yMMSL file to explain what is what, and hopefully
your yMMSL files have them. Unfortunately, reading comments and figuring out what they
apply to is not easy, and is mostly unsupported by the PyYAML library that is used in
Python to read YAML files.

In yMMSL v0.2, there are therefore ``description`` fields in various places, including
at the top level (to describe the file), and for models, components, and programs. The
newly added ``supported_settings`` feature also allows adding a description.

Because of the constraints on reading YAML comments, they won't be converted
automatically. Instead, the new v0.2 file will contain ``description`` keys in various
places with a placeholder text, and you'll have to move over the comments manually. If
there were no comments, then this is a good time to add some descriptions while you're
at it.

Split models
^^^^^^^^^^^^

In yMMSL v0.1, it was possible to split the definition of a model across multiple files.
This made it possible for example to have optional extensions to the model, in the form
of more components and conduits. Unfortunately, this also makes it more difficult to
understand the structure of the model, as the file you're looking at may contain parts
that end up not actually used or working differently when overwritten by parts from
another file.

In yMMSL v0.2, merging models from multiple files is therefore no longer allowed, and
new features have been added that make it possible to support model variations in a
cleaner manner, such as the new import mechanism and ``custom_implementations``.
Switching to them has to be done manually however, since the converter only reads one
file at a time, and does not understand your model conceptually. It's still a good idea
to run the converter on your files however, as you'll be able to save time by
copy-pasting many of the details from the converter output.

Component ports
^^^^^^^^^^^^^^^

In yMMSL v0.1, components could optionally have ports. In yMMSL v0.2, components are now
required to have a ports description. If no ports description is given in the source
file, then the converter will check to see if any conduits connect to the component, and
generate a ports description based on that. This may give incorrect results!

For example, the component may have optional ports that are present but not currently,
connected, or there may be more conduits in another file, and in any case the converter
cannot deduce which operator the port is associated with from the conduits. By default,
it will mark receiving ports as ``F_INIT`` and sending ports as ``O_F``, but this may
well be incorrect for your model. A warning will be generated about this, and you should
check the result carefully and fix it where needed.

Upgrading Python code
`````````````````````

MUSCLE3 models written in Python use two classes from the ``ymmsl`` package
(``Operator`` and optionally ``Settings``), neither of which have changed and both of
which remain available via a backwards compatibility definition. You can change your
code to import them from ``ymmsl.v0_2`` instead, but it's not necessary.

If you have other Python code that uses the ``ymmsl`` package, then the upgrade from
version 0.14.0 to 0.15.0 will break your code. Unfortunately, this was necessary to
support multiple versions without causing confusion. Fortunately, yMMSL v0.1 is still
supported and a quick fix is available for the near term. Eventually, you'll want to
upgrade to the new version however, which is a bit more work.

Quick fix
^^^^^^^^^

In ``ymmsl`` before 0.15.0, all classes and functions are imported from ``ymmsl``
directly. In ``ymmsl`` 0.15.0, :func:`ymmsl.load`, :func:`ymmsl.dump` and
:func:`ymmsl.save` are still imported from ``ymmsl``, but the classes representing the
contents of a v0.1 yMMSL file are now imported from ``ymmsl.v0_1``. If you update your
import statements accordingly, then your code will work with newer versions of the
library (but not anymore with older ones, so set a version constraint accordingly). Of
course, you'll only be able to read and write v0.1 yMMSL files.

If you use Python type annotations, then you'll note that the return type of
:func:`ymmsl.load` has changed from ``ymmsl.PartialConfiguration`` (now
:class:`ymmsl.v0_1.PartialConfiguration`) to :class:`ymmsl.Document`. This is a parent
class to both :class:`ymmsl.v0_1.PartialConfiguration` and
:class:`ymmsl.v0_2.Configuration`, and the function will return either depending on the
version of the input file.

Since your code does not support v0.2 yet, you may want to use

.. code-block:: python

    ymmsl.load_as(ymmsl.v0_1.PartialConfiguration, infile)

instead. This always returns a :class:`ymmsl.v0_1.PartialConfiguration`, and raises a
:class:`ymmsl.DowngradeError` if it is asked to load a newer file.


Supporting v0.2
^^^^^^^^^^^^^^^

To upgrade your code to support yMMSL v0.2, you'll have to switch to the v0_2 API in
``ymmsl.v0_2``. Besides updating import statements, some larger changes are needed
because the data format has changed somewhat. The overall structure is still similar
however, so this will likely not be a complete overhaul.

In many places, some new attributes have been added to classes, sometimes in the middle
of other ones, and we've taken the opportunity to rearrange attributes that had ended up
in a less-than-logical order for reasons of backwards compatibility. So when upgrading,
you should carefully check which arguments you are passing when creating an object, and
in which order, and make sure they match the new definition.

Additionally, in a few places (e.g. ``Model.components``, ``Configuration.programs``),
attributes are now dictionaries mapping names to objects, rather than lists of objects.
This matches the YAML more directly, but most importantly is often more convenient in
Python too.

Most classes have kept their name and overall role, but there is one exception.
:class:`ymmsl.v0_1.Implementation` is used to describe how to start a program in yMMSL
v0.1. In v0.2, this is now done using :class:`ymmsl.v0_2.Program`, which you'll find to
otherwise be very similar. Likewise, ``Configuration.implementations`` is now
``Configuration.programs``.

There exists a :class:`ymmsl.v0_2.Implementation`, which is a base class of ``Program``
and :class:`ymmsl.v0_2.Model` and contains common attributes. In yMMSL v0.2, both
programs and models can be used as implementations of components, so this makes sense,
but it is a potential source of confusion to be aware of. Use
:class:`ymmsl.v0_2.Program` instead.
