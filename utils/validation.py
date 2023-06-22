import matplotlib.pyplot as plt

from utils.spatial import crop2aoi


def validate_resample(data, data_res, align="v", title=""):
    if align == "h":
        fig, (ax_orig, ax_res) = plt.subplots(1, 2)
    else:
        fig, (ax_orig, ax_res) = plt.subplots(2, 1)
    plt.suptitle(title, weight="bold")
    space = .5
    plt.subplots_adjust(wspace=space, hspace=space)
    data.plot(ax=ax_orig)
    data_res.plot(ax=ax_res)
    ax_orig.set_title("original")
    ax_res.set_title("resampled")
    return fig, (ax_orig, ax_res)


def validate_crops(xds, AOI, buffers, title="Validate Crops"):
    fig, axs = plt.subplots(1, len(buffers))
    fig.suptitle(title, weight="bold")
    for buffer, ax in zip(buffers, axs):
        crop = crop2aoi(xds, AOI, buffer)
        crop.plot(ax=ax)
        ax.set_title(f"buffer = {buffer}")
    return fig, axs
