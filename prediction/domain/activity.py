from typing import List

class Segment:
    def __init__(self, id_: int):
        self.id = id_
        self.name
        self.moving_time
        self.start_date_local
        self.distance
        self.average_cadence
        self.average_watts
        self.average_grade
        self.maximum_grade




class Activity:

    def __init__(self, id_: int):
        self.id = id_
        self.name
        self.athlete_id
        self.distance
        self.moving_time
        self.total_elevation_gain
        self.type
        self.start_date_local
        self.average_cadence
        self.average_watts
        self.max_watts
        self.segments_efforts = List[Segment]




class ActivityRepository:

    def get(self, id_) -> Activity:
        raise NotImplementedError()

    def save(self, activity: Activity):
        raise NotImplementedError()

    def search_if_exist(self, _id) -> bool:
        raise NotImplementedError()


repository: ActivityRepository
