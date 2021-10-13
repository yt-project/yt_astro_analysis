"""
AnalysisPipeline class and member functions



"""

import os

from yt.funcs import ensure_dir
from yt_astro_analysis.halo_analysis.halo_catalog.analysis_operators import (
    callback_registry,
    filter_registry,
    quantity_registry,
    recipe_registry,
)


class AnalysisPipeline:
    def __init__(self, output_dir=None):
        self.actions = []
        self.quantities = []
        self.field_quantities = []
        if output_dir is None:
            output_dir = "."
        self.output_dir = output_dir

    def add_callback(self, callback, *args, **kwargs):
        callback = callback_registry.find(callback, *args, **kwargs)
        self.actions.append(("callback", callback))

    def add_quantity(self, key, *args, **kwargs):
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
        halo_filter = filter_registry.find(halo_filter, *args, **kwargs)
        self.actions.append(("filter", halo_filter))

    def add_recipe(self, recipe, *args, **kwargs):
        halo_recipe = recipe_registry.find(recipe, *args, **kwargs)
        halo_recipe(self)

    def _preprocess(self):
        "Create callback output directories."

        for action_type, action in self.actions:
            if action_type != "callback":
                continue
            my_output_dir = action.kwargs.get("output_dir")
            if my_output_dir is not None:
                new_output_dir = ensure_dir(
                    os.path.join(self.output_dir, my_output_dir)
                )
                action.kwargs["output_dir"] = new_output_dir

    def _process_target(self, target):
        target_filter = True
        for action_type, action in self.actions:
            if action_type == "callback":
                action(target)
            elif action_type == "filter":
                target_filter = action(target)
                if not target_filter:
                    break
            elif action_type == "quantity":
                key, quantity = action
                if callable(quantity):
                    target.quantities[key] = quantity(target)
                else:
                    target._set_field_value(key, quantity)
            else:
                raise RuntimeError("Action must be a callback, filter, or quantity.")

        return target_filter
