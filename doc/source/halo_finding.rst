.. _halo_catalog_finding:

Halo Finding
============

Halo finding and analysis are combined into a single framework called the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`.

If you already have a halo catalog, either produced by one of the methods
below or in a format described in :ref:`yt:halo-catalog-data`, and want to
perform further analysis, skip to :ref:`halo_catalog_analysis`.

Three halo finding methods exist within yt.  These are:

* :ref:`fof_finding`: a basic friend-of-friends algorithm
  (e.g. `Efstathiou et al. 1985
  <http://adsabs.harvard.edu/abs/1985ApJS...57..241E>`__)
* :ref:`hop_finding`: `Eisenstein and Hut (1998)
  <http://adsabs.harvard.edu/abs/1998ApJ...498..137E>`__.
* :ref:`rockstar_finding`: a 6D phase-space halo finder that scales well,
  does substructure finding, and will automatically calculate halo
  ancestor/descendent links for merger trees (`Behroozi et al.
  2011 <http://adsabs.harvard.edu/abs/2011arXiv1110.4372B>`__).

Halo finding is performed through the creation of a
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`
object.  The dataset or datasets on which halo finding is to be performed should
be loaded and given to the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`
along with the ``finder_method`` keyword to specify the method to be
used.

.. code-block:: python

   import yt
   from yt.extensions.astro_analysis.halo_analysis import HaloCatalog

   data_ds = yt.load("Enzo_64/RD0006/RedshiftOutput0006")
   hc = HaloCatalog(data_ds=data_ds, finder_method="hop")
   hc.create()

.. _halo_finding_time_series:

Halo Finding on Multiple Snapshots
----------------------------------

To run halo finding on a series of snapshots, provide a
:class:`~yt.data_objects.time_series.DatasetSeries` or
:class:`~yt.data_objects.time_series.SimulationTimeSeries` to the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`.
See :ref:`time-series-analysis` and :ref:`analyzing-an-entire-simulation` for
more information on creating these. All three halo finders can be run this way.
If you want to make merger trees with Rockstar halo catalogs, you must run
Rockstar in this way.

.. code-block:: python

   import yt
   from yt.extensions.astro_analysis.halo_analysis import HaloCatalog

   my_sim = yt.load_simulation("enzo_tiny_cosmology/32Mpc_32.enzo", "Enzo")
   my_sim.get_time_series()
   hc = HaloCatalog(data_ds=my_sim, finder_method="hop")
   hc.create()

Halo Finder Options
-------------------

The available ``finder_method`` options are "fof", "hop", or
"rockstar". Each of these methods has their own set of keyword
arguments to control functionality. These can specified in the form
of a dictionary using the ``finder_kwargs`` keyword.

.. code-block:: python

   import yt
   from yt.extensions.astro_analysis.halo_analysis import HaloCatalog

   data_ds = yt.load("Enzo_64/RD0006/RedshiftOutput0006")
   hc = HaloCatalog(
       data_ds=data_ds,
       finder_method="fof",
       finder_kwargs={"ptype": "stars", "padding": 0.02},
   )
   hc.create()

For a full list of options for each halo finder, see:

* FoF ("fof"): :class:`~yt_astro_analysis.halo_analysis.halo_finding.halo_objects.FOFHaloFinder`

* HOP ("hop"): :class:`~yt_astro_analysis.halo_analysis.halo_finding.halo_objects.HOPHaloFinder`

* Rockstar-galaxies ("rockstar"): :class:`~yt_astro_analysis.halo_analysis.halo_finding.rockstar.rockstar.RockstarHaloFinder`

.. _fof_finding:

FoF
^^^

This is a basic friends-of-friends algorithm. Any two particles
separated by less than a linking length are considered to be in
the same group. See
`Efstathiou et al. (1985)
<http://adsabs.harvard.edu/abs/1985ApJS...57..241E>`_ for more
details as well as
:class:`~yt_astro_analysis.halo_finding.halo_objects.FOFHaloFinder`.

.. _hop_finding:

HOP
^^^

This is the method introduced by `Eisenstein and Hut (1998)
<http://adsabs.harvard.edu/abs/1998ApJ...498..137E>`__. The
procedure is roughly as follows.

#. Estimate the local density at each particle using a
   smoothing kernel.

#. Build chains of linked particles by 'hopping' from one
   particle to its densest neighbor. A particle which is
   its own densest neighbor is the end of the chain.

#. All chains that share the same densest particle are
   grouped together.

#. Groups are included, linked together, or discarded
   depending on the user-supplied over density
   threshold parameter. The default is 160.

For both the FoF and HOP halo finders, the resulting halo catalogs will be written
to a directory associated with the ``output_dir`` keyword provided to the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`.
The number of files for each catalog is equal to the number of processors used. The
catalog files have the naming convention
``<dataset_name>/<dataset_name>.<processor_number>.h5``, where ``dataset_name`` refers
to the name of the snapshot. For more information on loading these with yt, see
:ref:`halocatalog`.

.. _rockstar_finding:

Rockstar-galaxies
^^^^^^^^^^^^^^^^^

Rockstar uses an adaptive hierarchical refinement of friends-of-friends
groups in six phase-space dimensions and one time dimension, which
allows for robust (grid-independent, shape-independent, and noise-
resilient) tracking of substructure. The methods are described in
`Behroozi et al. 2011 <http://adsabs.harvard.edu/abs/2011arXiv1110.4372B>`__.

The ``yt_astro_analysis`` package works with the latest version of
``rockstar-galaxies``. See :ref:`installation-rockstar` for information on
obtaining and installing ``rockstar-galaxies`` for use with
``yt_astro_analysis``.

To run Rockstar, your script must be run with ``mpirun`` using a minimum of three
processors. Rockstar processes are divided into three groups:

* readers: these read particle data from the snapshots. Set the number of readers
  with the ``num_readers`` keyword argument.
* writers: these perform the halo finding and write the subsequent halo catalogs.
  Set the number of writers with the ``num_writers`` keyword argument.
* server: this process coordinates the activity of the readers and writers.
  There is only one server process. The total number of processes given with
  ``mpirun`` must be equal to the number of readers plus writers plus one
  (for the server).

.. code-block:: python

   import yt

   yt.enable_parallelism()
   from yt.extensions.astro_analysis.halo_analysis import HaloCatalog

   my_sim = yt.load_simulation("enzo_tiny_cosmology/32Mpc_32.enzo", "Enzo")
   my_sim.get_time_series()
   hc = HaloCatalog(
       data_ds=my_sim,
       finder_method="rockstar",
       finder_kwargs={"num_readers": 1, "num_writers": 1},
   )
   hc.create()

.. warning:: Running Rockstar from yt on multiple compute nodes
   connected by an Infiniband network can be problematic. It is recommended to
   force the use of the non-Infiniband network (e.g. Ethernet) using this flag:
   ``--mca btl ^openib``.  For example, to run with 24 cores, do:
   ``mpirun -n 24 --mca btl ^openib python ./run_rockstar.py``.

See
:class:`~yt_astro_analysis.halo_analysis.halo_finding.rockstar.rockstar.RockstarHaloFinder`
for the list of available options.

Rockstar halo catalogs are saved to the directory associated the ``output_dir``
keyword provided to the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`.
The number of files for each catalog is equal to the number of writers. The
catalog files have the naming convention
``halos_<catalog_number>.<processor_number>.bin``, where catalog number 0 is the
first halo catalog calculated. For more information on loading these with yt,
see :ref:`rockstar`.

Parallelism
-----------

All three halo finders can be run in parallel using ``mpirun`` and by adding
``yt.enable_parallelism()`` to the top of the script. The computational domain
will be divided evenly among all processes (among the writers in the case of
Rockstar) with a small amount of padding to ensure halos on sub-volume
boundaries are not split. For FoF and HOP, the number of processors used only
needs to provided to ``mpirun`` (e.g., ``mpirun -np 8`` to run on 8 processors).

.. code-block:: python

   import yt

   yt.enable_parallelism()
   from yt.extensions.astro_analysis.halo_analysis import HaloCatalog

   data_ds = yt.load("Enzo_64/RD0006/RedshiftOutput0006")
   hc = HaloCatalog(
       data_ds=data_ds,
       finder_method="fof",
       finder_kwargs={"ptype": "stars", "padding": 0.02},
   )
   hc.create()

For more information on running ``yt`` in parallel, see
:ref:`parallel-computation`.

.. _saving_halo_particles:

Saving Halo Particles
---------------------

As of version 1.1 of ``yt_astro_analysis``, the ids of the particles
belonging to each halo can be saved to the catalog when using either the
:ref:`fof_finding` or :ref:`hop_finding` methods. The is enabled by default
and can be disabled by setting ``save_particles`` to ``False`` in the
``finder_kwargs`` dictionary, as described above. Rockstar will also save
halo particles to the ``.bin`` files. However, reading these is not currently
supported in yt. See :ref:`halocatalog` for information on accessing halo
particles for FoF and HOP catalogs.
