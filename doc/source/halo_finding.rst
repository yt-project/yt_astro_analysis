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
   from yt.extensions.astro_analysis.halo_analysis Import

   data_ds = yt.load('Enzo_64/RD0006/RedshiftOutput0006')
   hc = HaloCatalog(data_ds=data_ds, finder_method='hop')
   hc.create()

Halo Finding on Multiple Snapshots
----------------------------------

To run halo finding on a series of snapshots, provide a
:class:`~yt.data_objects.time_series.DatasetSeries` or
:class:`~yt.data_objects.time_series.SimulationTimeSeries` to the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`.
See :ref:`time-series-analysis` and :ref:`analyzing-an-entire-simulation` for
more information on creating these. All three halo finders can be run this way.

.. code-block:: python

   import yt
   from yt.extensions.astro_analysis.halo_analysis Import

   my_sim = yt.load_simulation('enzo_tiny_cosmology/32Mpc_32.enzo', 'Enzo')
   hc = HaloCatalog(data_ds=my_sim, finder_method='hop')
   hc.create()

Halo Finder Options
-------------------

The available ``finder_method`` options are "fof", "hop", or
"rockstar". Each of these methods has their own set of keyword
arguments to control functionality. These can specified in the form
of a dictionary using the ``finder_kwargs`` keyword.

.. code-block:: python

   import yt
   from yt.extensions.astro_analysis.halo_analysis.api import HaloCatalog

   data_ds = yt.load('Enzo_64/RD0006/RedshiftOutput0006')
   hc = HaloCatalog(data_ds=data_ds, finder_method='fof',
                    finder_kwargs={"ptype": "stars",
                                   "padding": 0.02})
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

### YOU ARE HERE

To run the Rockstar Halo finding, you must launch python with MPI and
parallelization enabled. While Rockstar itself does not require MPI to run,
the MPI libraries allow yt to distribute particle information across multiple
nodes.

.. warning:: At the moment, running Rockstar inside of yt on multiple compute nodes
   connected by an Infiniband network can be problematic. Therefore, for now
   we recommend forcing the use of the non-Infiniband network (e.g. Ethernet)
   using this flag: ``--mca btl ^openib``.
   For example, here is how Rockstar might be called using 24 cores:
   ``mpirun -n 24 --mca btl ^openib python ./run_rockstar.py --parallel``.

The script above configures the Halo finder, launches a server process which
disseminates run information and coordinates writer-reader processes.
Afterwards, it launches reader and writer tasks, filling the available MPI
slots, which alternately read particle information and analyze for halo
content.

The RockstarHaloFinder class has these options that can be supplied to the
halo catalog through the ``finder_kwargs`` argument:

* ``dm_type``, the index of the dark matter particle. Default is 1.
* ``outbase``, This is where the out*list files that Rockstar makes should be
  placed. Default is 'rockstar_halos'.
* ``num_readers``, the number of reader tasks (which are idle most of the
  time.) Default is 1.
* ``num_writers``, the number of writer tasks (which are fed particles and
  do most of the analysis). Default is MPI_TASKS-num_readers-1.
  If left undefined, the above options are automatically
  configured from the number of available MPI tasks.
* ``force_res``, the resolution that Rockstar uses for various calculations
  and smoothing lengths. This is in units of Mpc/h.
  If no value is provided, this parameter is automatically set to
  the width of the smallest grid element in the simulation from the
  last data snapshot (i.e. the one where time has evolved the
  longest) in the time series:
  ``ds_last.index.get_smallest_dx() * ds_last['Mpch']``.
* ``total_particles``, if supplied, this is a pre-calculated
  total number of dark matter
  particles present in the simulation. For example, this is useful
  when analyzing a series of snapshots where the number of dark
  matter particles should not change and this will save some disk
  access time. If left unspecified, it will
  be calculated automatically. Default: ``None``.
* ``dm_only``, if set to ``True``, it will be assumed that there are
  only dark matter particles present in the simulation.
  This option does not modify the halos found by Rockstar, however
  this option can save disk access time if there are no star particles
  (or other non-dark matter particles) in the simulation. Default: ``False``.

Rockstar dumps halo information in a series of text (halo*list and
out*list) and binary (halo*bin) files inside the ``outbase`` directory.
We use the halo list classes to recover the information.

Inside the ``outbase`` directory there is a text file named ``datasets.txt``
that records the connection between ds names and the Rockstar file names.

Parallelism
-----------

DO THIS TOO

Saving Halo Particles
---------------------

As of version 1.1 of ``yt_astro_analysis``, the ids of the particles
belonging to each halo can be saved to the catalog when using either the
:ref:`fof_finding` or :ref:`hop_finding` methods. The is enabled by default
and can be disabled by setting ``save_particles`` to ``False`` in the
``finder_kwargs`` dictionary, as described above. This is not supported for
the ``yt`` version of Rockstar.
