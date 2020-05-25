"""
Halo object.



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2013, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from yt_astro_analysis.halo_analysis.halo_catalog.analysis_pipeline import \
    AnalysisTarget

class Halo(AnalysisTarget):
    _container_name = "halo_catalog"

    def _get_field_value(self, fieldname, data_source, index):
        return data_source[fieldname][index]
