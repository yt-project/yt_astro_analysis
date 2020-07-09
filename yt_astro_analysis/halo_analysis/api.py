"""
API for halo_analysis



"""

#-----------------------------------------------------------------------------
# Copyright (c) yt Development Team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import warnings

from numpy import VisibleDeprecationWarning

warnings.warn(
    "Importing from yt_astro_analysis.halo_analysis.api is deprecated. " +
    "Please import from yt_astro_analysis.halo_analysis or " +
    "yt.extensions.astro_analysis.halo_analysis.",
    VisibleDeprecationWarning, stacklevel=2)

from yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog import \
    HaloCatalog

from yt_astro_analysis.halo_analysis.halo_catalog.halo_callbacks import \
    add_callback

from yt_astro_analysis.halo_analysis.halo_catalog.halo_finding_methods import \
    add_finding_method

from yt_astro_analysis.halo_analysis.halo_catalog.halo_filters import \
    add_filter

from yt_astro_analysis.halo_analysis.halo_catalog.halo_quantities import \
    add_quantity

from yt_astro_analysis.halo_analysis.halo_catalog.halo_recipes import \
    add_recipe
