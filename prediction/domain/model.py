import logging
import os
import glob
import pickle
import random
import time
import uuid
from datetime import timedelta, date, datetime
from enum import Enum
from statistics import mean, StatisticsError
from typing import List, Dict, Optional

import numpy as np
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

from prediction.domain import activity
from prediction.utils.functions import transforms_date_in_str, transforms_time_in_str


class TypeModel(Enum):
    XGB = xgb.XGBRegressor()
    RFORREST = RandomForestRegressor()


class Model:
    directory_models = './models/'

    def __init__(self, model: TypeModel):
        self.model = model
        self.id = uuid.uuid4()
        self.activities, self.segments = self.load_data()
        self.label = 'elapsed_time'
        self.features = ['distance', 'climb_category']
        self.cleaning_result = {}
        self.features_added = []
        self.ratio_train_total = None
        self.features_train = []
        self.processing = []
        self.mae = None
        self.mape = None
        self.rmse = None
        self.training_time = None
        self.training_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    @classmethod
    def delete_all(cls) -> None:
        """
        Deletion of all registered pickle models
        """
        files = glob.glob(f'{cls.directory_models}*')
        for file in files:
            os.remove(file)

    @staticmethod
    def load_data():
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

    @staticmethod
    def format_date_to_str(item_list: List):
        """
        Use to reformat dates into a string at the end of the training for storage in Elastic
        """
        for item in item_list:
            item['start_date'] = transforms_date_in_str(item.get("start_date"))
            item['start_time'] = transforms_time_in_str(item.get("start_time"))
        return item_list

    def clean_data(self):
        initial_shape = (len(self.segments), len(self.segments[0]))

        # maximum_grade
        self.segments = [
            segment_ for segment_ in self.segments if segment_.get('maximum_grade') < 50
        ]

        # double segment in same activity
        unique_segments = []
        for segment_ in self.segments:
            if segment_ not in unique_segments:
                unique_segments.append(segment_)

        self.segments = unique_segments

        # self.segments too long
        self.segments = [
            segment_ for segment_ in self.segments if segment_.get('distance') < 25000
        ]

        # low heart_rate
        # We keep the None, which are activities performed without a cardiac sensor.

        self.segments = [
            segment_ for segment_ in self.segments
            if segment_.get('average_heart_rate') is None or segment_.get('average_heart_rate') > 100
        ]

        end_shape = (len(self.segments), len(self.segments[0]))

        self.cleaning_result = {
            'initial_shape': initial_shape,
            'end_shape': end_shape
        }

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

    def time_activities_last_30d(self) -> None:

        for segment_ in self.segments:
            activities_last_30d = self.activities_last_30d(segment_.get("start_date"))
            time_activities = sum(activity_['elapsed_time'] for activity_ in activities_last_30d)
            time_activities = round((time_activities / 60), 2)
            segment_['time_activities_last_30d'] = time_activities

        self.features_added.append('time_activities_last_30d')

    def type_virtual_ride(self) -> None:
        for segment_ in self.segments:
            if segment_.get("type") == "VirtualRide":
                segment_['type_virtual_ride'] = 1
            else:
                segment_['type_virtual_ride'] = 0
            del segment_['type']
        self.features_added.append('type_virtual_ride')

    def days_since_last_activity(self) -> None:
        result = None
        for segment_ in self.segments:
            for activity_ in self.activities:
                if activity_.get("id") == segment_.get('activity_id'):
                    index_activity = self.activities.index(activity_)
                    try:
                        result = self.activities[index_activity]['start_date'] \
                                 - self.activities[index_activity + 1]['start_date']
                        result = result.days
                    except IndexError:
                        result = 0
            segment_['days_since_last_activity'] = result
        self.features_added.append('days_since_last_activity')

    def average_climb_cat_last_30d(self) -> None:
        for segment_ in self.segments:
            segments_last_30d = self.segments_last_30d(segment_.get("start_date"))
            try:
                avg_climb_cat = mean(seg_['climb_category'] for seg_ in segments_last_30d)
                avg_climb_cat = round(avg_climb_cat, 2)
            # If there are no segments in the last 30 days
            except StatisticsError:
                avg_climb_cat = 0
            segment_['average_climb_cat_last_30d'] = avg_climb_cat
        self.features_added.append('average_climb_cat_last_30d')

    # TODO : Par Climb Category ?
    def average_speed_last_30d(self) -> None:
        for segment_ in self.segments:
            activities_last_30d = self.activities_last_30d(segment_.get("start_date"))
            try:
                avg_speed_last_30d = mean(activity_['average_speed'] for activity_ in activities_last_30d)
                avg_speed_last_30d = round(avg_speed_last_30d, 2)
            except StatisticsError:
                avg_speed_last_30d = 0
            segment_['average_speed_last_30d'] = avg_speed_last_30d
        self.features_added.append('average_speed_last_30d')

    def split_train_test(self, ratio: float):

        for segment_ in self.segments:
            segment_['calendar_day'] = segment_.get("start_date").strftime('%j%Y')

        #

        dates_unique = []
        for segment_ in self.segments:
            if segment_.get('calendar_day') not in dates_unique:
                dates_unique.append(segment_.get('calendar_day'))

        ratio_train_test = len(dates_unique) * ratio

        random.seed(42)
        dates_test_set = random.sample(dates_unique, int(ratio_train_test))

        test_set = [
            segment_ for segment_ in self.segments if segment_.get('calendar_day') in dates_test_set
        ]

        train_set = [
            segment_ for segment_ in self.segments if segment_.get('calendar_day') not in dates_test_set
        ]

        x_train = [
            [value for key, value in segment_.items() if key in self.features_train] for segment_ in train_set
        ]

        y_train = [
            segment_.get(self.label) for segment_ in train_set
        ]

        x_test = [
            [value for key, value in segment_.items() if key in self.features_train] for segment_ in test_set
        ]

        y_test = [
            segment_.get(self.label) for segment_ in test_set
        ]

        self.ratio_train_total = round(len(train_set) / len(self.segments), 2)
        return np.array(x_train), np.array(y_train), np.array(x_test), np.array(y_test)

    def log_label(self, y_train: np.array) -> np.array:
        y_train_log = [
            np.log(value) for value in y_train
        ]
        self.processing.append("log_label")
        return y_train_log

    def fit_predict(self, model, x_train, y_train, x_test):
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)
        return y_pred

    def metrics(self, y_test, y_pred) -> None:
        if "log_label" in self.processing:
            y_pred = np.exp(y_pred)

        # convert numpy dtypes to native python types with val.item()
        self.mae = (mean_absolute_error(y_test, y_pred)).item()
        self.mape = (mean_absolute_percentage_error(y_test, y_pred)).item()
        self.rmse = (np.sqrt(mean_squared_error(y_test, y_pred))).item()

    def pickle_dump(self, model) -> None:
        filename = self.directory_models + str(self.id)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        pickle.dump(model, open(filename, 'wb'))

    def logging_meta_data(self) -> None:
        logging.info(f'Initial Features -  {self.features}')
        logging.info(f"Data Cleaning - initial shape :  {self.cleaning_result['initial_shape']}"
                     f" end shape: {self.cleaning_result['end_shape']}")
        logging.info(f'Features added -  {self.features_added}')
        logging.info(f'Ratio train_set/total -  {self.ratio_train_total}')
        logging.info(f'Label -  {self.label}')
        logging.info(f'Features Train -  {self.features_train}')
        logging.info(f'Processing -  {self.processing}')
        logging.info(f'Model -  {self.model}')
        logging.info(f'Metrics - MAE :  {self.mae} , MAPE : {self.mape} , RMSE : {self.rmse} ')
        logging.info(f'Training Time : {self.training_time}')

    def train(self):
        start_train = time.perf_counter()

        # format date_str to date
        self.activities = self.format_date(self.activities)
        self.segments = self.format_date(self.segments)

        # cleaning
        self.clean_data()

        # features engineering
        self.time_activities_last_30d()
        self.days_since_last_activity()
        self.type_virtual_ride()
        self.average_climb_cat_last_30d()
        self.average_speed_last_30d()

        # split train/test
        self.features_train = self.features + self.features_added
        x_train, y_train, x_test, y_test = self.split_train_test(0.2)

        # log label
        y_train = self.log_label(y_train)

        # algo fit predict
        y_pred = self.fit_predict(self.model.value,
                                  x_train,
                                  y_train,
                                  x_test)

        # metrics
        self.metrics(y_test, y_pred)
        end_train = time.perf_counter()
        self.training_time = timedelta(seconds=int(end_train - start_train))

        # save
        self.pickle_dump(self.model.value)

        # TODO Ugly method for not to encode the model in json
        self.model = type(self.model.value).__name__
        self.logging_meta_data()

        # format date to str for elastic
        self.activities = self.format_date_to_str(self.activities)
        self.segments = self.format_date_to_str(self.segments)


class ModelRepository:

    def is_empty(self) -> bool:
        raise NotImplementedError()

    def get(self, id_) -> Model:
        raise NotImplementedError()

    def get_better_mape(self) -> Model:
        raise NotImplementedError()

    def get_general_info(self) -> Optional[dict]:
        """
        Returns the number of activities in base, the name and
        time of the last one
        Or None if the index is empty
        """
        raise NotImplementedError()

    def get_all(self) -> List[Model]:
        raise NotImplementedError()

    def save(self, model: Model):
        raise NotImplementedError()

    def delete_recreates_index(self) -> None:
        """
        deletes the index and its content and recreates it empty
        """
        raise NotImplementedError()


repository: ModelRepository
