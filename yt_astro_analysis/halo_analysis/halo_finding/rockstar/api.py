"""
API for Rockstar halo finding



"""

# -----------------------------------------------------------------------------
# Copyright (c) yt Development Team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import warnings

from numpy import VisibleDeprecationWarning

warnings.warn(
    "Running the RockstarHaloFinder directly is deprecated. "
    + "Please run using the HaloCatalog. See "
    + "https://yt-astro-analysis.readthedocs.io for more information.",
    VisibleDeprecationWarning,
    stacklevel=2,
)

from yt_astro_analysis.halo_analysis.halo_finding.rockstar.rockstar import (
    RockstarHaloFinder,
)
