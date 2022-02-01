.. _installation:

Installation
============

The most straightforward way to install ``yt_astro_analysis`` is to
first `install yt <https://github.com/yt-project/yt#installation>`__.
This will take care of all ``yt_astro_analysis`` dependencies. After
that, ``yt_astro_analysis`` can be installed with pip:

.. code-block:: bash

   $ pip install yt-astro-analysis

If you use ``conda`` to manage packages, you can install ``yt_astro_analysis``
from conda-forge:

.. code-block:: bash

   $ conda install -c conda-forge yt-astro-analysis

Note, the package name is spelled with hyphens (``yt-astro-analysis``)
when installing from pip or conda. With pip, the package name can be
spelled with either hyphens or underscores, but with conda it must
always be hyphens.

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

.. note:: As of ``yt_astro_analysis`` version 1.1, ``yt_astro_analysis``
   runs with the most recent version of ``rockstar-galaxies``. Older
   versions of ``rockstar`` will not work.

Rockstar support requires ``yt_astro_analysis`` to be installed from source.
Before that, the ``rockstar-galaxies`` code must also be installed from source
and the installation path then provided to ``yt_astro_analysis``. Two
recommended repositories exist for installing ``rockstar-galaxies``,
`this one <https://bitbucket.org/pbehroozi/rockstar-galaxies/>`__, by the
original author, Peter Behroozi, and
`this one <https://bitbucket.org/jwise77/rockstar-galaxies>`__, maintained by
John Wise.

.. warning:: If using `Peter Behroozi's repository
   <https://bitbucket.org/pbehroozi/rockstar-galaxies/>`__, the following
   command must be issued after loading the resulting halo catalog in ``yt``:

.. code-block:: python

   ds = yt.load(...)
   ds.parameters["format_revision"] = 2

To install ``rockstar-galaxies``, do the following:

.. code-block:: bash

   $ git clone https://bitbucket.org/jwise77/rockstar-galaxies
   $ cd rockstar-galaxies
   $ make lib

Then, go into the ``yt_astro_analysis`` source directory and add a file called
"rockstar.cfg" with the path the ``rockstar-galaxies`` repo you just cloned.
Then, install ``yt_astro_analysis``.

.. code-block:: bash

   $ cd yt_astro_analysis
   $ echo <path_to_rockstar> > rockstar.cfg
   $ pip install -e .

Finally, you'll need to make sure that the location of ``librockstar-galaxies.so``
is in your LD_LIBRARY_PATH.

.. code-block:: bash

   $ export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:<path_to_rockstar>
