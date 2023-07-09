"""
Defines default values for the thresholds/intervals.
"""

INF = 1e10

SINGLE_INTERVAL_LST = [20, 35]
SINGLE_INTERVAL_SMAP = [.3, .9]
SINGLE_INTERVAL_NDVI = [.3, 1]
SINGLE_INTERVAL_POP = [.1, 1]


MULTI_INTERVAL_LST = [
    [[25, 27]],
    [[24, 25], [27, 29]],
    [[23, 24], [29, 30]],
    [[21, 23]],
    [[-INF, 21], [30, INF]]
]

MULTI_INTERVAL_SMAP = [
    [],
    [[0.3, 0.4]],
    [],
    [[0.2, 0.3]],
    [[-INF, 0.2], [0.4, INF]]
]

MULTI_INTERVAL_NDVI = [
    [[0.6, 1]],
    [[0.4, 0.6]],
    [[0.2, 0.4]],
    [[0.1, 0.2]],
    [[-INF, 0]]
]

MULTI_INTERVAL_POP = [
    [[-INF, INF]],
    [],
    [],
    [],
    []
]
