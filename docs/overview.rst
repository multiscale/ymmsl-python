Overview
========

A yMMSL file is a YAML file that looks approximately like this:

.. literalinclude:: example.ymmsl
    :caption: ``docs/example.ymmsl``
    :language: yaml

This file describes a macro-micro coupled simulation model with time-scale
separation and domain overlap. It describes both the model itself and an
experiment to be run with this model, and contains the minimal information
needed for MUSCLE 3 to be able to coordinate model execution.

As the format may develop over time, files are required to carry a version, in
this case v0.1, which is currently the only version of yMMSL.

Models
------

The ``model`` section describes the simulation model. It has a name, which
is an :class:`Identifier` (see below), a list of compute elements, and conduits
between them. Compute elements are submodels, scale bridges, proxies, and any
other program that makes up the coupled simulation. In this case there are two,
one named ``macro``, and one named ``micro`` (also :class:`Identifier` s). For
each compute element, a :class:`Reference` to an implementation is given. This
information is useful for launchers or pilot jobs, who can then look up how to
run the corresponding binary in their internal configuration.

Conduits connect compute elements together. They lead from a port on a compute
element to a port on another compute element. In this model, port ``state_out``
on compute element ``macro`` is connected to port ``init_in`` on compute element
``micro``. Both sides of the description here are :class:`Reference` s.

Settings
--------

The settings section contains a set of parameter settings for the model.
Parameter values may be strings, integers, floating point numbers, lists of
floating point numbers (vectors), or lists of lists of floating point numbers
(arrays).

In this example, the two submodels share a one-dimensional domain, which is
named domain, has a length of 1.0, and a grid spacing of 0.01. The macro model
has a time step of 10 and a total run time of 1000 (so it will run for 100
steps), while the micro model has a time step of 0.01 and a total run time of
1.0. Furthermore, there are some model parameters, shared parameters ``k`` and
``interpolation_method``, and a parameter ``d`` that is specific to the
micromodel.

Identifiers and References
--------------------------

The classes :class:`Identifier` and :class:`Reference` play an important role in
yMMSL. An identifier uniquely identifies an object, like a simulation model or a
compute element. It is a string containing letters, digits, and/or underscores
which must start with a letter or underscore, and may not be empty. Identifiers
starting with an underscore are reserved for use by the software (e.g. MUSCLE
3), and may not be used when describing models.

A :class:`Reference` refers to some object by name. It consists of an
:class:`Identifier`, optionally followed by a period and another identifier, or
by an integer in square brackets, or a sequence of these. Some examples of
syntactically valid references are:

.. code-block:: none

  macro_micro_model
  macro_micro_model.macro
  macro.final_out[2]
  macro_micro_model.macro.final_out[1]
  x[2].y.z[2][4].a

Resolving references is left to the application, so to know how to reference a
particular object, you should consult the documentation for the software you are
using.
