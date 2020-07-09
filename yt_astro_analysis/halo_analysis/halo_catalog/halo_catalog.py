"""
HaloCatalog class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) yt Development Team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from yt.funcs import \
    mylog
from yt.utilities.parallel_tools.parallel_analysis_interface import \
    parallel_blocking_call

from yt_astro_analysis.halo_analysis.halo_catalog.analysis_pipeline import \
    AnalysisPipeline
from yt_astro_analysis.halo_analysis.halo_catalog.halo_finding_methods import \
    finding_method_registry
from yt_astro_analysis.halo_analysis.halo_catalog.halo_object import \
    Halo

_default_fields = \
  ["particle_identifier", "particle_mass", "virial_radius"] + \
  ["particle_position_" + ax for ax in "xyz"] + \
  ["particle_velocity_" + ax for ax in "xyz"]

class HaloCatalog(AnalysisPipeline):
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

    _target_cls = Halo

    def __init__(self, halos_ds=None, data_ds=None,
                 data_source=None, halo_field_type='all',
                 finder_method=None, finder_kwargs=None,
                 output_dir="halo_catalogs"):
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

        self.finder_method_name = finder_method
        if finder_kwargs is None:
            finder_kwargs = {}
        if finder_method is not None:
            finder_method = finding_method_registry.find(
                finder_method, **finder_kwargs)
        self.finder_method = finder_method

        super(HaloCatalog, self).__init__(
            output_dir=output_dir, data_source=data_source)

    def _add_default_quantities(self):
        if self.halos_ds is None:
            return

        field_type = self.halo_field_type
        for field in _default_fields:
            field_name = (field_type, field)
            if field_name not in self.halos_ds.derived_field_list:
                mylog.warning("Halo dataset %s has no field %s." %
                              (self.halos_ds, str(field_name)))
                continue
            self.add_quantity(field, from_data_source=True,
                              field_type=field_type)

    @parallel_blocking_call
    def _run(self, save_targets, save_catalog,
             njobs='auto', dynamic=False):
        r"""
        Run the requested halo analysis.

        Parameters
        ----------
        save_halos : bool
            If True, a list of all Halo objects is retained under the "halo_list"
            attribute.  If False, only the compiles quantities are saved under the
            "catalog" attribute.
        save_catalog : bool
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

        # Find halos.
        if self.halos_ds is None:
            self.finder_method(self)
            return

        super(HaloCatalog, self)._run(save_targets, save_catalog,
                                      njobs=njobs, dynamic=dynamic)
