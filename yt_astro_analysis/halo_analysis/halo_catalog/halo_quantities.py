"""
Halo quantity object



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2013-2017, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from yt.utilities.operator_registry import \
     OperatorRegistry

from yt_astro_analysis.halo_analysis.halo_catalog.halo_callbacks import \
    HaloCallback

quantity_registry = OperatorRegistry()

def add_quantity(name, function):
    quantity_registry[name] = HaloQuantity(function)

class HaloQuantity(HaloCallback):
    r"""
    A HaloQuantity is a function that takes minimally a Halo object, 
    performs some analysis, and then returns a value that is assigned 
    to an entry in the Halo.quantities dictionary.
    """
    def __init__(self, function, *args, **kwargs):
        HaloCallback.__init__(self, function, args, kwargs)
        
    def __call__(self, halo):
        return self.function(halo, *self.args, **self.kwargs)
