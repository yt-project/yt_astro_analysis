"""
Halo object.



"""


class Halo:
    def __init__(self, halo_catalog, data_source, index):
        self.halo_catalog = halo_catalog
        self.data_source = data_source
        self.index = index
        self.quantities = {}

    def _get_field_value(self, fieldname):
        return self.data_source[fieldname][self.index]

    def _set_field_value(self, fieldkey, fieldname):
        self.quantities[fieldkey] = self._get_field_value(fieldname)
