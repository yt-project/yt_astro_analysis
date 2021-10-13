"""
HaloCatalog filters



"""

import numpy as np

from yt.utilities.on_demand_imports import _scipy as scipy
from yt_astro_analysis.halo_analysis.halo_catalog.analysis_operators import add_filter


def quantity_value(halo, field, operator, value, units):
    r"""
    Filter based on a value in the halo quantities dictionary.

    Parameters
    ----------
    halo : Halo object
        The Halo object to be provided by the HaloCatalog.
    field : string
        The field used for the evaluation.
    operator : string
        The comparison operator to be used ("<", "<=", "==", ">=", ">", etc.)
    value : numneric
        The value to be compared against.
    units : string
        Units of the value to be compared.

    """

    if field not in halo.quantities:
        raise RuntimeError("Halo object does not contain %s quantity." % field)

    h_value = halo.quantities[field].in_units(units).to_ndarray()
    return eval(f"{h_value} {operator} {value}")


add_filter("quantity_value", quantity_value)


def not_subhalo(halo, field_type="halos"):
    """
    Only return true if this halo is not a subhalo.

    This is used for halo finders such as Rockstar that output parent
    and subhalos together.
    """

    if not hasattr(halo.halo_catalog, "parent_dict"):
        halo.halo_catalog.parent_dict = _create_parent_dict(
            halo.halo_catalog.data_source, ptype=field_type
        )
    return (
        halo.halo_catalog.parent_dict[int(halo.quantities["particle_identifier"])] == -1
    )


add_filter("not_subhalo", not_subhalo)


def _create_parent_dict(data_source, ptype="halos"):
    """
    Create a dictionary of halo parents to allow for filtering of subhalos.

    For a pair of halos whose distance is smaller than the radius of at least
    one of the halos, the parent is defined as the halo with the larger radius.
    Parent halos (halos with no parents of their own) have parent index values of -1.
    """
    pos = np.rollaxis(
        np.array(
            [
                data_source[ptype, "particle_position_x"].in_units("Mpc"),
                data_source[ptype, "particle_position_y"].in_units("Mpc"),
                data_source[ptype, "particle_position_z"].in_units("Mpc"),
            ]
        ),
        1,
    )
    rad = data_source[ptype, "virial_radius"].in_units("Mpc").to_ndarray()
    ids = data_source[ptype, "particle_identifier"].to_ndarray().astype("int")
    parents = -1 * np.ones_like(ids, dtype="int")
    boxsize = data_source.ds.domain_width.in_units("Mpc")
    my_tree = scipy.spatial.cKDTree(pos, boxsize=boxsize)

    for i in range(ids.size):
        neighbors = np.array(my_tree.query_ball_point(pos[i], rad[i], p=2))
        if neighbors.size > 1:
            parents[neighbors] = ids[neighbors[np.argmax(rad[neighbors])]]

    parents[ids == parents] = -1
    parent_dict = dict(zip(ids, parents))
    return parent_dict
