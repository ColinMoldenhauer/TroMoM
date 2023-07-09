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



def risk_estimation(data, thresh_list, discrete=True, average=True):
    """

    :param data:
    :param thresh_list:
    :return:
    """
    assert len(data) == len(thresh_list), "Number of thresholds must equal number of data layers."
    assert all([len(t) == 5 for t in thresh_list]), "At this point, we expect 5 risk levels per data layer."
    risk = np.zeros(data[0].to_numpy().shape[:2], dtype=float)        # TODO optional: unify for other types?

    for layer_, threshs_per_data_ in zip(data, thresh_list):    # one large list per data layer (POP, SMAP, etc...)
        layer_ = layer_.to_numpy()
        risk[np.isnan(layer_)] = np.nan                 # no data pixels are propagated
        for risk_level_, threshs_per_level_ in enumerate(threshs_per_data_, 1):     # 5 lists of lists
            for risk_interval_ in threshs_per_level_:
                lower, upper = risk_interval_
                # increase risk level per pixel if value in interval and not NaN
                risk[(layer_ >= lower) & (layer_ <= upper) & ~np.isnan(risk)] += risk_level_

    if average or discrete:
        mask_nan = np.isnan(risk)
        risk = risk/len(data)
        if discrete: risk = np.round(risk)
        risk[mask_nan] = np.nan

    risk = xarray.DataArray(
        name="Risk Estimation",
        data=risk,
        dims=["y", "x"],
        coords=data[0].coords,
        attrs=dict(
            description="Risk Estimation"
        )
    )
    return risk