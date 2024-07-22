import pickle
from datetime import timedelta, date, datetime
from statistics import mean, StatisticsError
from typing import Dict, List, Tuple

import numpy as np

from prediction.domain import activity
from prediction.domain.model import Model
from prediction.domain.route import Route
from prediction.utils.functions import convert_seconds_in_hms


class Predict:
    directory_models = './models/'

    def __init__(self, model: Model, route: Route, virtual_ride):
        self.model = model
        self.route = route
        self.virtual_ride = virtual_ride
        self.activities, self.segments = self.load_data()
        self.loaded_model = self.load_model()

    def load_model(self):
        filename = self.directory_models + str(self.model.id)
        loaded_model = pickle.load(open(filename, 'rb'))
        return loaded_model

    @staticmethod
    def load_data() -> Tuple[List[Dict], List[Dict]]:
        activities = activity.repository.get_all_desc()
        segments = [segment.__dict__ for activity_ in activities for segment in activity_.segment_efforts]
        activities = [activity_.__dict__ for activity_ in activities]
        for activity_ in activities:
            del activity_['segment_efforts']
        return activities, segments

    @staticmethod
    def format_date(item_list: List):
        for item in item_list:
            date_time_obj = datetime.strptime(item.get("start_date_local"), '%Y-%m-%dT%H:%M:%SZ')
            item['start_date'] = date_time_obj.date()
            item['start_time'] = date_time_obj.time()
            del item['start_date_local']
        item_list = sorted(item_list, key=lambda x: x['start_date'], reverse=True)
        return item_list

    def activities_last_30d(self, date_: date) -> List[Dict]:
        end_date = date_ - timedelta(days=1)
        start_date = end_date - timedelta(days=30)
        return [
            activity_ for activity_ in self.activities if start_date <= activity_.get("start_date") <= end_date
        ]

    def segments_last_30d(self, date_: date) -> List[Dict]:
        end_date = date_ - timedelta(days=1)
        start_date = end_date - timedelta(days=30)
        return [
            segment_ for segment_ in self.segments if start_date <= segment_.get("start_date") <= end_date
        ]

    def compute_time_activities_last_30d(self, data_to_predict: List[Dict]):
        activities_last_30d = self.activities_last_30d(date.today())
        time_activities_last_30d = sum(activity_['elapsed_time'] for activity_ in activities_last_30d)
        time_activities_last_30d = round((time_activities_last_30d / 60), 2)

        for segment in data_to_predict:
            segment['time_activities_last_30d'] = time_activities_last_30d

        return data_to_predict

    def compute_days_since_last_activity(self, data_to_predict: List[Dict]):
        last_activity = self.activities[0]
        time_since_last_activity = date.today() - last_activity.get("start_date")
        for segment in data_to_predict:
            segment['days_since_last_activity'] = time_since_last_activity.days
        return data_to_predict

    def compute_average_climb_cat_last_30d(self, data_to_predict: List[Dict]):
        segments_last_30d = self.segments_last_30d(date.today())
        try:
            avg_climb_cat_last_30d = mean(segment_['climb_category'] for segment_ in segments_last_30d)
            avg_climb_cat_last_30d = round(avg_climb_cat_last_30d, 2)
        except StatisticsError:
            avg_climb_cat_last_30d = 0

        for segment in data_to_predict:
            segment['average_climb_cat_last_30d'] = avg_climb_cat_last_30d

        return data_to_predict

    def compute_average_speed_last_30d(self, data_to_predict: List[Dict]):
        activities_last_30d = self.activities_last_30d(date.today())
        try:
            avg_speed_last_30d = mean(segment_['average_speed'] for segment_ in activities_last_30d)
            avg_speed_last_30d = round(avg_speed_last_30d, 2)
        except StatisticsError:
            avg_speed_last_30d = 0

        for segment in data_to_predict:
            segment['average_speed_last_30d'] = avg_speed_last_30d

        return data_to_predict

    def compute_virtual_ride(self, data_to_predict: List[Dict]):
        for segment in data_to_predict:
            if self.virtual_ride:
                segment['type_virtual_ride'] = 1
            else:
                segment['type_virtual_ride'] = 0
        return data_to_predict

    @staticmethod
    def compute_climb_category(data_to_predict: List[Dict]) -> List[Dict]:
        """
        Climb category is a feature of Strava
        https://support.strava.com/hc/en-us/articles/216917057-Climb-Categorization
        """
        climb_cat = None
        for segment in data_to_predict:
            result = segment.get("average_grade") * segment.get("distance")
            if result <= 8000:
                climb_cat = 0
            elif 8000 < result <= 16000:
                climb_cat = 1
            elif 16000 < result <= 32000:
                climb_cat = 2
            elif 32000 < result <= 64000:
                climb_cat = 3
            elif 64000 < result <= 80000:
                climb_cat = 4
            elif result > 80000:
                climb_cat = 5
            segment['climb_category'] = climb_cat
        return data_to_predict

    def ordered_data(self, data_to_predict: List[Dict]) -> List[Dict]:
        """
        orders the keys of each dict in the same order as during training
        """
        ordered_data = []
        for segment in data_to_predict:
            ordered_segment = {}
            for key in self.model.features_train:
                ordered_segment[key] = segment.get(key)
            ordered_data.append(ordered_segment)
        return ordered_data

    @staticmethod
    def data_formatting(data_to_predict: List[Dict]) -> np.array:
        formatted_data = [
            [value for value in segment_.values()] for segment_ in data_to_predict
        ]
        return np.array(formatted_data)

    def prepare_data(self):

        # format date_str to date
        self.activities = self.format_date(self.activities)
        self.segments = self.format_date(self.segments)

        # Remove all_points for dict_segment
        data_to_predict = [
            {key: value for key, value in segment.items() if key != "all_points"}
            for segment in self.route.segmentation
        ]

        # en fonction des features train

        if "climb_category" in self.model.features_train:
            data_to_predict = self.compute_climb_category(data_to_predict)
        if "type_virtual_ride" in self.model.features_train:
            data_to_predict = self.compute_virtual_ride(data_to_predict)
        if "time_activities_last_30d" in self.model.features_train:
            data_to_predict = self.compute_time_activities_last_30d(data_to_predict)
        if "days_since_last_activity" in self.model.features_train:
            data_to_predict = self.compute_days_since_last_activity(data_to_predict)
        if "average_climb_cat_last_30d" in self.model.features_train:
            data_to_predict = self.compute_average_climb_cat_last_30d(data_to_predict)
        if "average_speed_last_30d" in self.model.features_train:
            data_to_predict = self.compute_average_speed_last_30d(data_to_predict)

        data_to_predict = self.ordered_data(data_to_predict)
        data_to_predict = self.data_formatting(data_to_predict)

        return data_to_predict

    def get_prediction(self):

        data = self.prepare_data()
        prediction_segments = self.loaded_model.predict(data)

        if "log_label" in self.model.processing:
            prediction = sum(np.exp(prediction_segments))
        else:
            prediction = sum(prediction_segments)

        avg_speed_kmh = (self.route.distance / prediction) * 3.6
        avg_speed_kmh = round(avg_speed_kmh, 2)
        hours, minutes, seconds = convert_seconds_in_hms(prediction)

        return {
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "avg_speed_kmh": avg_speed_kmh
        }
