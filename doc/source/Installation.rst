.. _installation:

Installation
============

The most straightforward way to install ``yt_astro_analysis`` is to
first `install yt <https://github.com/yt-project/yt#installation>`__.
This will take care of all ``yt_astro_analysis`` dependencies. After
that, ``yt_astro_analysis`` can be installed with pip:

.. code-block:: bash

   $ pip install yt_astro_analysis

If you use ``conda`` to manage packages, you can install ``yt_astro_analysis``
from conda-forge:

.. code-block:: bash

   $ conda install -c conda-forge yt_astro_analysis
   
Installing from source
----------------------

To install from source, it is still recommended to first install ``yt``
in the manner described above. Then, clone the git repository and install
like this:

.. code-block:: bash

   $ git clone https://github.com/yt-project/yt_astro_analysis
   $ cd yt_astro_analysis
   $ pip install -e .

.. _installation-rockstar:

Installing with Rockstar support
--------------------------------

Rockstar support requires ``yt_astro_analysis`` to be installed from source.
In order to run the Rockstar halo finder from within ``yt_astro_analysis``,
you will need to install the `yt-project's fork of Rockstar
<https://github.com/yt-project/rockstar>`__ and then provide this path to
``yt_astro_analysis``.  To install Rockstar, do the following:

.. code-block:: bash

   $ git clone https://github.com/yt-project/rockstar
   $ cd rockstar
   $ make lib

Then, go into the ``yt_astro_analysis`` source directory and add a file called
"rockstar.cfg" with the path the Rockstar repo you just cloned.  Then, install
``yt_astro_analysis``.

.. code-block:: bash

   $ cd yt_astro_analysis
   $ echo <path_to_rockstar> > rockstar.cfg
   $ pip install -e .

Finally, you'll need to make sure that the location of ``librockstar.so`` is in
your LD_LIBRARY_PATH.

.. code-block:: bash

   $ export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:<path_to_rockstar>
