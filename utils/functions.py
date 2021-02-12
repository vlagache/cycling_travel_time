import datetime
from math import radians, cos, sin, asin, sqrt
from typing import List, Dict

import gpxpy
import numpy as np


def sign_equal(a, b):
    """
    Compares the two-digit sign and indicates whether they are identical
    Takes the 0 as a separate value
    ex : sign_equal(0,-5) >>> False
    Return True/False
    """
    return np.sign(a) == np.sign(b)


def transforms_string_in_datetime(date: str):
    format_date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    new_format = "%d/%m/%Y à %H:%M:%S"
    format_date = format_date.strftime(new_format)
    return format_date


def gpx_parser(gpx: str) -> List[Dict]:
    parsed_gpx = gpxpy.parse(gpx)
    data = [
        {"latitude": point.latitude, "longitude": point.longitude, "elevation": point.elevation}
        for track in parsed_gpx.tracks
        for segment in track.segments
        for point in segment.points
    ]
    return data


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    m = km * 1000
    return m
