from typing import List, Optional


class Route:

    def __init__(self, id_: int, athlete_id: int, description: str, distance: int, elevation_gain: int,
                 name: str, created_at: str, estimated_moving_time: int, gpx: str):
        self.id = id_
        self.athlete_id = athlete_id
        self.description = description
        self.distance = distance
        self.elevation_gain = elevation_gain
        self.name = name
        self.created_at = created_at
        self.estimated_moving_time = estimated_moving_time
        self.gpx = gpx


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
