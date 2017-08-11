.. _installation:

Installation
============

To install ``yt_astro_analysis``, you will first need to 
`install yt <https://github.com/yt-project/yt#installation>`__.  Then, clone
the git repository and install like this:

.. code-block:: bash

   $ git clone https://github.com/yt-project/yt_astro_analysis
   $ cd yt_astro_analysis
   $ pip install -e .

.. _installation-rockstar:

Installing with Rockstar support
--------------------------------

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
