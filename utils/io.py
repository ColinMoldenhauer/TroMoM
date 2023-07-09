import datetime as dt
import os
import re
import warnings

import cftime
import matplotlib.pyplot as plt
import h5py
import netCDF4
import numpy as np
import rioxarray
from xarray import DataArray
import xarray

# TODO: inspect outliers (LST = -3.33 zB) and handle them
# TODO: determine necessary data types (save space by using int/float16)
# TODO: compare extracted EASE coordinates with misc/ coordinate data
# TODO optional: unify verbosity handling
""" Notes
- "you can write the CF attributes" https://corteva.github.io/rioxarray/stable/getting_started/crs_management.html
"""

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
        for attr in dir(raster):
            if callable(getattr(raster, attr)): continue
            try:
                print(f"{attr: <10}  | ", getattr(raster, attr))
            except:
                print("error with attr:", attr)
    else:
        print(
            f"{indent}name: {raster.name}\n"
            f"{indent}shape: {raster.rio.shape}\n"
            f"{indent}resolution: {raster.rio.resolution()}\n"
            f"{indent}bounds: {raster.rio.bounds()}\n"
            f"{indent}CRS: {raster.rio.crs}\n"
            f"{indent}nodata: {raster.rio.nodata}\n"
        )


def read_SMAP(filepath, group_id="Soil_Moisture_Retrieval_Data_AM", variable_id='soil_moisture',
              verbose=False, debug=False):
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
        if verbose:
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

        # TODO: below line necessary for xarray?
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
        name="Soil Moisture",
        data=data,
        dims=["y", "x"],
        coords=dict(
            x=lon,
            y=lat),
        attrs=dict(
            description="Soil Moisture",            # TODO: extract from h5?
            units="water fraction cm³/cm³",         # TODO: confirm
            time=cftime.DatetimeGregorian(yyyy, mm, dd)
        )
    )
    da.rio.set_crs("epsg:4326", inplace=True)
    da.rio.set_nodata(np.nan, inplace=True)

    return da


def read_POP(filename):
    """

    Notes:
    - masked=True | doesnt change anything, probably full data in snippet -> check with whole data maybe

    :param filename:
    :return:
    """
    # TODO: check if nodata is available -> else maybe mask with ocean mask??
    xds = rioxarray.open_rasterio(filename, masked=True, decode_cf=True)[0]     # has only one "band" in first axis
    xds.attrs["units"] = "#inhabitants"
    xds.name = "POP"
    xds.rio.set_nodata(np.nan, inplace=True)

    return xds


def read_LST(filename, raw=False):
    """
    Reads Land Surface Temperature data, obtained from https://land.copernicus.eu/global/products/LST.
    The digital value needs to be transformed to the physical range as follows: PV = Scaling * DN + Offset.

    Notes:
    - open_rasterio(masked=True) changes _FillValue to from -8000 to 3.402823466e+38

    :param filename: (str) Filename of input file (.nc NetCDF file)
    :param raw: (bool) Whether to transform data into physical values right away or only read raw data
    :return: (xarray.DataArray) Georeferenced data array object
    """
    # TODO optional: EPSG:4326 not recognized by riox, need to set it manually (find out difference to NDVI?)

    xarray.set_options(keep_attrs=True)

    ds = rioxarray.open_rasterio(filename, masked=True)
    if ds.rio.crs != "EPSG:4326": ds.rio.write_crs(4326, inplace=True)

    xds_raw = ds["LST"][0]          # only one timestamp in first axis
    if raw:
        xds = xds_raw
    else:
        xds = xds_raw/100  # °C
        xds.attrs = xds_raw.attrs
        xds.rio.write_crs(input_crs=xds_raw.rio.crs, grid_mapping_name=xds_raw.rio.grid_mapping, inplace=True)
        xds.attrs["units"] = "°C"
        xds.attrs["valid_range"] = [-70, 80]

    xds.rio.set_nodata(np.nan, inplace=True)
    # TODO: check if raw also has no nodata, set no-data for either

    return xds


def read_NDVI(filename, raw=False, chunks=4000):
    """
    Reads NDVI data, obtained from https://land.copernicus.eu/global/products/NDVI.
    Makes use of dask chunking mechanisms and is hence suitable for very large files.
    The digital value needs to be transformed to the physical range as follows: PV = Scaling * DN + Offset.

    Notes:
    - EPSG:4326 recognized correctly

    :param filename: (str) Filename of input file (.nc NetCDF file)
    :param raw: (bool) Whether to transform data into physical values right away or only read raw data
    :return: (xarray.DataArray) Georeferenced data array object
    """
    # TODO: no-data: 254: water, 255: no-data multiple values? probably set all to 255
    #       check handling...
    # TODO: use ds.NDVI_unc, ds.NOBS, ds.QFLAG
    # TODO: understand valid NDVI value range, why not [-1, 1]

    ds = rioxarray.open_rasterio(filename, masked=True, chunks={'x': chunks, 'y': chunks})
    xds_raw = ds["NDVI"][0]             # only one timestamp in first axis
    if raw:
        xds = xds_raw
    else:
        xds = xds_raw/250 - 0.08
        xds.attrs = xds_raw.attrs
        xds.rio.write_crs(input_crs=xds_raw.rio.crs, grid_mapping_name=xds_raw.rio.grid_mapping, inplace=True)
        xds.attrs["units"] = "-"
        xds.attrs["valid_range"] = [-0.08, 0.92]
    assert xds.rio.crs == "EPSG:4326", "CRS not EPSG:4326, fix this!"

    xds.rio.set_nodata(np.nan, inplace=True)
    return xds


def read_SMOS(filename):
    """
    Reads SMOS data.

    Notes:

    :param filename: (str) Filename of input file (.nc NetCDF file)
    :return: (xarray.DataArray) Georeferenced data array object
    """
    # TODO optional: EPSG:4326 not recognized by riox, need to set it manually (find out difference to NDVI?)

    xarray.set_options(keep_attrs=True)

    ds = rioxarray.open_rasterio(filename, masked=True)     # <class 'xarray.core.dataset.Dataset'>
    if ds.rio.crs != "EPSG:4326":
        print("warning, no EPSG:4326 in SMOS")
        ds.rio.write_crs(4326, inplace=True)

    print("ds:")
    print(ds)

    xds = ds["SMOS"]

    print("da:")
    print(xds)

    print()
    print("rio")
    print_raster(xds)

    return xds
