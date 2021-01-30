class Segment:

    def __init__(self, id_: int, activity_id: int, athlete_id: int, name: str,
                 type_: str, elapsed_time: int, moving_time: int, start_date_local: str,
                 distance: int, average_cadence: int, average_watts: int, average_grade: int,
                 maximum_grade: int, climb_category: int, average_heart_rate: int = None, max_heart_rate: int = None):
        self.id = id_
        self.activity_id = activity_id,
        self.athlete_id = athlete_id,
        self.name = name,
        self.type = type_,
        self.elapsed_time = elapsed_time,
        self.moving_time = moving_time,
        self.start_date_local = start_date_local,
        self.distance = distance,
        self.average_cadence = average_cadence,
        self.average_watts = average_watts,
        self.average_grade = average_grade,
        self.maximum_grade = maximum_grade,
        self.climb_category = climb_category,
        self.average_heart_rate = average_heart_rate,
        self.max_heart_rate = max_heart_rate
