from typing import List, Optional, Dict

import folium
from folium import plugins


class Route:

    def __init__(self, id_: int, athlete_id: int, description: str, distance: int, elevation_gain: int,
                 name: str, created_at: str, estimated_moving_time: int, gpx: List[Dict]):
        self.id = id_
        self.athlete_id = athlete_id
        self.description = description
        self.distance = distance
        self.elevation_gain = elevation_gain
        self.name = name
        self.created_at = created_at
        self.estimated_moving_time = estimated_moving_time
        self.gpx = gpx

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
