Creating yMMSL from Python
--------------------------

yMMSL files are YAML files, and yMMSL is usually written in YAML. In fact, even if you
want to create a yMMSL configuration in Python, it's often convenient to just embed a
string containing a YAML description and converting it to objects using
:func:`ymmsl.load`.

However, all the classes mentioned here are normal Python classes. They have
constructors which you can use to create instances, and their attributes can be changed
as needed.

This example shows creating a yMMSL configuration in Python and saving it to a file.

.. literalinclude:: from_python.py
   :caption: Creating a Configuration and saving it (``docs/from_python.py``)
   :language: python

This will output:

.. literalinclude:: from_python.ymmsl
   :caption: Output of ``from_python.py`` (``docs/from_python.ymmsl``)
   :language: yaml


Another use case is loading a yMMSL file and modifying it:

.. literalinclude:: load_modify_save.py
   :caption: Loading, modifying, and saving a yMMSL file (``docs/load_modify_save.py``)
   :language: python

For more details about these classes and what you can do with them, we refer to the API
documentation.
