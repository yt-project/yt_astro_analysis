"""
callbacks, filters, quantities, and recipes for AnalysisPipeline



"""

from yt.utilities.operator_registry import OperatorRegistry

callback_registry = OperatorRegistry()


def add_callback(name, function):
    callback_registry[name] = AnalysisCallback(function)


class AnalysisCallback:
    r"""
    An AnalysisCallback is a function that minimally takes in a target object
    and performs some analysis on it. This function may attach attributes
    to the target object, write out data, etc, but does not return anything.
    """

    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __call__(self, target):
        self.function(target, *self.args, **self.kwargs)
        return True


filter_registry = OperatorRegistry()


def add_filter(name, function):
    filter_registry[name] = AnalysisFilter(function)


class AnalysisFilter(AnalysisCallback):
    r"""
    An AnalysisFilter is a function that minimally takes a target object, performs
    some analysis, and returns either True or False. The return value determines
    whether analysis is continued.
    """

    def __call__(self, target):
        return self.function(target, *self.args, **self.kwargs)


quantity_registry = OperatorRegistry()


def add_quantity(name, function):
    quantity_registry[name] = AnalysisQuantity(function)


def _remove_quantity(name):
    # this is useful to avoid test pollution when using add_quantity in tests
    # but it's not meant as public API
    quantity_registry.pop(name)


class AnalysisQuantity(AnalysisCallback):
    r"""
    An AnalysisQuantity is a function that takes minimally a target object,
    performs some analysis, and then returns a value.
    """

    def __call__(self, target):
        return self.function(target, *self.args, **self.kwargs)


recipe_registry = OperatorRegistry()


def add_recipe(name, function):
    recipe_registry[name] = AnalysisRecipe(function)


class AnalysisRecipe:
    r"""
    An AnalysisRecipe is a function that accepts an AnalysisPipeline and
    adds a series of callbacks, quantities, and filters.
    """

    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __call__(self, pipeline):
        return self.function(pipeline, *self.args, **self.kwargs)
