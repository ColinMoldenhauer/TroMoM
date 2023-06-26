import os
from osgeo import gdal  # makes import of rasterio work, even though gdal is not explicitly called here

import geopandas as gpd
import matplotlib.pyplot as plt


from utils.io import read_POP, read_LST, read_NDVI, read_SMAP, print_raster
from utils.spatial import crop2aoi, match_data
from utils.utils import get_objs
from utils.visualization import plot_data, plot_data_dual, plot_data_sources, plot_AOI
from utils.validation import validate_resample, validate_crops

# TODO: print everything again: xds, xds.rio, etc...

todo = ["pop", "smap", "lst", "ndvi"]
# todo = ["pop"]

AOI_file = "misc/borneo.geojson"
AOI = gpd.read_file(AOI_file)
f, ax = plot_AOI(AOI)

# test population data (EPSG:4326)
if "pop" in todo:
    dir_pop = "data/POP"
    file_pop = os.path.join(dir_pop, "GHS_POP_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif")
    data_pop = read_POP(file_pop)
    crop_pop = crop2aoi(data_pop, AOI)



# test land surface temperature (EPSG:4326)
if "lst" in todo:
    dir_lst = "data/LST"
    # file_lst = os.path.join(dir_lst, "c_gls_LST_202301021600_GLOBE_GEO_V2.1.1.nc")
    file_lst = os.path.join(dir_lst, "c_gls_LST_202301010200_GLOBE_GEO_V2.1.1.nc")
    data_lst = read_LST(file_lst)
    crop_lst = crop2aoi(data_lst, AOI)



# test NDVI (EPSG:4326)
if "ndvi" in todo:
    dir_ndvi = "data/NDVI"
    file_ndvi = os.path.join(dir_ndvi, "c_gls_NDVI300_202301010000_GLOBE_OLCI_V2.0.1.nc")
    data_ndvi = read_NDVI(file_ndvi)
    crop_ndvi = crop2aoi(data_ndvi, AOI)


# test SMAP (EASE2)
# TODO: confirm lon/lat of SMAP
if "smap" in todo:
    dir_smap = "data/SMAP"
    file_smap = os.path.join(dir_smap, "SMAP_L3_SM_P_E_20230101_R18290_002.h5")
    data_smap = read_SMAP(file_smap)
    crop_smap = crop2aoi(data_smap, AOI)




crops = get_objs("crop_", vars())
plot_data_sources(*crops, AOI=AOI, title="Cropped data")
matched = match_data(crop_ndvi, *crops)
plot_data_sources(*matched, AOI=AOI, title="Matched data")
# matched = match_data(crop_ndvi, crop_smap)
# plot_data_sources(*matched, AOI=AOI, title="Matched data debug")

plt.show()
