from rasterio.enums import Resampling
import geopandas as gpd


def resample_data(xds, factor, method=Resampling.bilinear, verbose=True):
    # TODO: POP: axis labels change to longitude, _FillValue is set, dimensions stay as x/y...
    # TODO: LST: axis labels change to longitude, dimensions stay as x/y...

    # TODO!!: resampling shouldnt use no-data values

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


def crop2aoi(xds, AOI, buffer=None, verbose=True):
    """

    Notes:
    - AOI may be larger than data
    :param xds:
    :param AOI:
    :param buffer:
    :param verbose:
    :return:
    """
    # TODO: adapt to multi-area AOIs -> get envelope -> then bounds (probably using GeoSeries.unary_union())
    # TODO: what happens if AOI larger than cropped area?
    if buffer is not None: AOI = AOI.buffer(buffer)
    minx, miny, maxx, maxy = AOI.bounds.values[0]
    if verbose:
        print(f"cropping | (minx, miny, maxx, maxy) = {AOI.bounds.values[0]}")
    clipped = xds.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
    return clipped