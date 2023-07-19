"""
Default values for the thresholds/intervals.
Utilities for determining thresholds.
"""

import numpy as np


INF = 1e10

SINGLE_INTERVAL_LST = [20, 35]
SINGLE_INTERVAL_SMAP = [.3, .9]
SINGLE_INTERVAL_NDVI = [.3, 1]
SINGLE_INTERVAL_POP = [.1, 1]


MULTI_INTERVAL_LST = [
    [[25, 27]],
    [[22, 25], [27, 29]],
    [[20, 22], [29, 30]],
    [[18, 20]],
    [[-INF, 18], [30, INF]]
]


MULTI_INTERVAL_NDVI = [
    [],
    [[0.6, 1]],
    [[0.3, 0.6]],
    [[0.1, 0.3]],
    [[-INF, 0.1]]
]

MULTI_INTERVAL_POP = [
    [[-INF, INF]],
    [],
    [],
    [],
    []
]

MULTI_INTERVAL_SMAP = [
    [],
    [[0.3, 0.4]],
    [[0.1, 0.3]],
    [],
    [[-INF, 0.2], [0.4, INF]]
]


# collect
threshs_multi = [MULTI_INTERVAL_POP, MULTI_INTERVAL_LST,
                 MULTI_INTERVAL_NDVI, MULTI_INTERVAL_SMAP]


def estimate_quantile_thresholds(quantiles, data, neg_inf=-INF, pos_inf=INF, ignore=[], show_hist=False):
    """
    Determines N = len(quantiles)-1 thresholds from data. Then creates N+1 intervals.
    :param quantiles:   (list[float])
    :param data:        (xarray.DataArray)
    :param ignore:      (list)                values to ignore for the quantile estimation
    :return:
    """
    # get quantiles from data
    data_flat = data.to_numpy().flatten()
    data_valid = data_flat[(~np.isnan(data_flat))]
    for ignore_val in ignore:
        data_valid = data_valid[data_valid != ignore_val]   # TODO: no loop optimize

    quant_vals = np.quantile(data_valid, quantiles)

    if show_hist:
        import matplotlib.pyplot as plt
        plt.figure()
        max_val = np.quantile(data_valid, 0.98)
        n, b, p = plt.hist(data_valid, bins=int(1e3), range=(0, max_val))
        plt.vlines(quant_vals, 0, 0.8*max(n), linestyles="--", color="r")
        plt.title("Data Histogram")


    # convert to above format of thresholds for compatibility
    threshs = [[[neg_inf, quant_vals[0]]]]
    threshs.extend([[[lower, upper]] for lower, upper in zip(quant_vals[:-1], quant_vals[1:])])
    threshs.append([[quant_vals[-1], pos_inf]])

    return threshs[::-1]