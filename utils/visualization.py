import geopandas as gpd
import matplotlib.pyplot as plt

from mpl_toolkits.basemap import Basemap

from .transforms import corners2xy


def plot_AOI(AOI, buffer_size=1e6, **kwargs):
    default_kwargs = {"figsize": (12, 6)}
    default_kwargs.update(**kwargs)

    crs_before = AOI.crs
    crs_utm = AOI.estimate_utm_crs()
    buffer = AOI.to_crs(crs_utm).buffer(buffer_size).to_crs(crs_before)
    envelope = buffer.envelope
    bounds = envelope.bounds

    # Plot
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    f, ax = plt.subplots(1, **default_kwargs)
    world.plot(ax=ax, facecolor='white', edgecolor='gray')
    AOI.plot(ax=ax, cmap='spring', alpha=.5)
    ax.set_ylim([bounds.miny[0], bounds.maxy[0]])
    ax.set_xlim([bounds.minx[0], bounds.maxx[0]])

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
