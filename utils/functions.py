import datetime
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
