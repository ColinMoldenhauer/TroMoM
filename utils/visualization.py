import geopandas as gpd
import matplotlib.pyplot as plt

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