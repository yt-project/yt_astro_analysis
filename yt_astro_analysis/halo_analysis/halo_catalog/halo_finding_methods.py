"""
Halo Finding methods



"""

import numpy as np

from yt.data_objects.time_series import DatasetSeries
from yt.utilities.operator_registry import OperatorRegistry
from yt_astro_analysis.halo_analysis.halo_finding.halo_objects import (
    FOFHaloFinder,
    HOPHaloFinder,
)

finding_method_registry = OperatorRegistry()


def add_finding_method(name, function):
    finding_method_registry[name] = HaloFindingMethod(function)


class HaloFindingMethod:
    r"""
    A halo finding method is a callback that performs halo finding on a
    dataset and returns a new dataset that is the loaded halo finder output.
    """

    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args
        if self.args is None:
            self.args = []
        self.kwargs = kwargs
        if self.kwargs is None:
            self.kwargs = {}

    def __call__(self, hc):
        return self.function(hc, *self.args, **self.kwargs)


def _hop_method(hc, **finder_kwargs):
    r"""
    Run the Hop halo finding method.
    """

    ds = hc.data_ds
    if isinstance(ds, DatasetSeries):
        ts = ds
    else:
        ts = DatasetSeries([ds])

    for my_ds in ts:
        halo_list = HOPHaloFinder(my_ds, **finder_kwargs)
        _parse_halo_list(hc, halo_list)


add_finding_method("hop", _hop_method)


def _fof_method(hc, **finder_kwargs):
    r"""
    Run the FoF halo finding method.
    """

    ds = hc.data_ds
    if isinstance(ds, DatasetSeries):
        ts = ds
    else:
        ts = DatasetSeries([ds])

    for my_ds in ts:
        halo_list = FOFHaloFinder(my_ds, **finder_kwargs)
        _parse_halo_list(hc, halo_list)


add_finding_method("fof", _fof_method)


def _rockstar_method(hc, **finder_kwargs):
    r"""
    Run the Rockstar halo finding method.
    """

    from yt_astro_analysis.halo_analysis.halo_finding.rockstar import RockstarHaloFinder

    if "outbase" not in finder_kwargs:
        finder_kwargs["outbase"] = hc.output_basedir

    ds = hc.data_ds
    rh = RockstarHaloFinder(ds, **finder_kwargs)
    rh.run()


add_finding_method("rockstar", _rockstar_method)


def _parse_halo_list(hc, halo_list):
    r"""
    Save the halo list as a HaloCatalog.
    """

    ds = halo_list.ds

    # Set up fields that we want to pull from identified halos and their units
    fields = [
        "particle_identifier",
        "particle_mass",
        "virial_radius",
        "particle_position_x",
        "particle_position_y",
        "particle_position_z",
        "particle_velocity_x",
        "particle_velocity_y",
        "particle_velocity_z",
    ]
    units = ["", "Msun", "kpc"] + ["unitary"] * 3 + ["km/s"] * 3
    ud = dict(zip(fields, units))

    # Set up a dictionary based on those fields
    # with empty arrays where we will fill in their values
    num_halos = len(halo_list)
    halo_properties = {
        f: ds.arr(np.empty(num_halos), unit) for f, unit in zip(fields, units)
    }

    save_particles = getattr(halo_list, "save_particles", False)
    if save_particles:
        n_particles = np.zeros(num_halos, dtype=np.int32)

    # Iterate through the halos pulling out fields.
    for i, halo in enumerate(halo_list):
        halo_properties["particle_identifier"][i] = halo.id
        halo_properties["particle_mass"][i] = halo.virial_mass().to(ud["particle_mass"])
        halo_properties["virial_radius"][i] = halo.virial_radius().to(
            ud["virial_radius"]
        )

        com = halo.center_of_mass()
        halo_properties["particle_position_x"][i] = com[0].to(ud["particle_position_x"])
        halo_properties["particle_position_y"][i] = com[1].to(ud["particle_position_y"])
        halo_properties["particle_position_z"][i] = com[2].to(ud["particle_position_z"])

        bv = halo.bulk_velocity()
        halo_properties["particle_velocity_x"][i] = bv[0].to(ud["particle_velocity_x"])
        halo_properties["particle_velocity_y"][i] = bv[1].to(ud["particle_velocity_y"])
        halo_properties["particle_velocity_z"][i] = bv[2].to(ud["particle_velocity_z"])

        if save_particles:
            n_particles[i] = halo.indices.size

    if save_particles:
        member_ids = np.empty(n_particles.sum(), dtype=np.int64)
        if member_ids.size > 0:
            np.concatenate(
                [halo["particle_index"].astype(np.int64) for halo in halo_list],
                out=member_ids,
            )

        start = n_particles.cumsum() - n_particles
        halo_properties.update(
            {
                "ids": member_ids,
                "particle_number": n_particles,
                "particle_index_start": start,
            }
        )

    field_types = {field: "." for field in halo_properties if field != "ids"}
    if save_particles:
        field_types["ids"] = "particles"

    hc._save(ds=ds, data=halo_properties, field_types=field_types)
