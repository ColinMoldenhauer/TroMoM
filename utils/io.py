import datetime as dt
import os
import re
import warnings

import h5py
import netCDF4
import numpy as np
import rasterio

from rasterio.plot import show


def lonlat_from_netCDF(fn):
    ds = netCDF4.Dataset(fn, "r")
    lat = ds["/latitude"][:].data
    lon = ds["/longitude"][:].data
    return lon, lat


def lonlat_from_double(lon_file, lat_file):
    # Read binary files and reshape to correct size
    lats = np.fromfile(lat_file, dtype=np.float64).reshape((406,964))
    lons = np.fromfile(lon_file, dtype=np.float64).reshape((406,964))
    return lons, lats


def read_SMAP(filepath, group_id="Soil_Moisture_Retrieval_Data_AM", variable_id='soil_moisture', verbose=True):
    '''
    This function extracts and soil moisture from SPL3SMP_E HDF5 file.
    Might work for other Level 3 SMAP products (with similar data structure).

    Parameters
    ----------
    filepath : str
        File path of a SMAP L3 HDF5 file
    Returns
    -------
    soil_moisture_am: numpy.array
    '''
    with h5py.File(filepath, 'r') as f:
        if verbose:
            print(f)
            print("available GROUPs")
            for i, key in enumerate(f.keys()):
                print(f"\t{i}:\t{key}")
            print(f"\n\t--> available VARIABLES for group '{group_id}'")
            for j, var in enumerate(list(f[group_id].keys())):
                print(f"\t\t{j}:\t{var}")

        soil_moisture_am = f[group_id][variable_id][:, :]

        flag_id = 'retrieval_qual_flag' if 'retrieval_qual_flag' in f[group_id] else "retrieval_qual_flag_pm"
        flag_am = f[group_id][flag_id][:, :]

        soil_moisture_am[soil_moisture_am == -9999.0] = np.nan
        # TODO: what does following line do?
        soil_moisture_am[(flag_am >> 0) & 1 == 1] = np.nan

        filename = os.path.basename(filepath)

        match = re.findall(r"(?=_(\d{4})(\d{2})(\d{2})_)", filename)
        if len(match) == 1:
            yyyy, mm, dd = [int(_) for _ in match[0]]
        else:
            raise ValueError(f"File {filename} has {len(match)} date-like patterns, should have exactly one.")

        date = dt.datetime(yyyy, mm, dd)

    return soil_moisture_am, date


def read_POP(filename, verbose=True):
    # no-data, further info: https://land.copernicus.eu/global/products/LST
    # TODO: no-data: -8000
    with rasterio.open(filename) as ds:
        if verbose:
            print("dims:", (ds.height, ds.width))
            print("crs:", ds.crs)
            print("bounds:", ds.bounds)
        data = ds.read(1)

        cols, rows = np.meshgrid(np.arange(ds.width), np.arange(ds.height))
        lon, lat = rasterio.transform.xy(ds.transform, rows, cols)

    if verbose: print("data:", data.shape, type(data), data.dtype)
    if (data < 0).sum() > 1: warnings.warn("Negative values in POP data, please investigate!")
    # TODO: transform to masked array (no-data value -200)
    return data, np.array(lon), np.array(lat)


def read_LST(filename, verbose=True):
    with rasterio.open(filename) as ds:
        print(ds)
        print(dir(ds))
        ds.


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


def read_NDVI(filename, verbose=True):
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
