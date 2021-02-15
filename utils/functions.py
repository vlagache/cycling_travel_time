import datetime
import warnings
from math import radians, cos, sin, asin, sqrt
from typing import List, Dict

import gpxpy
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


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


def compute_segmentation(gpx: List[Dict]) -> List[Dict]:
    """
    Segmentation of a gpx route into logical segments (ascent, descent, flat).
    Explanation of this function here :
    notebooks_explanations/Explanation_route_segmentation.ipynb
    """
    # TODO : adapt the window according to the profile of the route
    window = 6

    df = pd.DataFrame(gpx)
    df["elevation"] = round(df["elevation"], 2)

    # compute distance_to_the_last_point
    for i in range(df.shape[0]):
        if i == 0:
            df.loc[i, "distance_to_last_point"] = 0
        else:
            df.loc[i, "distance_to_last_point"] = round(
                haversine(
                    df['longitude'][i], df['latitude'][i],
                    df['longitude'][i - 1], df['latitude'][i - 1]
                ), 2)

    # total_distance
    df['total_distance'] = round(df['distance_to_last_point'].cumsum(), 2)

    # rolling_windows
    df['rw_altitude_gain'] = \
        df['elevation'].rolling(window=window).apply(lambda x: x.iloc[window - 1] - x.iloc[0])

    # segmentation
    df_na = df[df['rw_altitude_gain'].isna()]
    df_na['segment'] = 0
    df = df.dropna().reset_index(drop=True)

    for i in range(df.shape[0]):
        if i == 0:
            df.loc[i, "segment"] = 0
        else:
            if not sign_equal(df.loc[i - 1, 'rw_altitude_gain'], df.loc[i, "rw_altitude_gain"]):
                df.loc[i, "segment"] = df.loc[i - 1, "segment"] + 1
            else:
                df.loc[i, "segment"] = df.loc[i - 1, "segment"]

    df = df_na.append(df, ignore_index=True)
    df_start_end_segments = df.groupby('segment').agg(['first', 'last']).stack()

    # Compute information about segments
    segments = []
    for i in range(len(df_start_end_segments.index.levels[0].unique())):
        if i == 0:
            total_distance = df_start_end_segments.xs('last', level=1)['total_distance'][i]
            altitude_gain = df_start_end_segments.xs('last', level=1)['elevation'][i] - \
                            df_start_end_segments.xs('first', level=1)['elevation'][i]
        else:
            total_distance = df_start_end_segments.xs('last', level=1)['total_distance'][i] - \
                             df_start_end_segments.xs('last', level=1)['total_distance'][i - 1]
            altitude_gain = df_start_end_segments.xs('last', level=1)['elevation'][i] - \
                            df_start_end_segments.xs('last', level=1)['elevation'][i - 1]

        vertical_drop = (altitude_gain * 100) / total_distance

        segment = {
            "distance": float(round(total_distance, 2)),
            "altitude_gain": float(round(altitude_gain, 2)),
            "vertical_drop": float(round(vertical_drop, 2))
        }
        segments.append(segment)

    return segments
