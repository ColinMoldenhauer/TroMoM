import datetime as dt
import os
import re
import warnings

import matplotlib.pyplot as plt
import h5py
import netCDF4
import numpy as np
import rioxarray
from xarray import DataArray
import xarray

# TODO: fix attributes for plotting https://docs.xarray.dev/en/stable/user-guide/plotting.html

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


def print_raster(raster, all=False, indent=0):
    indent = "\t"*indent
    print(f"{indent}type:", type(raster))
    if all:
        print("dir:", dir(raster))
        # for attr in list(dir(raster)):
            # if attr.startswith("_") or attr in ["T", "all", "any", "argmax"]: continue
            # print(f"{indent}{attr}: {raster.__getattr__(attr)}")
        # import inspect
        # for i in inspect.getmembers(raster):
        #     # Ignores anything starting with underscore
        #     # (that is, private and protected attributes)
        #     if not i[0].startswith('_'):
        #         # Ignores methods
        #         if not inspect.ismethod(i[1]):
        #             print(i)
        for attr in dir(raster):
            if callable(getattr(raster, attr)): continue
            try:
                print(f"{attr}  | ", getattr(raster, attr))
            except:
                print("error with attr:", attr)
    else:
        print(
            f"{indent}shape: {raster.rio.shape}\n"
            f"{indent}resolution: {raster.rio.resolution()}\n"
            f"{indent}bounds: {raster.rio.bounds()}\n"
            f"{indent}CRS: {raster.rio.crs}\n"
            f"{indent}nodata: {raster.rio.nodata}\n"
        )


def read_SMAP(filepath, group_id="Soil_Moisture_Retrieval_Data_AM", variable_id='soil_moisture',
              verbose=1, debug=False):
    # TODO: mask handling?

    def _print_structure(name, obj):
        level = name.count("/")
        indent = "\t"*level
        print(f"{indent}{obj}")

    def _find_full_entry(data, axis):
        uniq = np.apply_along_axis(np.unique, axis=axis, arr=data)
        if axis == 1: uniq = uniq.T
        return uniq[1]

    suffix = "_pm" if group_id.endswith("_PM") else ""
        
    with h5py.File(filepath, 'r') as f:
        if verbose > 1:
            print(f)
            print("available GROUPs")
            for i, key in enumerate(f.keys()):
                print(f"\t{i}:\t{key}")
            print(f"\n\t--> available VARIABLES for group '{group_id}'")
            for j, var in enumerate(list(f[group_id].keys())):
                print(f"\t\t{j}:\t{var}")

            f.visititems(_print_structure)

        data = f[group_id][variable_id][:, :]
        flag = f[group_id]['retrieval_qual_flag' + suffix][:, :]

        lon_all = f[group_id]['longitude' + suffix][:, :]
        lat_all = f[group_id]['latitude' + suffix][:, :]
        lon = _find_full_entry(lon_all, axis=0)
        lat = _find_full_entry(lat_all, axis=1)

        if debug:
            fig, (ax_data, ax_lon, ax_lat) = plt.subplots(1, 3)
            ax_data.imshow(data)
            ax_data.set_title("data")
            ax_lon.imshow(lon_all)
            ax_lon.set_title("lon")
            ax_lat.imshow(lat_all)
            ax_lat.set_title("lat")
            plt.show()

            fig, (ax_lon, ax_lat) = plt.subplots(1, 2)
            ax_lon.plot(lon)
            ax_lon.set_title("lon")
            ax_lat.plot(lat)
            ax_lat.set_title("lat")
            plt.show()


        data[data == -9999.0] = np.nan
        # TODO: what does following line do?
        data[(flag >> 0) & 1 == 1] = np.nan

        filename = os.path.basename(filepath)

        # TODO: time necessary still?
        match = re.findall(r"(?=_(\d{4})(\d{2})(\d{2})_)", filename)
        if len(match) == 1:
            yyyy, mm, dd = [int(_) for _ in match[0]]
        else:
            raise ValueError(f"File {filename} has {len(match)} date-like patterns, should have exactly one.")

        date = dt.datetime(yyyy, mm, dd)

    # from: https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html
    da = DataArray(
        data=data,
        dims=["y", "x"],
        coords=dict(
            x=lon,
            y=lat),
        attrs=dict(
            description="Soil Moisture",    # TODO: extract from h5?
            units="water fraction",         # TODO: confirm
        )
    )
    da.rio.set_crs("epsg:4326", inplace=True)
    da.rio.set_nodata(-9999.0, inplace=True)

    if verbose > 0:
        print("\nSMAP file:", filepath)
        print_raster(da, indent=1)

    return da


def read_POP(filename, verbose=2):
    """

    Notes:
    - masked=True | doesnt change anything, probably full data in snippet -> check with whole data maybe

    :param filename:
    :param verbose:
    :return:
    """
    # TODO: units
    xds = rioxarray.open_rasterio(filename, masked=True, decode_cf=True)     # <class 'xarray.core.dataarray.DataArray'>
    xds.rio.set_nodata(-200, inplace=True)
    if verbose == 1:
        print("\nPOP file:", filename)
        print_raster(xds, indent=1)
    elif verbose > 1:
        print(xds)

    return xds


import functools

def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)

def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))

def _copy_attributes(ref, new, attrs):
    for attr in attrs:
        print("\nbefore:", attr, ":", rgetattr(new, attr))
        rsetattr(new, attr, rgetattr(ref, attr))
        print("after:", attr, ":", rgetattr(new, attr))



def read_LST(filename, raw=False, verbose=1):
    """
    Reads Land Surface Temperature data, obtained from https://land.copernicus.eu/global/products/LST.
    The digital value needs to be transformed to the physical range as follows: PV = Scaling * DN + Offset.

    Notes:
    - open_rasterio(masked=True) changes _FillValue to from -8000 to 3.402823466e+38

    :param filename: (str) Filename of input file (.nc NetCDF file)
    :param raw: (bool) Default False | Whether to transform data into physical values right away or only read raw data
    :param verbose: (int) Toggles verbosity level
    :return: (xarray.DataArray) Georeferenced data array object
    """
    # TODO optional: EPSG:4326 not recognized by riox, need to set it manually (find out difference to NDVI?)

    xarray.set_options(keep_attrs=True)

    ds = rioxarray.open_rasterio(filename, masked=True)     # <class 'xarray.core.dataset.Dataset'>
    if ds.rio.crs != "EPSG:4326": ds.rio.write_crs(4326, inplace=True)

    xds_raw = ds["LST"]
    if raw:
        xds = xds_raw
    if not raw:
        xds = xds_raw/100  # °C
        xds.rio.write_crs(input_crs=xds_raw.rio.crs, grid_mapping_name=xds_raw.rio.grid_mapping, inplace=True)
        xds.attrs["units"] = "°C"
        xds.attrs["valid_range"] = list(np.array([-7000.0, 8000.])/100)


    if verbose: print("\nLST file:", filename)
    if verbose == 1:
        print_raster(xds, indent=1)
    elif verbose == 2:
        print(xds)
    elif verbose == 3:
        print(ds)

    return xds


def read_NDVI(filename, verbose=1):
    # further info: https://land.copernicus.eu/global/products/NDVI
    # TODO: no-data: 254: water, 255: no-data multiple values? probably set all to 255
    # TODO: units
    # note: EPSG:4326 recognized correctly

    ds = rioxarray.open_rasterio(filename)
    xds = ds["NDVI"]
    assert xds.rio.crs == "EPSG:4326", "CRS not EPSG:4326, fix this!"

    if verbose:
        print("\nNDVI file:", filename)
    if verbose == 1:
        print_raster(xds, indent=1)
    elif verbose == 2:
        print(xds)
    else:
        print(ds)
    return xds
