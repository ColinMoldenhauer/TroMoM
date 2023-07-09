import os
import glob
from functools import partial

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from mpl_toolkits.basemap import Basemap

from .spatial import crop2aoi
from .transforms import corners2xy
from .utils import format_coord


def plot_AOI(AOI, buffer_size=1e6, **kwargs):
    crs_before = AOI.crs
    crs_utm = AOI.estimate_utm_crs()
    buffer = AOI.to_crs(crs_utm).buffer(buffer_size).to_crs(crs_before)
    envelope = buffer.envelope
    bounds = envelope.bounds

    # Plot
    world = gpd.read_file('misc/naturalearth_lowres/naturalearth_lowres.shp')
    # TODO: maybe clip like below?
    # world = gpd.read_file('misc/naturalearth_lowres/naturalearth_lowres.shp').clip(AOI)
    f, ax = plt.subplots(1, **kwargs)
    plt.suptitle(f"AOI ({AOI.crs})", weight="bold")
    world.plot(ax=ax, facecolor='white', edgecolor='gray')
    AOI.plot(ax=ax, cmap='spring', alpha=.5)
    ax.set_ylim([bounds.miny[0], bounds.maxy[0]])
    ax.set_xlim([bounds.minx[0], bounds.maxx[0]])
    ax.set_xlabel("longitude [deg]")
    ax.set_ylabel("latitude [deg]")

    return f, ax


def plot_AOI_basemap(m, points):
    if len(points[0]) == 2:
        x, y = corners2xy(points)
    else:
        x, y = points
    m.plot(x, y, latlon=True, color="red", markersize=100)


def plot_data(data, lon, lat, colorbar=False):
    fig = plt.figure(figsize=(10, 6))

    m = Basemap(resolution='l', projection='robin', lat_ts=40, lat_0=lat.mean(), lon_0=lon.mean())
    xi, yi = m(lon, lat)
    m.drawcoastlines()
    cs = m.pcolor(xi, yi, data, vmin = 0., vmax = 0.55, cmap = 'terrain_r')

    if colorbar:
        cbar = m.colorbar(cs, location='bottom', pad="5%")
        cbar.set_label('$cm^3 cm^{-3}$')
    # return fig
    return m


def plot_data_dual(data, lon, lat, colorbar=False):
    # TODO: use AOI for zoom
    fig, (ax_world, ax_aoi) = plt.subplots(1, 2, figsize=(12, 6))
    print("means:", lon.mean(), lat.mean())
    m_world = Basemap(resolution='l', projection='robin', lat_ts=40, lat_0=lat.mean(), lon_0=-lon.mean(),
                ax=ax_world)
    # ax_world.xaxis.set_inverted(False)

    m_aoi = Basemap(resolution='l', projection='merc', lon_0=112, lat_0=0,
                    ax=ax_aoi, llcrnrlon=107, llcrnrlat=-5, urcrnrlon=120, urcrnrlat=7)
    ax_aoi.xaxis.set_inverted(True)

    m_world.drawcoastlines()
    m_aoi.drawcoastlines()

    xi_world, yi_world = m_world(lon, lat)
    xi_aoi, yi_aoi = m_aoi(lon, lat)
    cs_world = m_world.pcolor(xi_world, yi_world, data, vmin = 0., vmax = 0.55, cmap = 'terrain_r')
    cs_aoi = m_aoi.pcolor(xi_aoi, yi_aoi, data, vmin = 0., vmax = 0.55, cmap = 'terrain_r')

    if colorbar:
        cbar_world = m_world.colorbar(cs_world, location='bottom', pad="5%")
        cbar_world.set_label('$cm^3 cm^{-3}$')
        cbar_aoi = m_aoi.colorbar(cs_aoi, location='bottom', pad="5%")
        cbar_aoi.set_label('$cm^3 cm^{-3}$')

    return m_world, m_aoi


def plot_data_sources(*data, AOI, title, clip_to_AOI=True, plot_numpy=False, **kwargs):
    # TODO: include meaningful title (AOI?, time?)
    # TODO: fix plot_numpy AOI reprojection
    n_data = len(data)
    if n_data == 1:
        fig = plt.figure()
        axs = [plt.gca()]
    elif n_data < 4:
        fig, axs = plt.subplots(1, n_data, **kwargs)
        axs = axs.flatten()
    else:
        fig, axs = plt.subplots(2, 2, **kwargs)
        axs = axs.flatten()
    fig.suptitle(title, weight="bold")
    plt.subplots_adjust(wspace=0.3, hspace=0.4)

    world = gpd.read_file('misc/naturalearth_lowres/naturalearth_lowres.shp')
    if clip_to_AOI: world = world.clip(AOI)

    # TODO: do cities too
    for ax, d_ in zip(axs, data):
        if clip_to_AOI: d_ = crop2aoi(d_, AOI)
        if d_.name == "NDVI":
            cmap = "Greens"
        else:
            cmap = None

        ax.axis('equal')
        if len(data) == 1:
            if plot_numpy:
                plt.imshow(d_.to_numpy(), cmap=cmap)
            else:
                d_.plot(cmap=cmap, robust=True)
        else:
            if plot_numpy:
                ax.imshow(d_.to_numpy(), cmap=cmap)
            else:
                d_.plot(ax=ax, cmap=cmap, robust=True)
        world.plot(ax=ax, facecolor='none', edgecolor='cyan')
        ax.set_title(d_.name or "No xds.name")

        # def _format_coord(x, y):
        #     val = d_[0, round(x), round(y)]
        #     print("x", x, "y", y)
        #     print("val:", val.values)
        #     return f"({x}, {y}){val}"
        # ax.format_coord = _format_coord

        ax.format_coord = partial(format_coord, data_plot=d_)

    return fig


def visualize_available_data(data_dir, pattern, reader, plot_world=True, crop=None, maxn=None):
    matches = glob.glob(os.path.join(data_dir, pattern))
    if maxn: matches = matches[:maxn]

    nrow = int(len(matches)**.5)
    ncol = len(matches)//nrow
    if nrow*ncol < len(matches): ncol += 1

    fig, axs = plt.subplots(nrow, ncol)
    for i, (ax_, match_) in enumerate(zip(axs.flatten(), matches)):
        if i == maxn: break
        data = reader(match_)
        if crop:
            if isinstance(crop, str):
                AOI = gpd.read_file(crop)
            else:
                AOI = crop
            data = crop2aoi(data, AOI)
        data.plot(ax=ax_)
        if plot_world:
            world = gpd.read_file('misc/naturalearth_lowres/naturalearth_lowres.shp')
            if crop: world = world.clip(AOI)    # TODO: do isinstance as above
            world.plot(ax=ax_, facecolor='none', edgecolor='cyan')

        ax_.set_title(str(i))


def plot_binary_prediction(classif, data, AOI, plot_world=True):
    # TODO: different colorbar if per layer
    fig, ax = plt.subplots(1, 1)
    cmap_bin = matplotlib.colors.ListedColormap(['red', 'green'])
    pcolor = classif.plot(ax=ax, cmap=cmap_bin)
    ax.set_title("Binary risk estimation")
    cbar_ax = fig.axes[-1]
    cbar = plt.colorbar(pcolor, cax=cbar_ax, aspect=10, fraction=.09,
                        boundaries=[-1, 0, 1], values=[.5, -.5], ticks=[-.5, .5],
                        cmap=cmap_bin)
    cbar_ax.set_yticklabels(["no-risk", "risk"])

    if plot_world:
        world = gpd.read_file('misc/naturalearth_lowres/naturalearth_lowres.shp').clip(AOI)
        world.plot(ax=ax, facecolor='none', edgecolor='cyan')

    ax.format_coord = partial(format_coord, data_plot=classif, data_aux=data, sep="  |  ")

    return cbar_ax
