import numpy as np
import xarray
import matplotlib.pyplot as plt


def classify_by_interval(data, thresh_list, per_layer=False):
    # TODO: docstring
    """

    :param data:
    :param thresh_list:
    :param per_layer:
    :return:
    """
    assert len(data) == len(thresh_list), "Number of thresholds must equal number of data layers."
    classif = np.zeros(data[0].to_numpy().shape[:2], dtype=float)        # TODO optional: unify for other types?

    for i, (layer_, thresh_) in enumerate(zip(data, thresh_list)):
        layer_ = layer_.to_numpy()
        lower, upper = thresh_
        classif[np.isnan(layer_)] = np.nan          # no data pixels are propagated
        classif[(layer_ >= lower) & (layer_ <= upper) & ~np.isnan(classif)] += 10**i   # keep track which conditions are met

    # TODO: copy relevant attributes back to DataArray?
    if not per_layer:
        risk_thresh = int("1"*len(thresh_list))
        mask_nan = np.isnan(classif)
        classif = (classif == risk_thresh).astype(float)
        classif[mask_nan] = np.nan

    classif = xarray.DataArray(
        name="Binary Risk Estimation",
        data=classif,
        dims=["y", "x"],
        coords=data[0].coords,
        attrs=dict(
            description="Binary Classification"
        )
    )

    return classif



def risk_estimation(data, thresh_list, per_layer=False):
    """

    :param data:
    :param thresh_list:
    :param per_layer:
    :return:
    """
    # assert data[0].to_numpy().shape[0] == len(thresh_list), "Number of thresholds must equal number of data layers."
    assert len(data) == len(thresh_list), "Number of thresholds must equal number of data layers."
    classif = np.zeros(data[0].to_numpy().shape[:2], dtype=float)        # TODO optional: unify for other types?

    for i, (layer_, thresh_) in enumerate(zip(data, thresh_list)):
        # if isinstance(layer_, xarray.DataArray):
        name = layer_.name
        layer_ = layer_.to_numpy()
        lower, upper = thresh_
        classif[np.isnan(layer_)] = np.nan          # no data pixels are propagated
        classif[(layer_ >= lower) & (layer_ <= upper) & ~np.isnan(classif)] += 10**i   # keep track which conditions are met

    # TODO: copy relevant attributes back to DataArray?
    if not per_layer:
        risk_thresh = int("1"*len(thresh_list))
        mask_nan = np.isnan(classif)
        classif = (classif == risk_thresh).astype(float)
        classif[mask_nan] = np.nan

    classif = xarray.DataArray(
        name="Binary Risk Estimation",
        data=classif,
        dims=["y", "x"],
        coords=data[0].coords,
        attrs=dict(
            description="Binary Classification"
        )
    )

    return classif