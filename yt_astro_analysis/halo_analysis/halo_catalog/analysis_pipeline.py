"""
AnalysisPipeline class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) yt Development Team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import functools
import numpy as np
import os

from yt.frontends.ytdata.utilities import \
    save_as_dataset
from yt.funcs import \
    ensure_dir, \
    mylog
from yt.units.yt_array import \
    YTArray
from yt.utilities.parallel_tools.parallel_analysis_interface import \
    ParallelAnalysisInterface, \
    parallel_blocking_call, \
    parallel_objects

from yt_astro_analysis.halo_analysis.halo_catalog.halo_callbacks import \
    callback_registry
from yt_astro_analysis.halo_analysis.halo_catalog.halo_filters import \
    filter_registry
from yt_astro_analysis.halo_analysis.halo_catalog.halo_quantities import \
    quantity_registry
from yt_astro_analysis.halo_analysis.halo_catalog.halo_recipes import \
    recipe_registry
from yt_astro_analysis.utilities.logging import \
    quiet

class AnalysisTarget(object):
    _container_name = "pipeline"
    def __init__(self, pipeline):
        setattr(self, self._container_name, pipeline)
        self.quantities = {}

    def _set_field_value(self, fieldkey, fieldname, data_source, index):
        self.quantities[fieldkey] = \
          self._get_field_value(fieldname, data_source, index)

    def _get_field_value(self, fieldname, data_source, index):
        pass

class AnalysisPipeline(ParallelAnalysisInterface):
    r"""Create a AnalysisPipeline: an object that allows for the creation and association
    of data with a set of halo objects.

    A AnalysisPipeline object pairs a simulation dataset and the output from a halo finder,
    allowing the user to perform analysis on each of the halos found by the halo finder.
    Analysis is performed by providing callbacks: functions that accept a Halo object
    and perform independent analysis, return a quantity to be associated with the halo,
    or return True or False whether a halo meets various criteria.  The resulting set of
    quantities associated with each halo is then written out to disk at a "halo catalog."
    This halo catalog can then be loaded in with yt as any other simulation dataset.

    Parameters
    ----------
    halos_ds : str
        Dataset created by a halo finder.  If None, a halo finder should be
        provided with the finder_method keyword.
    data_ds : str
        Dataset created by a simulation.
    data_source : data container
        Data container associated with either the halos_ds to use for analysis.
        This can be used to restrict analysis to a subset of the full catalog.
        By default, the entire catalog will be analyzed.
    finder_method : str
        Halo finder to be used if no halos_ds is given.
    output_dir : str
        The top level directory into which analysis output will be written.
        Default: "halo_catalogs"
    finder_kwargs : dict
        Arguments to pass to the halo finder if finder_method is given.

    Examples
    --------

    >>> # create profiles or overdensity vs. radius for each halo and save to disk
    >>> import yt
    >>> from yt.extensions.astro_analysis.halo_analysis.api import *
    >>> data_ds = yt.load("DD0064/DD0064")
    >>> halos_ds = yt.load("rockstar_halos/halos_64.0.bin",
    ...                    output_dir="halo_catalogs/catalog_0064")
    >>> hc = AnalysisPipeline(data_ds=data_ds, halos_ds=halos_ds)
    >>> # filter out halos with mass < 1e13 Msun
    >>> hc.add_filter("quantity_value", "particle_mass", ">", 1e13, "Msun")
    >>> # create a sphere object with radius of 2 times the virial_radius field
    >>> hc.add_callback("sphere", factor=2.0, radius_field="virial_radius")
    >>> # make radial profiles
    >>> hc.add_callback("profile", "radius", [("gas", "overdensity")],
    ...                 weight_field="cell_volume", accumulation=True)
    >>> # save the profiles to disk
    >>> hc.add_callback("save_profiles", output_dir="profiles")
    >>> # create the catalog
    >>> hc.create()

    >>> # load in the saved halo catalog and all the profile data
    >>> halos_ds = yt.load("halo_catalogs/catalog_0064/catalog_0064.0.h5")
    >>> hc = AnalysisPipeline(halos_ds=halos_ds,
                         output_dir="halo_catalogs/catalog_0064")
    >>> hc.add_callback("load_profiles", output_dir="profiles")
    >>> hc.load()

    See Also
    --------
    add_callback, add_filter, add_quantity, add_recipe

    """

    _target_cls = AnalysisTarget
    _target_id_field = 'particle_identifier'

    def __init__(self, output_dir="analysis", data_source=None):
        ParallelAnalysisInterface.__init__(self)

        self.output_basedir = ensure_dir(output_dir)
        self.data_source = data_source

        # all of the analysis actions to be performed:
        # callbacks, filters, and quantities
        self.actions = []
        # fields to be written to the halo catalog
        self.quantities = []
        self.field_quantities = []

        self._add_default_quantities()

    def _add_default_quantities(self):
        pass

    _source_ds = None
    @property
    def source_ds(self):
        if self._source_ds is not None:
            return self._source_ds
        return getattr(self.data_source, 'ds', {})

    @property
    def output_basename(self):
        ds = self.source_ds
        if isinstance(ds, dict):
            basename = ds.get('basename')
        else:
            basename = getattr(ds, 'basename')

        if basename is None:
            basename = 'analysis'
        if '.' in basename:
            basename = basename[:basename.find('.')]
        return basename

    @property
    def output_dir(self):
        return os.path.join(self.output_basedir, self.output_basename)

    def add_callback(self, callback, *args, **kwargs):
        r"""
        Add a callback to the halo catalog action list.

        A callback is a function that accepts and operates on a Halo object and
        does not return anything.  Callbacks must exist within the callback_registry.
        Give additional args and kwargs to be passed to the callback here.

        Parameters
        ----------
        callback : string
            The name of the callback.

        Examples
        --------

        >>> # Here, a callback is defined and added to the registry.
        >>> def _say_something(halo, message):
        ...     my_id = halo.quantities['particle_identifier']
        ...     print "Halo %d: here is a message - %s." % (my_id, message)
        >>> add_callback("hello_world", _say_something)

        >>> # Now this callback is accessible to the AnalysisPipeline object
        >>> hc.add_callback("hello_world", "this is my message")

        """
        callback = callback_registry.find(callback, *args, **kwargs)
        self.actions.append(("callback", callback))

    def add_quantity(self, key, *args, **kwargs):
        r"""
        Add a quantity to the halo catalog action list.

        A quantity is a function that accepts a Halo object and return a value or
        values.  These values are stored in a "quantities" dictionary associated
        with the Halo object.  Quantities must exist within the quantity_registry.
        Give additional args and kwargs to be passed to the quantity function here.

        Parameters
        ----------
        key : string
            The name of the callback.
        field_type : string
            If not None, the quantity is the value of the field provided by the
            key parameter, taken from the halo finder dataset.  This is the way
            one pulls values for the halo from the halo dataset.
            Default : None

        Examples
        --------

        >>> # pull the virial radius from the halo finder dataset
        >>> hc.add_quantity("virial_radius", field_type="halos")

        >>> # define a custom quantity and add it to the register
        >>> def _mass_squared(halo):
        ...     # assume some entry "particle_mass" exists in the quantities dict
        ...     return halo.quantities["particle_mass"]**2
        >>> add_quantity("mass_squared", _mass_squared)

        >>> # add it to the halo catalog action list
        >>> hc.add_quantity("mass_squared")

        """

        from_data_source = kwargs.pop("from_data_source", False)
        field_type = kwargs.pop("field_type", None)

        if not from_data_source:
            quantity = quantity_registry.find(key, *args, **kwargs)
        else:
            if field_type is None:
                quantity = key
            else:
                quantity = (field_type, key)
            self.field_quantities.append(quantity)

        self.quantities.append(key)
        self.actions.append(("quantity", (key, quantity)))

    def add_filter(self, halo_filter, *args, **kwargs):
        r"""
        Add a filter to the halo catalog action list.

        A filter is a function that accepts a Halo object and returns either True
        or False.  If True, any additional actions added to the list are carried out
        and the results are added to the final halo catalog.  If False, any further
        actions are skipped and the halo will be omitted from the final catalog.
        Filters must exist within the filter_registry.  Give additional args and kwargs
        to be passed to the filter function here.

        Parameters
        ----------
        halo_filter : string
            The name of the filter.

        Examples
        --------

        >>> # define a filter and add it to the register.
        >>> def _my_filter(halo, mass_value):
        ...     return halo.quantities["particle_mass"] > YTQuantity(mass_value, "Msun")
        >>> # add it to the register
        >>> add_filter("mass_filter", _my_filter)

        >>> # add the filter to the halo catalog actions
        >>> hc.add_filter("mass_value", 1e12)

        """

        halo_filter = filter_registry.find(halo_filter, *args, **kwargs)
        self.actions.append(("filter", halo_filter))

    def add_recipe(self, recipe, *args, **kwargs):
        r"""
        Add a recipe to the halo catalog action list.

        A recipe is an operation consisting of a series of callbacks, quantities,
        and/or filters called in succession.  Recipes can be used to store a more
        complex series of analysis tasks as a single entity.

        Currently, the available recipe is ``calculate_virial_quantities``.

        Parameters
        ----------

        halo_recipe : string
            The name of the recipe.

        Examples
        --------

        >>> import yt
        >>> from yt.extensions.astro_analysis.halo_analysis.api import AnalysisPipeline
        >>>
        >>> data_ds = yt.load('Enzo_64/RD0006/RedshiftOutput0006')
        >>> halos_ds = yt.load('rockstar_halos/halos_0.0.bin')
        >>> hc = AnalysisPipeline(data_ds=data_ds, halos_ds=halos_ds)
        >>>
        >>> # Filter out less massive halos
        >>> hc.add_filter("quantity_value", "particle_mass", ">", 1e14, "Msun")
        >>>
        >>> # Calculate virial radii
        >>> hc.add_recipe("calculate_virial_quantities", ["radius", "matter_mass"])
        >>>
        >>> hc.create()

        """

        halo_recipe = recipe_registry.find(recipe, *args, **kwargs)
        halo_recipe(self)

    def _preprocess(self):
        "Create callback output directories."

        for action_type, action in self.actions:
            if action_type != 'callback':
                continue
            my_output_dir = action.kwargs.get('output_dir')
            if my_output_dir is not None:
                new_output_dir = ensure_dir(
                    os.path.join(self.output_dir, my_output_dir))
                action.kwargs['output_dir'] = new_output_dir


    def create(self, save_objects=False, save_output=True,
               njobs='auto', dynamic=False):
        r"""
        Create the halo catalog given the callbacks, quantities, and filters that
        have been provided.

        This is a wrapper around the main _run function with default arguments tuned
        for halo catalog creation.  By default, halo objects are not saved but the
        halo catalog is written, opposite to the behavior of the load function.

        Parameters
        ----------
        save_objects : bool
            If True, a list of all Halo objects is retained under the "halo_list"
            attribute.  If False, only the compiles quantities are saved under the
            "catalog" attribute.
            Default: False
        save_output : bool
            If True, save the final catalog to disk.
            Default: True
        njobs : int
            The number of jobs over which to divide halo analysis.  Choose -1
            to allocate one processor per halo.
            Default: -1
        dynamic : int
            If False, halo analysis is divided evenly between all available processors.
            If True, parallelism is performed via a task queue.
            Default: False

        See Also
        --------
        load

        """
        self._run(save_objects, save_output,
                  njobs=njobs, dynamic=dynamic)

    def load(self, njobs='auto', dynamic=False):
        r"""
        Load a previously created halo catalog.

        This is a wrapper around the main _run function with default arguments tuned
        for reloading halo catalogs and associated data.  By default, halo objects are
        saved and the halo catalog is not written, opposite to the behavior of the
        create function.

        Parameters
        ----------
        njobs : int
            The number of jobs over which to divide halo analysis.  Choose -1
            to allocate one processor per halo.
            Default: -1
        dynamic : int
            If False, halo analysis is divided evenly between all available processors.
            If True, parallelism is performed via a task queue.
            Default: False

        See Also
        --------
        create

        """
        self._run(True, False, njobs=njobs, dynamic=dynamic)

    @parallel_blocking_call
    def _run(self, save_objects, save_output,
             njobs='auto', dynamic=False):
        r"""
        Run the requested halo analysis.

        Parameters
        ----------
        save_objects : bool
            If True, a list of all Halo objects is retained under the "halo_list"
            attribute.  If False, only the compiles quantities are saved under the
            "catalog" attribute.
        save_output : bool
            If True, save the final catalog to disk.
        njobs : int
            The number of jobs over which to divide halo analysis.  Choose -1
            to allocate one processor per halo.
            Default: -1
        dynamic : int
            If False, halo analysis is divided evenly between all available processors.
            If True, parallelism is performed via a task queue.
            Default: False

        See Also
        --------
        create, load

        """

        self._preprocess()

        self.catalog = []
        if save_objects:
            self.target_list = []

        for my_index, chunk in self._yield_targets(
                njobs=njobs, dynamic=dynamic):
            self._process_target(
                my_index, my_index,
                save_objects, data_source=chunk)

        if save_output:
            self._save()

    def _yield_targets(self, njobs='auto', dynamic=False):

        my_size = self.comm.size

        if njobs == 'auto':
            # use task queue if odd number of cores more than 2
            my_dynamic = my_size > 2 and my_size % 2
            my_njobs = -1
        else:
            my_dynamic = dynamic
            my_njobs = njobs

        for chunk in self.data_source.chunks([], 'io'):

            if self.comm.rank == 0:
                chunk.get_data(self.field_quantities)

            if my_size > 1:
                fdata = self.comm.comm.bcast(chunk.field_data, root=0)
                chunk.field_data.update(fdata)

            target_indices = \
              range(chunk[self.halo_field_type, self._target_id_field].size)
            my_indices = parallel_objects(
                target_indices, njobs=my_njobs, dynamic=my_dynamic)

            for my_index in my_indices:
                yield my_index, chunk

    def _process_target(self, target, index, save_objects,
                        data_source=None):

        new_target = self._target_cls(self)
        new_target.index = index
        new_target.object = target
        target_filter = True
        for action_type, action in self.actions:
            if action_type == "callback":
                action(new_target)
            elif action_type == "filter":
                target_filter = action(new_target)
                if not target_filter:
                    break
            elif action_type == "quantity":
                key, quantity = action
                if callable(quantity):
                    new_target.quantities[key] = quantity(new_target)
                else:
                    new_target._set_field_value(
                        key, quantity, data_source, index)
            else:
                raise RuntimeError(
                    "Action must be a callback, filter, or quantity.")

        if target_filter:
            for quantity in new_target.quantities.values():
                if hasattr(quantity, "units"):
                    quantity.convert_to_base()
            self.catalog.append(new_target.quantities)

        if save_objects and target_filter:
            self.target_list.append(new_target)
        else:
            del new_target

    def _save(self, ds=None, data=None, extra_attrs=None, ftypes=None):
        "Save pipeline results."

        if ds is None:
            ds = self.source_ds
        else:
            self._source_ds = ds

        data_dir = ensure_dir(self.output_dir)
        filename = os.path.join(
            data_dir, "%s.%d.h5" % (self.output_basename, self.comm.rank))

        if data is None:
            n_halos = len(self.catalog)
            data = {}
            if n_halos > 0:
                for key in self.quantities:

                    if hasattr(self.catalog[0][key], 'units'):
                        registry = self.catalog[0][key].units.registry
                        my_arr = functools.partial(YTArray, registry=registry)
                    else:
                        my_arr = np.array

                    data[key] = my_arr([halo[key] for halo in self.catalog])
        else:
            n_halos = data[self._target_id_field].size

        mylog.info("Saving analysis (%d targets): %s." %
                   (n_halos, filename))

        if ftypes is None:
            ftypes = dict((key, ".") for key in self.quantities)

        if extra_attrs is None:
            extra_attrs = {}
        extra_attrs_d = {"data_type": "halo_catalog",
                         "num_halos": n_halos}
        extra_attrs_d.update(extra_attrs)

        with quiet():
            save_as_dataset(
                ds, filename, data,
                field_types=ftypes,
                extra_attrs=extra_attrs_d)
        self._source_ds = None
