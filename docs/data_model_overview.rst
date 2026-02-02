Data model overview
===================

As shown on the previous page, the ``ymmsl-python`` library converts yMMSL from
YAML to Python objects and back. Here, we dive into this a bit deeper and see
how those Python objects can be used.

This section gives an overview of the data model, but its goal is not to provide an
introduction to the concepts or an explanation of how they're used. Instead, it provides
an overview of what is where. If you're new to yMMSL and MUSCLE3, then you should read
the `MUSCLE3 documentation`_ first. There, you'll find a from-scratch tutorial that will
help you get started.

yMMSL files can be used to describe four kinds of things:

1. Models

   A model description describes the components a coupled model consists of and how
   they are connected together so that they can exchange information while running. This
   is an abstract description, it may specify programs to run but not how to start or
   configure them.

2. Scenarios

   Settings configure a model to match a specific scenario. This entails setting
   parameters and other model options, and even replacing or filling in implementations
   for some of the components if the model was designed with a flexible structure.

3. Programs

   To actually run a simulation on some kind of computer, programs need to be available
   that do the calculations. We need to describe how to start them on the computer we
   want to run on, which depends on how they were installed there. This too can be
   described in yMMSL.

4. Runs

   Finally, additional technical information on how to run the simulation can be
   specified. This includes resources to use for each component (threads or MPI
   processes), and configuration of checkpointing and resuming.


These are explained in more detail in the following sections.

.. _MUSCLE3 documentation: https://muscle3.readthedocs.io
