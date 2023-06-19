import geopandas as gpd
from shapely.geometry.polygon import orient


def aoi2poly(AOI):
    # CMR polygon points need to be provided in counter-clockwise order. The last point should match the first point
    # to close the polygon.

    # Simplify polygon for complex shapes in order to pass a reasonable request length to CMR.
    # The larger the tolerance value, the more simplified the polygon.
    # Orient counter-clockwise: CMR polygon points need to be provided in counter-clockwise order.
    # The last point should match the first point to close the polygon.

    poly = orient(AOI.simplify(0.05, preserve_topology=False).loc[0], sign=1.0)

    # geojson = gpd.GeoSeries(poly).to_json() # Convert to geojson
    # geojson = geojson.replace(' ', '') # remove spaces for API call

    # Format dictionary to polygon coordinate pairs for CMR polygon filtering
    polygon = ','.join([str(c) for xy in zip(*poly.exterior.coords.xy) for c in xy])

    return polygon


def corners2xy(points):
    w, n, e, s = [c for corner in points for c in corner]
    x = [w, e, e, w, w]
    y = [n, n, s, s, n]
    return x, y


def EASE2EPSG(epsg):
    pass


def smap2EPSG(data, lon, lat, epsg):
    pass


def crop2aoi(data, AOI):
    pass