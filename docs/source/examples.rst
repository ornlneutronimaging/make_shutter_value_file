********
Examples
********

This page list a few cases

.. code-block:: html

    > python make_shutter_value_file --default_mode True --verbose
    1e-6	2.5e-3	5	10.24
    2.9e-3	5.8e-3	6	10.24
    6.2e-3	15.9e-3	7	10.24

    > python make_shutter_value_file --default_mode True

In both cases, a file *ShutterValue.txt* was created in the current folder (./)

.. code-block:: html

    > python make_shutter_value_file --resonance_mode True --verbose

