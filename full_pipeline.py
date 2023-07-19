import os
from osgeo import gdal  # makes import of rasterio work, even though gdal is not explicitly called here
import numpy as np      # to use debugger properly

import geopandas as gpd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from TroMoM.utils.io import read_POP, read_LST, read_NDVI, read_SMAP, read_SMOS, print_raster, save_tiff
from TroMoM.utils.spatial import crop2aoi, match_data
from TroMoM.utils.utils import get_objs
from TroMoM.utils.visualization import plot_data, plot_data_dual, plot_data_sources, plot_AOI, plot_binary_prediction, \
    plot_risk_estimation
from TroMoM.utils.validation import validate_resample, validate_crops
from TroMoM.utils.prediction import classify_by_interval, risk_estimation
import TroMoM.utils.thresholds as thresh

#################### SETTINGS ########################
# decide which data sources to include/process
todo = ["pop", "smap", "lst", "ndvi"]
match_parent_str = "POP"

show_plots = True
save_to_file = not show_plots
if save_to_file: plt.rcParams['figure.figsize'] = [18, 10]


AOI_file = "misc/nigeria.geojson"
# AOI_file = "misc/borneo.geojson"
#######################################################


if not show_plots: plt.ioff()
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

# decide which data source should the others be equalized to
match_parent = get_objs(f"crop_{match_parent_str.lower()}", vars())[0]
matched = match_data(match_parent, *crops)


# equalize data resolution, extent, etc...
matched_pop, matched_lst, matched_ndvi, matched_smap = matched

# ... and plot the matched data
plot_data_sources(*crops, AOI=AOI, title="Cropped data")
fig_data_sources = plot_data_sources(*matched, AOI=AOI, title="Matched data")


threshs_multi = thresh.threshs_multi
threshs_multi[0] = thresh.estimate_quantile_thresholds([.1, .5, .8, .95], matched_pop)

# plot multi risk
risk_estim_multi = risk_estimation(matched, threshs_multi, discrete=True, single=True)
fig_risk_per_layer, _ = plot_risk_estimation(risk_estim_multi, matched, threshs_multi, AOI, discrete=True, title="Risk per Layer")
if save_to_file:
    save_tiff(matched, [f"predictions/{match_parent_str}/matched_{d_.name}.tiff" for d_ in matched])
    save_tiff(risk_estim_multi, [f"predictions/{match_parent_str}/risk_per_layer_{d_.name}.tiff" for d_ in matched])

# plot risk estimation
risk_estim_disc = risk_estimation(matched, threshs_multi, discrete=True)
fig_risk, _ = plot_risk_estimation(risk_estim_disc, matched, threshs_multi, AOI, discrete=True)

# other risk plots (non-averaged, non-discrete)
# plot_risk_estimation(risk_estim, matched, AOI, discrete=False)
# risk_estim_avg = risk_estimation(matched, threshs_multi, discrete=False)

# plot_risk_estimation(risk_estim_avg, matched, AOI, discrete=False)
# risk_estim = risk_estimation(matched, threshs_multi, discrete=False, average=False)

# save results
if save_to_file:
    print("saving results...")
    save_tiff(risk_estim_disc, f"predictions/{match_parent_str}/risk_estimation.tiff")
    #fig_data_sources.canvas.manager.full_screen_toggle()
    #fig_risk_per_layer.canvas.manager.full_screen_toggle()
    #fig_risk.canvas.manager.full_screen_toggle()
    fig_data_sources.savefig(f"predictions/{match_parent_str}/input_data.png")
    fig_risk_per_layer.savefig(f"predictions/{match_parent_str}/risk_per_layer.png")
    fig_risk.savefig(f"predictions/{match_parent_str}/risk.png")


# repeat without pop
matched_no_pop = matched[1:]
threshs_multi_no_pop = threshs_multi[1:]


# plot risk estimation
risk_estim_disc_no_pop = risk_estimation(matched_no_pop, threshs_multi_no_pop, discrete=True)
fig_risk_no_pop, _ = plot_risk_estimation(risk_estim_disc, matched_no_pop, threshs_multi_no_pop, AOI, discrete=True, title="Risk Estimation (no POP)")

# save results
if save_to_file:
    print("saving results_no_pop...")
    save_tiff(risk_estim_disc_no_pop, f"predictions/{match_parent_str}/risk_estimation_no_pop.tiff")
    #fig_risk_no_pop.canvas.manager.full_screen_toggle()
    fig_risk_no_pop.savefig(f"predictions/{match_parent_str}/risk.png")

if show_plots: plt.show()