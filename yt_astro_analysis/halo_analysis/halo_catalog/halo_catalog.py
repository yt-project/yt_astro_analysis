"""
HaloCatalog class and member functions



"""

import functools
import os

import numpy as np
from unyt import unyt_array

from yt.data_objects.time_series import DatasetSeries
from yt.frontends.ytdata.utilities import save_as_dataset
from yt.funcs import ensure_dir, mylog
from yt.utilities.parallel_tools.parallel_analysis_interface import (
    ParallelAnalysisInterface,
    parallel_blocking_call,
    parallel_objects,
)
from yt_astro_analysis.halo_analysis.halo_catalog.analysis_pipeline import (
    AnalysisPipeline,
)
from yt_astro_analysis.halo_analysis.halo_catalog.halo_finding_methods import (
    finding_method_registry,
)
from yt_astro_analysis.halo_analysis.halo_catalog.halo_object import Halo
from yt_astro_analysis.utilities.logging import quiet

_default_fields = (
    ["particle_identifier", "particle_mass", "virial_radius"]
    + ["particle_position_" + ax for ax in "xyz"]
    + ["particle_velocity_" + ax for ax in "xyz"]
)


class HaloCatalog(ParallelAnalysisInterface):
    r"""Create a HaloCatalog: an object that allows for the creation and association
    of data with a set of halo objects.

    A HaloCatalog object pairs a simulation dataset and the output from a halo finder,
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
    halo_field_type : str
        The field type for halos. This can be used to specify a certain type of halo
        in a dataset that contains multiple types.
        Default: "all"
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
    >>> from yt.extensions.astro_analysis.halo_analysis import HaloCatalog
    >>> data_ds = yt.load("DD0064/DD0064")
    >>> halos_ds = yt.load("rockstar_halos/halos_64.0.bin",
    ...                    output_dir="halo_catalogs/catalog_0064")
    >>> hc = HaloCatalog(data_ds=data_ds, halos_ds=halos_ds)
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
    >>> hc = HaloCatalog(halos_ds=halos_ds,
                         output_dir="halo_catalogs/catalog_0064")
    >>> hc.add_callback("load_profiles", output_dir="profiles")
    >>> hc.load()

    See Also
    --------
    add_callback, add_filter, add_quantity, add_recipe

    """

    _id_field = "particle_identifier"

    def __init__(
        self,
        halos_ds=None,
        data_ds=None,
        data_source=None,
        halo_field_type="all",
        finder_method=None,
        finder_kwargs=None,
        output_dir=None,
    ):

        super().__init__()

        self.halos_ds = halos_ds
        self.data_ds = data_ds
        self.halo_field_type = halo_field_type

        if halos_ds is None:
            if data_ds is None:
                raise RuntimeError("Must specify a halos_ds, data_ds, or both.")
            if finder_method is None:
                raise RuntimeError("Must specify a halos_ds or a finder_method.")

        if data_source is None and halos_ds is not None:
            data_source = halos_ds.all_data()
        self.data_source = data_source

        if output_dir is None:
            if finder_method == "rockstar":
                output_dir = finder_kwargs.get("outbase", "rockstar_halos")
            else:
                output_dir = "halo_catalogs"

        self.output_basedir = ensure_dir(output_dir)
        self.pipeline = AnalysisPipeline(output_dir=self.output_dir)
        self.quantities = self.pipeline.quantities

        self.finder_method_name = finder_method
        if finder_kwargs is None:
            finder_kwargs = {}
        if finder_method is not None:
            finder_method = finding_method_registry.find(finder_method, **finder_kwargs)
        self.finder_method = finder_method

        self._add_default_quantities()

    def _add_default_quantities(self):
        if self.halos_ds is None:
            return

        field_type = self.halo_field_type
        for field in _default_fields:
            field_name = (field_type, field)
            if field_name not in self.halos_ds.derived_field_list:
                mylog.warning(
                    "Halo dataset %s has no field %s.", self.halos_ds, field_name
                )
                continue
            self.add_quantity(field, from_data_source=True, field_type=field_type)

    _source_ds = None

    @property
    def source_ds(self):
        if self._source_ds is not None:
            return self._source_ds
        if self.data_source is not None:
            return self.data_source.ds
        return None

    @property
    def output_basename(self):
        ds = self.data_ds
        if isinstance(ds, DatasetSeries):
            ds = None

        if ds is None:
            ds = self.source_ds
        if ds is None:
            basename = "halo_catalog"
        else:
            basename = ds.basename

        if "." in basename:
            basename = basename[: basename.find(".")]
        return basename

    @property
    def output_dir(self):
        return os.path.join(self.output_basedir, self.output_basename)

    def _yield_halos(self, njobs="auto", dynamic=False):

        my_size = self.comm.size

        if njobs == "auto":
            # use task queue if odd number of cores more than 2
            my_dynamic = my_size > 2 and my_size % 2
            my_njobs = -1
        else:
            my_dynamic = dynamic
            my_njobs = njobs

        for chunk in self.data_source.chunks([], "io"):

            if self.comm.rank == 0:
                chunk.get_data(self.pipeline.field_quantities)

            if my_size > 1:
                fdata = self.comm.comm.bcast(chunk.field_data, root=0)
                chunk.field_data.update(fdata)

            target_indices = range(chunk[self.halo_field_type, self._id_field].size)
            my_indices = parallel_objects(
                target_indices, njobs=my_njobs, dynamic=my_dynamic
            )

            for my_index in my_indices:
                my_halo = Halo(self, chunk, my_index)
                yield my_halo

    @parallel_blocking_call
    def _run(self, save_halos, save_catalog, njobs="auto", dynamic=False):
        """
        Run analysis pipeline on all halos.

        This is used by both load and create.
        """

        # Find halos.
        if self.halos_ds is None:
            self.finder_method(self)
            return

        self.pipeline._preprocess()

        self.catalog = []
        if save_halos:
            self.halo_list = []

        for my_halo in self._yield_halos(njobs=njobs, dynamic=dynamic):
            rval = self.pipeline._process_target(my_halo)

            if rval:
                for quantity in my_halo.quantities.values():
                    if hasattr(quantity, "units"):
                        quantity.convert_to_base()
                self.catalog.append(my_halo.quantities)

            if save_halos and rval:
                self.halo_list.append(my_halo)
            else:
                del my_halo

        if save_catalog:
            self._save()

    def _save(self, ds=None, data=None, extra_attrs=None, field_types=None):
        "Save new halo catalog."

        if ds is None:
            ds = self.source_ds
        else:
            self._source_ds = ds

        data_dir = ensure_dir(self.output_dir)
        filename = os.path.join(data_dir, f"{self.output_basename}.{self.comm.rank}.h5")

        if data is None:
            n_halos = len(self.catalog)
            data = {}
            if n_halos > 0:
                for key in self.quantities:

                    if hasattr(self.catalog[0][key], "units"):
                        registry = self.catalog[0][key].units.registry
                        my_arr = functools.partial(unyt_array, registry=registry)
                    else:
                        my_arr = np.array

                    data[key] = my_arr([halo[key] for halo in self.catalog])
        else:
            n_halos = data[self._id_field].size

        mylog.info("Saving %d halos: %s.", n_halos, filename)

        if field_types is None:
            field_types = {key: "." for key in self.quantities}

        if extra_attrs is None:
            extra_attrs = {}
        extra_attrs_d = {"data_type": "halo_catalog", "num_halos": n_halos}
        extra_attrs_d.update(extra_attrs)

        with quiet():
            save_as_dataset(
                ds, filename, data, field_types=field_types, extra_attrs=extra_attrs_d
            )

    def create(self, save_halos=False, save_output=True, njobs="auto", dynamic=False):
        r"""
        Create the halo catalog given the callbacks, quantities, and filters that
        have been provided.

        This is a wrapper around the main _run function with default arguments tuned
        for halo catalog creation.  By default, halo objects are not saved but the
        halo catalog is written, opposite to the behavior of the load function.

        Parameters
        ----------
        save_halos : bool
            If True, a list of all Halo objects is retained under the "halo_list"
            attribute.  If False, only the compiles quantities are saved under the
            "catalog" attribute.
            Default: False
        save_output : bool
            If True, save the final catalog to disk.
            Default: True
        njobs : int
            The number of jobs over which to divide halo analysis. If set to "auto",
            use a task queue if total number of processors is an odd number and
            divide jobs evenly if an even number.
            Default: "auto"
        dynamic : int
            If False, halo analysis is divided evenly between all available processors.
            If True, parallelism is performed via a task queue. If njobs is set to
            "auto", behavior is controlled in the way described above.
            Default: False

        See Also
        --------
        load

        """

        self._run(save_halos, save_output, njobs=njobs, dynamic=dynamic)

    def load(self, njobs="auto", dynamic=False):
        r"""
        Load a previously created halo catalog.

        This is a wrapper around the main _run function with default arguments tuned
        for reloading halo catalogs and associated data.  By default, halo objects are
        saved and the halo catalog is not written, opposite to the behavior of the
        create function.

        Parameters
        ----------
        njobs : int
            The number of jobs over which to divide halo analysis. If set to "auto",
            use a task queue if total number of processors is an odd number and
            divide jobs evenly if an even number.
            Default: "auto"
        dynamic : int
            If False, halo analysis is divided evenly between all available processors.
            If True, parallelism is performed via a task queue. If njobs is set to
            "auto", behavior is controlled in the way described above.
            Default: False

        See Also
        --------
        create

        """

        self._run(True, False, njobs=njobs, dynamic=dynamic)

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

        >>> # Now this callback is accessible to the HaloCatalog object
        >>> hc.add_callback("hello_world", "this is my message")

        """

        self.pipeline.add_callback(callback, *args, **kwargs)

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

        self.pipeline.add_quantity(key, *args, **kwargs)

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
        ...     return halo.quantities["particle_mass"] > unyt_quantity(mass_value, "Msun")
        >>> # add it to the register
        >>> add_filter("mass_filter", _my_filter)

        >>> # add the filter to the halo catalog actions
        >>> hc.add_filter("mass_value", 1e12)

        """

        self.pipeline.add_filter(halo_filter, *args, **kwargs)

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
        >>> from yt.extensions.astro_analysis.halo_analysis import HaloCatalog
        >>>
        >>> data_ds = yt.load('Enzo_64/RD0006/RedshiftOutput0006')
        >>> halos_ds = yt.load('rockstar_halos/halos_0.0.bin')
        >>> hc = HaloCatalog(data_ds=data_ds, halos_ds=halos_ds)
        >>>
        >>> # Filter out less massive halos
        >>> hc.add_filter("quantity_value", "particle_mass", ">", 1e14, "Msun")
        >>>
        >>> # Calculate virial radii
        >>> hc.add_recipe("calculate_virial_quantities", ["radius", "matter_mass"])
        >>>
        >>> hc.create()

        """

        self.pipeline.add_recipe(recipe, *args, **kwargs)
