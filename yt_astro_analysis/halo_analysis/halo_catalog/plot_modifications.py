import warnings

import numpy as np

from yt.data_objects.data_containers import YTDataContainer
from yt.data_objects.static_output import Dataset
from yt.visualization.plot_modifications import PlotCallback


class HaloCatalogCallback(PlotCallback):
    """
    Plots circles at the locations of all the halos
    in a halo catalog with radii corresponding to the
    virial radius of each halo.

    Parameters
    ----------
    halo_catalog : :class:`~yt.data_objects.static_output.Dataset`,
        :class:`~yt.data_objects.data_containers.YTDataContainer`, or
        :class:`~yt_astro_analysis.halo_analysis.halo_catalog.halo_catalog.HaloCatalog`
        The object containing halos to be overplotted. This can
        be a HaloCatalog object, a loaded halo catalog dataset,
        or a data container from a halo catalog dataset.
    circle_args : list
        Contains the arguments controlling the
        appearance of the circles, supplied to the
        Matplotlib patch Circle.
    width : tuple
        The width over which to select halos to plot,
        useful when overplotting to a slice plot. Accepts
        a tuple in the form (1.0, 'Mpc').
    annotate_field : str
        A field contained in the
        halo catalog to add text to the plot near the halo.
        Example: annotate_field = 'particle_mass' will
        write the halo mass next to each halo.
    radius_field : str
        A field contained in the halo
        catalog to set the radius of the circle which will
        surround each halo. Default: 'virial_radius'.
    center_field_prefix : str
        Accepts a field prefix which will
        be used to find the fields containing the coordinates
        of the center of each halo. Ex: 'particle_position'
        will result in the fields 'particle_position_x' for x
        'particle_position_y' for y, and 'particle_position_z'
        for z. Default: 'particle_position'.
    text_args : dict
        Contains the arguments controlling the text
        appearance of the annotated field.
    factor : float
        A number the virial radius is multiplied by for
        plotting the circles. Ex: factor = 2.0 will plot
        circles with twice the radius of each halo virial radius.

    Examples
    --------

    >>> import yt
    >>> dds = yt.load("Enzo_64/DD0043/data0043")
    >>> hds = yt.load("rockstar_halos/halos_0.0.bin")
    >>> p = yt.ProjectionPlot(
    ...     dds, "x", ("gas", "density"), weight_field=("gas", "density")
    ... )
    >>> p.annotate_halos(hds)
    >>> p.save()

    >>> # plot a subset of all halos
    >>> import yt
    >>> dds = yt.load("Enzo_64/DD0043/data0043")
    >>> hds = yt.load("rockstar_halos/halos_0.0.bin")
    >>> # make a region half the width of the box
    >>> dregion = dds.box(
    ...     dds.domain_center - 0.25 * dds.domain_width,
    ...     dds.domain_center + 0.25 * dds.domain_width,
    ... )
    >>> hregion = hds.box(
    ...     hds.domain_center - 0.25 * hds.domain_width,
    ...     hds.domain_center + 0.25 * hds.domain_width,
    ... )
    >>> p = yt.ProjectionPlot(
    ...     dds,
    ...     "x",
    ...     ("gas", "density"),
    ...     weight_field=("gas", "density"),
    ...     data_source=dregion,
    ...     width=0.5,
    ... )
    >>> p.annotate_halos(hregion)
    >>> p.save()

    >>> # plot halos from a HaloCatalog
    >>> import yt
    >>> from yt.extensions.astro_analysis.halo_analysis import HaloCatalog
    >>> dds = yt.load("Enzo_64/DD0043/data0043")
    >>> hds = yt.load("rockstar_halos/halos_0.0.bin")
    >>> hc = HaloCatalog(data_ds=dds, halos_ds=hds)
    >>> p = yt.ProjectionPlot(
    ...     dds, "x", ("gas", "density"), weight_field=("gas", "density")
    ... )
    >>> p.annotate_halos(hc)
    >>> p.save()

    """

    _type_name = "halos"
    region = None
    _descriptor = None
    _supported_geometries = ("cartesian", "spectral_cube")

    def __init__(
        self,
        halo_catalog,
        circle_args=None,
        circle_kwargs=None,
        width=None,
        annotate_field=None,
        radius_field="virial_radius",
        center_field_prefix="particle_position",
        text_args=None,
        font_kwargs=None,
        factor=1.0,
    ):

        PlotCallback.__init__(self)
        def_circle_args = {"edgecolor": "white", "facecolor": "None"}
        def_text_args = {"color": "white"}

        if isinstance(halo_catalog, YTDataContainer):
            self.halo_data = halo_catalog
        elif isinstance(halo_catalog, Dataset):
            self.halo_data = halo_catalog.all_data()
        else:
            # assuming halo_catalog is a HaloCatalog instance
            # but do so with a EAFP pattern instead of LBYL to workaround
            # conflicting namespaces, see https://github.com/yt-project/yt_astro_analysis/issues/131
            try:
                if halo_catalog.data_source.ds == halo_catalog.halos_ds:
                    self.halo_data = halo_catalog.data_source
                else:
                    self.halo_data = halo_catalog.halos_ds.all_data()
            except AttributeError as exc:
                raise TypeError(
                    "halo_catalog argument must be a HaloCatalog object, "
                    "a dataset, or a data container. "
                    f"Received {halo_catalog} with type {type(halo_catalog)}"
                ) from exc

        self.width = width
        self.radius_field = radius_field
        self.center_field_prefix = center_field_prefix
        self.annotate_field = annotate_field
        if circle_kwargs is not None:
            circle_args = circle_kwargs
            warnings.warn(
                "The circle_kwargs keyword is deprecated.  Please "
                "use the circle_args keyword instead."
            )
        if font_kwargs is not None:
            text_args = font_kwargs
            warnings.warn(
                "The font_kwargs keyword is deprecated.  Please use "
                "the text_args keyword instead."
            )
        if circle_args is None:
            circle_args = def_circle_args
        self.circle_args = circle_args
        if text_args is None:
            text_args = def_text_args
        self.text_args = text_args
        self.factor = factor

    def __call__(self, plot):
        from matplotlib.patches import Circle

        data = plot.data
        x0, x1, y0, y1 = self._physical_bounds(plot)
        xx0, xx1, yy0, yy1 = self._plot_bounds(plot)

        halo_data = self.halo_data
        axis_names = plot.data.ds.coordinates.axis_name
        xax = plot.data.ds.coordinates.x_axis[data.axis]
        yax = plot.data.ds.coordinates.y_axis[data.axis]
        field_x = f"{self.center_field_prefix}_{axis_names[xax]}"
        field_y = f"{self.center_field_prefix}_{axis_names[yax]}"
        field_z = f"{self.center_field_prefix}_{axis_names[data.axis]}"

        # Set up scales for pixel size and original data
        pixel_scale = self._pixel_scale(plot)[0]
        units = plot.xlim[0].units

        # Convert halo positions to code units of the plotted data
        # and then to units of the plotted window
        px = halo_data[("all", field_x)][:].in_units(units)
        py = halo_data[("all", field_y)][:].in_units(units)

        xplotcenter = (plot.xlim[0] + plot.xlim[1]) / 2
        yplotcenter = (plot.ylim[0] + plot.ylim[1]) / 2

        xdomaincenter = plot.ds.domain_center[xax]
        ydomaincenter = plot.ds.domain_center[yax]

        xoffset = xplotcenter - xdomaincenter
        yoffset = yplotcenter - ydomaincenter

        xdw = plot.ds.domain_width[xax].to(units)
        ydw = plot.ds.domain_width[yax].to(units)

        modpx = np.mod(px - xoffset, xdw) + xoffset
        modpy = np.mod(py - yoffset, ydw) + yoffset

        px[modpx != px] = modpx[modpx != px]
        py[modpy != py] = modpy[modpy != py]

        px, py = self._convert_to_plot(plot, [px, py])

        # Convert halo radii to a radius in pixels
        radius = halo_data[("all", self.radius_field)][:].in_units(units)
        radius = np.array(radius * pixel_scale * self.factor)

        if self.width:
            pz = halo_data[("all", field_z)][:].in_units("code_length")
            c = data.center[data.axis]

            # I should catch an error here if width isn't in this form
            # but I dont really want to reimplement get_sanitized_width...
            width = data.ds.arr(self.width[0], self.width[1]).in_units("code_length")

            indices = np.where((pz > c - 0.5 * width) & (pz < c + 0.5 * width))

            px = px[indices]
            py = py[indices]
            radius = radius[indices]

        for x, y, r in zip(px, py, radius):
            plot._axes.add_artist(Circle(xy=(x, y), radius=r, **self.circle_args))

        plot._axes.set_xlim(xx0, xx1)
        plot._axes.set_ylim(yy0, yy1)

        if self.annotate_field:
            annotate_dat = halo_data[("all", self.annotate_field)]
            texts = [f"{float(dat):g}" for dat in annotate_dat]
            labels = []
            for pos_x, pos_y, t in zip(px, py, texts):
                labels.append(plot._axes.text(pos_x, pos_y, t, **self.text_args))

            # Set the font properties of text from this callback to be
            # consistent with other text labels in this figure
            self._set_font_properties(plot, labels, **self.text_args)
