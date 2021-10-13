.. _halo_catalog_analysis:

Halo Analysis
=============

Halo finding and analysis are combined into a single framework called the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`.
All halo catalogs created by the methods outlined in
:ref:`halo_catalog_finding` as well as those in the formats discussed in
:ref:`halo-catalog-data` can be loaded in to yt as first-class datasets.
Once a halo catalog has been created, further analysis can be performed
by providing both the halo catalog and the original simulation dataset to
the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`.

.. code-block:: python

   import yt
   from yt.extensions.astro_analysis.halo_analysis import HaloCatalog

   halos_ds = yt.load("rockstar_halos/halos_0.0.bin")
   data_ds = yt.load("Enzo_64/RD0006/RedshiftOutput0006")
   hc = HaloCatalog(data_ds=data_ds, halos_ds=halos_ds)

A data object can also be supplied via the keyword ``data_source``,
associated with either dataset, to control the spatial region in
which halo analysis will be performed.

The :class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`
allows the user to create a pipeline of analysis actions that will be
performed on all halos in the existing catalog.  The analysis can be
performed in parallel with separate processors or groups of processors
being allocated to perform the entire pipeline on individual halos.
The pipeline is setup by adding actions to the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`.
Each action is represented by a callback function that will be run on
each halo.  There are four types of actions:

* :ref:`halo_catalog_filters`
* :ref:`halo_catalog_quantities`
* :ref:`halo_catalog_callbacks`
* :ref:`halo_catalog_recipes`

A list of all available filters, quantities, and callbacks can be found in
:ref:`halo_analysis_ref`.
All interaction with this analysis can be performed by importing from
halo_analysis.

.. _halo_catalog_filters:

Filters
-------

A filter is a function that returns True or False. If the return value
is True, any further queued analysis will proceed and the halo in
question will be added to the final catalog. If the return value False,
further analysis will not be performed and the halo will not be included
in the final catalog.

An example of adding a filter:

.. code-block:: python

   hc.add_filter("quantity_value", "particle_mass", ">", 1e13, "Msun")

The two available filters are
:func:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_filters.quantity_value`
and
:func:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_filters.not_subhalo`.
More can be added by the user by defining a function that accepts a halo object
as the first argument and then adding it as an available filter. If you
think that your filter may be of use to the general community, you can
add it to ``yt_astro_analysis/halo_analysis/halo_catalog/halo_filters.py`` and issue a
pull request.

An example of defining your own filter:

.. code-block:: python

   def my_filter_function(halo):

       # Define condition for filter
       filter_value = True

       # Return a boolean value
       return filter_value


   # Add your filter to the filter registry
   add_filter("my_filter", my_filter_function)

   # ... Later on in your script
   hc.add_filter("my_filter")

.. _halo_catalog_quantities:

Quantities
----------

A quantity is a call back that returns a value or values. The return values
are stored within the halo object in a dictionary called “quantities.” At
the end of the analysis, all of these quantities will be written to disk as
the final form of the generated halo catalog.

Quantities may be available in the initial fields found in the halo catalog,
or calculated from a function after supplying a definition. An example
definition of center of mass is shown below. If you think that
your quantity may be of use to the general community, add it to
``yt_astro_analysis/halo_analysis/halo_catalog/halo_quantities.py``
and issue a pull request.  Default halo quantities are:

* ``particle_identifier`` -- Halo ID (e.g. 0 to N)
* ``particle_mass`` -- Mass of halo
* ``particle_position_x`` -- Location of halo
* ``particle_position_y`` -- Location of halo
* ``particle_position_z`` -- Location of halo
* ``virial_radius`` -- Virial radius of halo

An example of adding a quantity:

.. code-block:: python

   hc.add_quantity("center_of_mass")

An example of defining your own quantity:

.. code-block:: python

   def my_quantity_function(halo):
       # Define quantity to return
       quantity = 5

       return quantity


   # Add your filter to the filter registry
   add_quantity("my_quantity", my_quantity_function)


   # ... Later on in your script
   hc.add_quantity("my_quantity")

This quantity will then be accessible for functions called later via the
*quantities* dictionary that is associated with the halo object.

.. code-block:: python

   def my_new_function(halo):
       print(halo.quantities["my_quantity"])


   add_callback("print_quantity", my_new_function)

   # ... Anywhere after "my_quantity" has been called
   hc.add_callback("print_quantity")

.. _halo_catalog_callbacks:

Callbacks
---------

A callback is actually the super class for quantities and filters and
is a general purpose function that does something, anything, to a Halo
object. This can include hanging new attributes off the Halo object,
performing analysis and writing to disk, etc. A callback does not return
anything.

An example of using a pre-defined callback where we create a sphere for
each halo with a radius that is twice the saved ``radius``.

.. code-block:: python

   hc.add_callback("sphere", factor=2.0)

Currently available callbacks are located in
``yt_astro_analysis/halo_analysis/halo_catalog/halo_callbacks.py``.  New callbacks may
be added by using the syntax shown below. If you think that your
callback may be of use to the general community, add it to
halo_callbacks.py and issue a pull request.

An example of defining your own callback:

.. code-block:: python

   def my_callback_function(halo):
       # Perform some callback actions here
       x = 2
       halo.x_val = x


   # Add the callback to the callback registry
   add_callback("my_callback", my_callback_function)


   # ...  Later on in your script
   hc.add_callback("my_callback")

.. _halo_catalog_recipes:

Recipes
-------

Recipes allow you to create analysis tasks that consist of a series of
callbacks, quantities, and filters that are run in succession.  An example
of this is
:func:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_recipes.calculate_virial_quantities`,
which calculates virial quantities by first creating a sphere container,
performing 1D radial profiles, and then interpolating to get values at a
specified threshold overdensity.  All of these operations are separate
callbacks, but the recipes allow you to add them to your analysis pipeline
with one call.  For example,

.. code-block:: python

   hc.add_recipe("calculate_virial_quantities", ["radius", "matter_mass"])

The available recipes are located in
``yt_astro_analysis/halo_analysis/halo_catalog/halo_recipes.py``.  New recipes can be
created in the following manner:

.. code-block:: python

   def my_recipe(halo_catalog, fields, weight_field=None):
       # create a sphere
       halo_catalog.add_callback("sphere")
       # make profiles
       halo_catalog.add_callback("profile", ["radius"], fields, weight_field=weight_field)
       # save the profile data
       halo_catalog.add_callback("save_profiles", output_dir="profiles")


   # add recipe to the registry of recipes
   add_recipe("profile_and_save", my_recipe)


   # ...  Later on in your script
   hc.add_recipe("profile_and_save", ["density", "temperature"], weight_field="cell_mass")

Note, that unlike callback, filter, and quantity functions that take a ``Halo``
object as the first argument, recipe functions should take a ``HaloCatalog``
object as the first argument.

Running the Pipeline
--------------------

After all callbacks, quantities, and filters have been added, the
analysis begins with a call to
:meth:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog.create`.

.. code-block:: python

   hc.create()

The ``save_halos`` keyword determines whether the actual Halo objects
are saved after analysis on them has completed or whether just the
contents of their quantities dicts will be retained for creating the
final catalog. The looping over halos uses a call to parallel_objects
allowing the user to control how many processors work on each halo.
The final catalog is written to disk in the output directory given
when the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`
object was created.

All callbacks, quantities, and filters are stored in an actions list,
meaning that they are executed in the same order in which they were added.
This enables the use of simple, reusable, single action callbacks that
depend on each other. This also prevents unnecessary computation by allowing
the user to add filters at multiple stages to skip remaining analysis if it
is not warranted.

Parallelism
-----------

Halo analysis using the
:class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`
can be parallelized by adding ``yt.enable_parallelism()`` to the top of the
script and running with ``mpirun``.

.. code-block:: python

   import yt

   yt.enable_parallelism()
   from yt.extensions.astro_analysis.halo_analysis import HaloCatalog

   halos_ds = yt.load("rockstar_halos/halos_0.0.bin")
   data_ds = yt.load("Enzo_64/RD0006/RedshiftOutput0006")
   hc = HaloCatalog(data_ds=data_ds, halos_ds=halos_ds)
   hc.create(njobs="auto")

The nature of the parallelism can be configured with two keywords provided to the
:meth:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog.create`
function: ``njobs`` and ``dynamic``. If ``dynamic`` is set to False, halos will be
distributed evenly over all processors. If ```dynamic`` is set to True, halos
will be allocated to processors via a task queue. The ``njobs`` keyword determines
the number of processor groups over which the analysis will be divided. The
default value for ``njobs`` is "auto". In this mode, a single processor will be
allocated to analyze a halo. The ``dynamic`` keyword is overridden to False if
the number of processors being used is even and True (use a task queue) if odd.
Set ``njobs`` to -1 to mandate a single processor to analyze a halo and to a positive
number to create that many processor groups for performing analysis. The number of
processors used per halo will then be the total number of processors divided by
``njobs``. For more information on running ``yt`` in parallel, see
:ref:`parallel-computation`.

Loading Created Halo Catalogs
-----------------------------

A :class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`
saved to disk can be reloaded as a yt dataset with the standard call to
:func:`~yt.loaders.load`. See :ref:`halocatalog` for more information on
loading a newly created catalog.
