Functionality
-------------

Besides loading and saving yMMSL files and converting between YAML and Python objects,
the ``ymmsl`` package offers some related functionality that is briefly described here.

Format conversion
`````````````````

There are currently two versions of the yMMSL file format: v0.1 and v0.2. Both are
supported by this library, with the corresponding Python classes being available from
``ymmsl.v0_1`` and ``ymmsl.v0_2`` respectively.

When you use :func:`ymmsl.load` to load a yMMSL file, you'll get a
:class:`ymmsl.Document` object in return. This is a base class for all yMMSL documents,
regardless of version. If the file is a v0.1 file, then the result will be an instance
of :class:`.ymmsl.v0_1.Configuration`, if it is a v0.2 file then it will be an instance
of :class:`.ymmsl.v0_2.Configuration`.

The :func:`ymmsl.convert_to` function can be used to convert a v0.1 Configuration to a
v0.2 Configuration, but not the other way around. In other words, only upgrades are
supported. To use it, tell it what you want and give it what you have:

.. code-block:: python
    :caption: Conversion example

    import ymmsl

    v0_1_config = ymmsl.v0_1.Configuration(...)
    v0_2_config = ymmsl.convert_to(ymmsl.v0_2.Configuration, v0_1_config)

Note that we're passing the type we want to have as the first argument, not an object.

Auto-convert on load
^^^^^^^^^^^^^^^^^^^^

When implementing tools, you may want to auto-convert any input files to the latest
version and write your code against that, so that you don't have to support multiple
versions. This can be done using :func:`ymmsl.load_as`:

.. code-block:: python
    :caption: Automatic conversion on load

    from pathlib import Path
    import ymmsl

    v0_2_config = ymmsl.load_as(ymmsl.v0_2.Configuration, Path('input.ymmsl'))

Now ``v0_2_config`` will be an instance of :class:`.ymmsl.v0_2.Configuration` even if
the input file is a version 0.1 file.

Merging
```````

Because descriptions of models, scenarios, programs and runs are often made at different
times and sometimes by different people, and because different combinations of them are
needed to do different things, it's often convenient to split them across multiple yMMSL
files. A particular configuration then needs to be assembled from multiple files.

If you have a list of files that need to be merged (as MUSCLE3 does), then you can use
the :func:`ymmsl.v0_2.Configuration.update` function to merge them. To get the same
behaviour as MUSCLE3, start with the first Configuration in the list and successively
update it with the remaining ones.

Note that the rules for how files are combined have changed between the versions. For
example, in yMMSL v0.1 it was legal to have a model description in one yMMSL file and
update it with another description of the same model (with the same name), adding
components and conduits. This is no longer allowed in v0.2, where the import
functionality must be used instead.

Checking consistency
````````````````````

yMMSL files are full of cross-references, from conduits to ports on components, from
components to implementations, from settings to supported settings, and more. For a
configuration to be able to be run, these all need to be correct. The
:func:`ymmsl.v0_2.Configuration.check_consistent` function performs a variety of checks
to ensure that everything is consistent. It will raise a ``RuntimeError`` listing any
issues found in a user-friendly format.

Resolving imports
`````````````````

Imports may be used to obtain models and programs from other yMMSL files for use in the
present one. Loading a yMMSL file with imports productes a ``Configuration`` object
containing those import statements at ``config.imports``, as a list of
:class:`ymmsl.v0_2.ImportStatement` objects.

To get the imported objects, these imports must be resolved, which can be done through
the :func:`ymmsl.v0_2.resolve` function. This takes the name of the module corresponding
to a ``Configuration`` (which is the file name without the ``.ymmsl`` extension, wrapped
in a :class:`ymmsl.v0_2.Reference`) and the configuration itself.

It updates that configuration in place, renaming any local models and programs to their
absolute name by prefixing them with the given module name, then imports the
implementations described in the import statements and adds them to the model under
their full name. For example, an import statement

.. code-block::

   from a.b.c import implementation x

will result in a new model or program (depending on what it is) named ``a.b.c.x`` being
added to the ``programs`` or ``models`` section. References between components, models
and programs will be updated accordingly.

Imports are resolved recursively, so any implementations needed by an imported model
will be imported and added as well. As a result, a single import statement may cause a
whole collection of models and programs to be added.

After the imports have been resolved, the import statements are removed from the
configuration in order to avoid confusion.
