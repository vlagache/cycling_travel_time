import warnings
from typing import List, Optional, Dict

import folium
import pandas as pd
from folium import plugins

from utils.functions import haversine, sign_equal

warnings.filterwarnings('ignore')


class Route:

    def __init__(self, id_: int, athlete_id: int, description: str, distance: int, elevation_gain: int,
                 name: str, created_at: str, estimated_moving_time: int, gpx: List[Dict],
                 segments: List[Dict]):
        self.id = id_
        self.athlete_id = athlete_id
        self.description = description
        self.distance = distance
        self.elevation_gain = elevation_gain
        self.name = name
        self.created_at = created_at
        self.estimated_moving_time = estimated_moving_time
        self.gpx = gpx
        self.segments = segments

    def get_map(self) -> str:
        """
        from points of geographical coordinates returns a map of the route as a string html

        """

        middle_value = round(len(self.gpx) / 2)
        middle_point = [
            self.gpx[middle_value].get("latitude"),
            self.gpx[middle_value].get("longitude")
        ]
        points = [
            [point.get("latitude"), point.get("longitude")]
            for point in self.gpx
        ]

        m = folium.Map(
            location=middle_point,
            zoom_start=13
        )
        folium.plugins.AntPath(
            locations=points,
            dash_array=[10, 35],
            color="#FC4C02",
            pulse_color="black",
            weight=5,
            delay=800,
            hardware_acceleration=True,
            opacity=0.9
        ).add_to(m)

        m.fit_bounds(m.get_bounds())
        return m._repr_html_()

    def compute_segmentation(self):
        """
        Segmentation of a route into logical segments (ascent, descent, flat).
        Explanation of this function here :
        notebooks_explanations/Explanation_route_segmentation.ipynb
        """
        # TODO : adapt the window according to the route
        window = 6

        df = pd.DataFrame(self.gpx)
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
                "distance": round(total_distance, 2),
                "altitude_gain": round(altitude_gain, 2),
                "vertical_drop": round(vertical_drop, 2)
            }
            segments.append(segment)

        self.segments = segments


class RouteRepository:

    def is_empty(self) -> bool:
        raise NotImplementedError()

    def get(self, id_) -> Route:
        raise NotImplementedError()

    def get_all_desc(self) -> List[Route]:
        """
        all activities in desc order
        """
        raise NotImplementedError()

    def get_general_info(self) -> Optional[dict]:
        """
        Returns the number of routes in base, the name and
        time of the last one.
        Or None if the index is empty
        """
        raise NotImplementedError()

    def save(self, route: Route):
        raise NotImplementedError()

    def search_if_exist(self, _id) -> bool:
        raise NotImplementedError()


repository: RouteRepository
