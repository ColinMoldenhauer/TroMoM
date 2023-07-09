# import rioxarray.raster_array
import numpy as np
import xarray

from rasterio.enums import Resampling

from TroMoM.utils.io import print_raster


def resample_data(xds, factor, method=Resampling.bilinear, verbose=True):
    # TODO: POP: axis labels change to longitude, _FillValue is set, dimensions stay as x/y...
    # TODO: LST: axis labels change to longitude, dimensions stay as x/y...

    # TODO!!: resampling shouldnt use no-data values | done, but isolated values are lost

    new_width = round(xds.rio.width * factor)
    new_height = round(xds.rio.height * factor)

    if verbose: print("reproject | new shape:", (new_height, new_width))

    xds_resampled = xds.rio.reproject(
        xds.rio.crs,
        shape=(new_height, new_width),
        resampling=method,
    )
    if verbose:
        print("in:", xds, sep="\n")
        print("out:", xds_resampled, sep="\n")

    return xds_resampled


def crop2aoi(xds, AOI, buffer=None, verbose=False):
    # TODO: if is dasked -> remove dask if small enough?
    #       The easiest way to convert an xarray data structure from lazy Dask arrays into eager,
    #       in-memory NumPy arrays is to use the load() method:
    """
    Crops data to a user-specified area of interest (AOI).

    Notes:
    - AOI may be larger than data

    :param xds: (xarray.DataArray) The data to be cropped.
    :param AOI: (geopandas.GeoDataFrame) GeoDataFrame specifying the area of interest. Frames with multiple geometries
    are not yet supported, the first geometry will always be chosen for the crop.
    :param buffer: (float | int) Before cropping, the AOI will first be extended (buffer > 0) or shrunk (buffer < 0).
    :param verbose: (bool) Toggles verbosity level.
    :return: (xarray.DataArray) The cropped data.
    """
    # TODO: adapt to multi-area AOIs -> get envelope -> then bounds (probably using GeoSeries.unary_union())
    if buffer is not None: AOI = AOI.buffer(buffer)
    minx, miny, maxx, maxy = AOI.bounds.values[0]
    if verbose: print(f"cropping to (minx, miny, maxx, maxy) = {AOI.bounds.values[0]}")
    clipped = xds.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
    return clipped


def match_data(data_target, *data, resampling=Resampling.bilinear):
    """

    Notes:
    - SMAP data gets stripes: investigate

    :param data_target:
    :param data:
    :param resampling:
    :return:
    """
    out = []
    for xds in data:
        # TODO: check if other params for .reproject() are necessary
        matched = xds.rio.reproject_match(data_target, resampling)
        out.append(matched)
    return out
