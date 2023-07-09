import os
from osgeo import gdal  # makes import of rasterio work, even though gdal is not explicitly called here
import numpy as np      # to use debugger properly

import geopandas as gpd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


from TroMoM.utils.io import read_POP, read_LST, read_NDVI, read_SMAP, read_SMOS, print_raster
from TroMoM.utils.spatial import crop2aoi, match_data
from TroMoM.utils.utils import get_objs
from TroMoM.utils.visualization import plot_data, plot_data_dual, plot_data_sources, plot_AOI, plot_binary_prediction
from TroMoM.utils.validation import validate_resample, validate_crops
from TroMoM.utils.prediction import classify_by_interval
import TroMoM.utils.thresholds as thresh

# TODO: print everything again: xds, xds.rio, etc...
todo = ["pop", "smap", "lst", "ndvi"]
# todo = ["ndvi"]
# todo = ["smos"]

AOI_file = "misc/nigeria.geojson"
# AOI_file = "misc/borneo.geojson"
AOI = gpd.read_file(AOI_file)
# f, ax = plot_AOI(AOI)


if "pop" in todo:
    dir_pop = "data/POP"
    file_pop = os.path.join(dir_pop, "GHS_POP_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif")
    data_pop = read_POP(file_pop)
    crop_pop = crop2aoi(data_pop, AOI)


if "smos" in todo:
    dir_smos = "data/SMOS"
    file_smos = os.path.join(dir_smos, "SM_REPR_MIR_SMUDP2_20200102T235426_20200103T004746_700_300_1.nc")
    data_smos = read_SMOS(file_smos)
    crop_smos = crop2aoi(data_smos, AOI)
    

if "lst" in todo:
    dir_lst = "data/LST"
    file_lst = os.path.join(dir_lst, "c_gls_LST_202301010200_GLOBE_GEO_V2.1.1.nc")
    data_lst = read_LST(file_lst)
    crop_lst = crop2aoi(data_lst, AOI)



if "ndvi" in todo:
    dir_ndvi = "data/NDVI"
    file_ndvi = os.path.join(dir_ndvi, "c_gls_NDVI300_202301010000_GLOBE_OLCI_V2.0.1.nc")
    data_ndvi = read_NDVI(file_ndvi)
    crop_ndvi = crop2aoi(data_ndvi, AOI)
    # print("cropped NDVI: no-data 254:\n", crop_ndvi.load().where(crop_ndvi == 254, drop=True))


# TODO: confirm lon/lat of SMAP
if "smap" in todo:
    dir_smap = "data/SMAP"
    file_smap = os.path.join(dir_smap, "SMAP_L3_SM_P_E_20230102_R18290_002.h5")
    data_smap = read_SMAP(file_smap)
    crop_smap = crop2aoi(data_smap, AOI)


crops = get_objs("crop_", vars())
# plot_data_sources(*crops, AOI=AOI, title="Cropped data")
matched = match_data(crop_smap, *crops)
matched_pop, matched_lst, matched_ndvi, matched_smap = matched
plot_data_sources(*matched, AOI=AOI, title="Matched data")
classif = classify_by_interval(matched, [thresh.SINGLE_INTERVAL_POP,
                                         thresh.SINGLE_INTERVAL_LST,
                                         thresh.SINGLE_INTERVAL_NDVI,
                                         thresh.SINGLE_INTERVAL_SMAP])

cbar = plot_binary_prediction(classif, matched, AOI)

# plt.show()
