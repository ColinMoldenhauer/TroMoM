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


def print_raster(raster, indent=0):
    indent = "\t"*indent
    print(f"{indent}type:", type(raster))
    print(
        f"{indent}shape: {raster.rio.shape}\n"
        f"{indent}resolution: {raster.rio.resolution()}\n"
        f"{indent}bounds: {raster.rio.bounds()}\n"
        f"{indent}CRS: {raster.rio.crs}\n"
        f"{indent}nodata: {raster.rio.nodata}\n"
    )


def read_SMAP(filepath, group_id="Soil_Moisture_Retrieval_Data_AM", variable_id='soil_moisture',
              verbose=1, debug=False):
    '''
    This function extracts and soil moisture from SPL3SMP_E HDF5 file.
    Might work for other Level 3 SMAP products (with similar data structure).
    '''
    # TODO: nodata (-9999)

    def _print_structure(name, obj):
        level = name.count("/")
        indent = "\t"*level
        print(f"{indent}{obj}")

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

        def _find_full_entry(data, axis):
            uniq = np.apply_along_axis(np.unique, axis=axis, arr=data)
            if axis == 1: uniq = uniq.T
            return uniq[1]

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

        match = re.findall(r"(?=_(\d{4})(\d{2})(\d{2})_)", filename)
        if len(match) == 1:
            yyyy, mm, dd = [int(_) for _ in match[0]]
        else:
            raise ValueError(f"File {filename} has {len(match)} date-like patterns, should have exactly one.")

        date = dt.datetime(yyyy, mm, dd)

    # from: https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html
    da = DataArray(
        data=data.T,
        dims=["x", "y"],
        coords=dict(
            x=lon,
            y=lat),
        attrs=dict(
            description="Soil Moisture",    # TODO: extract from h5?
            units="water fraction",         # TODO: confirm
        )
    )
    da.rio.set_crs("epsg:4326", inplace=True)

    if verbose > 0:
        print("\nSMAP file:", filepath)
        print_raster(da, indent=1)

    return data, date


def read_POP(filename, verbose=1):
    # TODO: nodata
    xds = rioxarray.open_rasterio(filename)     # <class 'xarray.core.dataarray.DataArray'>
    if verbose == 1:
        print("\nPOP file:", filename)
        print_raster(xds, indent=1)
    else:
        print(xds)

    return xds


def read_LST(filename, verbose=1):
    # further info: https://land.copernicus.eu/global/products/LST
    # TODO: no-data: -8000
    # note: EPSG:4326 not recognized by riox, need to set it manually (find out difference to NDVI?)

    ds = rioxarray.open_rasterio(filename)     # <class 'xarray.core.dataset.Dataset'>
    if ds.rio.crs != "EPSG:4326":
        warnings.warn("LST CRS not EPSG:4326, setting CRS manually")
        ds.rio.write_crs(4326, inplace=True)
    xds = ds["LST"]

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
    # TODO: no-data: 254: water, 255: no-data
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
