from typing import List, Optional

from prediction.domain.segment import Segment


class Activity:

    def __init__(self, id_: int, athlete_id: int, name: str, distance: int,
                 moving_time: int, elapsed_time: int, total_elevation_gain: int,
                 type_: str, start_date_local: str, average_speed: int, average_cadence: int,
                 average_watts: int, max_watts: int, suffer_score: int, calories: int, segment_efforts: List[Segment],
                 average_heart_rate: int = None, max_heart_rate: int = None):
        self.id = id_
        self.athlete_id = athlete_id
        self.name = name
        self.distance = distance
        self.moving_time = moving_time
        self.elapsed_time = elapsed_time
        self.total_elevation_gain = total_elevation_gain
        self.type = type_
        self.start_date_local = start_date_local
        self.average_speed = average_speed
        self.average_cadence = average_cadence
        self.average_watts = average_watts
        self.max_watts = max_watts
        self.suffer_score = suffer_score
        self.calories = calories
        self.segment_efforts = segment_efforts
        self.average_heart_rate = average_heart_rate
        self.max_heart_rate = max_heart_rate


class ActivityRepository:

    def is_empty(self) -> bool:
        raise NotImplementedError()

    def get(self, id_) -> Activity:
        raise NotImplementedError()

    def get_all_desc(self) -> List[Activity]:
        """
        all activities in desc order
        """
        raise NotImplementedError()

    def get_general_info(self) -> Optional[dict]:
        """
        Returns the number of activities in base, the name and
        time of the last one
        Or None if the index is empty
        """
        raise NotImplementedError()

    def save(self, activity: Activity):
        raise NotImplementedError()

    def search_if_exist(self, _id) -> bool:
        raise NotImplementedError()


repository: ActivityRepository
