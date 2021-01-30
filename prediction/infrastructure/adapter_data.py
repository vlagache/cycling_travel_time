from typing import Optional, List

from prediction.domain.activity import Activity
from prediction.domain.athlete import Athlete
from prediction.domain.segment import Segment


class AdapterAthlete:

    def __init__(self, data: dict):
        self.data = data

    def id(self) -> int:
        return self.data.get("athlete").get("id")

    def refresh_token(self) -> str:
        return self.data.get("refresh_token")

    def access_token(self) -> str:
        return self.data.get("access_token")

    def token_expires_at(self) -> int:
        return self.data.get("expires_at")

    def firstname(self) -> str:
        return self.data.get("athlete").get("firstname")

    def lastname(self) -> str:
        return self.data.get("athlete").get("lastname")

    def get(self) -> Athlete:
        return Athlete(
            id_=self.id(),
            refresh_token=self.refresh_token(),
            access_token=self.access_token(),
            token_expires_at=self.token_expires_at(),
            firstname=self.firstname(),
            lastname=self.lastname()
        )


class AdapterSegment:

    def __init__(self, data: dict):
        self.data = data

    def id(self) -> int:
        return self.data.get("segment").get("id")

    def activity_id(self) -> int:
        return self.data.get("activity").get("id")

    def athlete_id(self) -> int:
        return self.data.get("athlete").get("id")

    def name(self) -> str:
        return self.data.get("name")

    def type(self) -> str:
        return self.data.get("segment").get("activity_type")

    def elapsed_time(self) -> int:
        return self.data.get("elapsed_time")

    def moving_time(self) -> int:
        return self.data.get("moving_time")

    def start_date_local(self) -> str:
        return self.data.get("start_date_local")

    def distance(self) -> int:
        return self.data.get("distance")

    def average_cadence(self) -> int:
        return self.data.get("average_cadence")

    def average_watts(self) -> int:
        return self.data.get("average_watts")

    def average_grade(self) -> int:
        return self.data.get("segment").get("average_grade")

    def maximum_grade(self) -> int:
        return self.data.get("segment").get("maximum_grade")

    def climb_category(self) -> int:
        return self.data.get("segment").get("climb_category")

    def average_heart_rate(self) -> Optional[int]:
        """
        May be None if the activity has been carried out
        without heart rate device
        """
        return self.data.get("average_heartrate")

    def max_heart_rate(self) -> Optional[int]:
        """
        May be None if the activity has been carried out
        without heart rate device
        """
        return self.data.get("max_heartrate")

    def get(self) -> Segment:
        return Segment(
            id_=self.id(),
            activity_id=self.activity_id(),
            athlete_id=self.athlete_id(),
            name=self.name(),
            type_=self.type(),
            elapsed_time=self.elapsed_time(),
            moving_time=self.moving_time(),
            start_date_local=self.start_date_local(),
            distance=self.distance(),
            average_cadence=self.average_cadence(),
            average_watts=self.average_watts(),
            average_grade=self.average_grade(),
            maximum_grade=self.maximum_grade(),
            climb_category=self.climb_category(),
            average_heart_rate=self.average_heart_rate(),
            max_heart_rate=self.max_heart_rate()
        )


class AdapterActivity:

    def __init__(self, data: dict):
        self.data = data

    def id(self) -> int:
        return self.data.get("id")

    def athlete_id(self) -> int:
        return self.data.get("athlete").get("id")

    def name(self) -> str:
        return self.data.get("name")

    def distance(self) -> int:
        return self.data.get("distance")

    def moving_time(self) -> int:
        return self.data.get("moving_time")

    def elapsed_time(self) -> int:
        return self.data.get("elapsed_time")

    def total_elevation_gain(self) -> int:
        return self.data.get("total_elevation_gain")

    def type(self) -> str:
        return self.data.get("type")

    def start_date_local(self) -> str:
        return self.data.get("start_date_local")

    def average_speed(self) -> int:
        return self.data.get("average_speed")

    def average_cadence(self) -> int:
        return self.data.get("average_cadence")

    def average_watts(self) -> int:
        return self.data.get("average_watts")

    def max_watts(self) -> int:
        return self.data.get("max_watts")

    def suffer_score(self) -> int:
        return self.data.get("suffer_score")

    def calories(self) -> int:
        return self.data.get("calories")

    # def segment_efforts(self) -> List[Segment]:
    def segment_efforts(self) -> List:
        return self.data.get("segment_efforts")
        # return [AdapterSegment(segment_effort).get() for segment_effort in segments]

    def average_heart_rate(self) -> Optional[int]:
        """
        May be None if the activity has been carried out
        without heart rate device
        """
        return self.data.get("average_heartrate")

    def max_heart_rate(self) -> Optional[int]:
        """
        May be None if the activity has been carried out
        without heart rate device
        """
        return self.data.get("max_heartrate")

    def get(self) -> Activity:
        return Activity(
            id_=self.id(),
            athlete_id=self.athlete_id(),
            name=self.name(),
            distance=self.distance(),
            moving_time=self.moving_time(),
            elapsed_time=self.elapsed_time(),
            total_elevation_gain=self.total_elevation_gain(),
            type_=self.type(),
            start_date_local=self.start_date_local(),
            average_speed=self.average_speed(),
            average_cadence=self.average_cadence(),
            average_watts=self.average_watts(),
            max_watts=self.max_watts(),
            suffer_score=self.suffer_score(),
            calories=self.calories(),
            segment_efforts=self.segment_efforts(),
            average_heart_rate=self.average_heart_rate(),
            max_heart_rate=self.max_heart_rate()
        )
