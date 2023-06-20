"""
Following functions are development remnants and are only kept for reference.
"""

import warnings

import netCDF4
import numpy as np
import rasterio
from rasterio.control import GroundControlPoint
from rasterio.transform import from_gcps
from rioxarray import rioxarray

from utils.io import print_raster


def read_SMAP_riox(filename, verbose=True):
    # does not work
    xds = rioxarray.open_rasterio(filename)
    if verbose:
        print("\nPOP file:", filename)
        print_raster(xds, indent=1)
        print("\t", dir(xds))

    return xds


def read_POP_rio(filename, verbose=True):
    with rasterio.open(filename) as ds:
        if verbose: print("profile:", ds.profile)
        data = ds.read(1)

        cols, rows = np.meshgrid(np.arange(ds.width), np.arange(ds.height))
        lon, lat = rasterio.transform.xy(ds.transform, rows, cols)

    if verbose: print("data:", data.shape, type(data), data.dtype)
    if (data < 0).sum() > 1: warnings.warn("Negative values in POP data, please investigate!")
    # TODO: transform to masked array (no-data value -200)
    return data, np.array(lon), np.array(lat)


def read_LST_rionCDF(filename, verbose=True):
    nc = netCDF4.Dataset(filename, "r")
    print(nc)
    lon = nc["lon"]
    lat = nc["lat"]
    width = nc.dimensions["lon"].size
    height = nc.dimensions["lat"].size

    tl = GroundControlPoint(0, 0, lat[0], lon[0])
    bl = GroundControlPoint(height, 0, lat[-1], lon[0])
    br = GroundControlPoint(height, width, lat[-1], lon[-1])
    tr = GroundControlPoint(0, width, lat[0], lon[-1])
    gcps = [tl, bl, br, tr]

    transform = from_gcps(gcps)
    crs = 'epsg:4326'

    print("estimated transform:\n", transform, sep="")

    with rasterio.open(filename, "r+") as ds:
        if verbose:
            print("profile:", ds.profile)
            print("lon:", lon[0], lon[-1], "max", lon[:].max(), "min", lon[:].min())
            print("lat:", lat[0], lat[-1], "max", lat[:].max(), "min", lat[:].min())

        ds.crs = crs
        ds.transform = transform


def read_LST_nCDF(filename, verbose=True):
    ds = netCDF4.Dataset(filename, "r")
    lst_masked = ds["LST"][:]
    if verbose:
        print(ds)
        print("time:", ds["time"][:])
        print("LST:", ds["LST"][:].shape, type(ds["LST"][:]))
        print("lat:", ds["lat"][:].shape, type(ds["lat"][:]))
        print("lon:", ds["lon"][:].shape, type(ds["lon"][:]))

    if verbose: print(f"LST masked:", lst_masked.mask.sum(), lst_masked.mask.sum()/lst_masked.size)
    return lst_masked


def read_NDVI_nCDF(filename, verbose=True):
    # no-data, further info: https://land.copernicus.eu/global/products/NDVI
    # TODO: no-data: 254: water, 255: no-data

    ds = netCDF4.Dataset(filename, "r")
    ndvi_masked = ds["NDVI"][:]
    if verbose:
        print(ds)
        print("time:", ds["time"][:])
        print("NDVI:", ds["NDVI"][:].shape, type(ds["LST"][:]))
        print("lat:", ds["lat"][:].shape, type(ds["lat"][:]))
        print("lon:", ds["lon"][:].shape, type(ds["lon"][:]))

    if verbose: print(f"NDVI masked:", ndvi_masked.mask.sum(), ndvi_masked.mask.sum() / ndvi_masked.size)
    return ndvi_masked


def read_NDVI_tiff(filename, verbose=True):
    with rasterio.open(filename) as ds:
        if verbose:
            print("bands:", ds.count)
            print("dims:", (ds.height, ds.width))
            print("crs:", ds.crs)
            print("bounds:", ds.bounds)
        data = ds.read(1)

    if verbose: print("data:", data.shape, type(data), data.dtype)
    if (data < 0).sum() > 1: warnings.warn("Negative values in NDVI data, please investigate!")
    # TODO: transform to masked array
    return data
