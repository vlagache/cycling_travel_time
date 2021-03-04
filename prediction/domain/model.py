import datetime
import logging
import os
import pickle
import random
import time
import uuid
from datetime import timedelta, date
from typing import Tuple, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

from prediction.domain import activity


class Model:

    def __init__(self):
        self.id = uuid.uuid4()
        self.activities, self.segments = self.load_data()
        self.features = ['elapsed_time', 'distance', 'climb_category']
        self.cleaning_result = {}
        self.features_added = []
        self.ratio_train_total = None
        self.features_train = []
        self.processing = []
        self.name = None
        self.mae = None
        self.mape = None
        self.rmse = None
        self.training_time = None
        self.training_date = date.today().strftime('%d/%m/%Y')

    @staticmethod
    def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
        activities = activity.repository.get_all_desc()
        segments = [segment.__dict__ for activity_ in activities for segment in activity_.segment_efforts]
        activities = [activity_.__dict__ for activity_ in activities]
        activities_df = pd.DataFrame(activities)
        activities_df = activities_df.drop(columns='segment_efforts')
        segments_df = pd.DataFrame(segments)
        return activities_df, segments_df

    @staticmethod
    def format_date(dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe['start_date_local'] = pd.to_datetime(dataframe['start_date_local'])
        dataframe['start_time'] = dataframe['start_date_local'].dt.time
        dataframe['start_date'] = dataframe['start_date_local'].dt.date
        dataframe = dataframe.drop(columns=['start_date_local'])
        return dataframe

    def clean_data(self):
        initial_shape = self.segments.shape
        # maximum_grade
        huge_max_index = self.segments.loc[self.segments['maximum_grade'] > 50].index
        self.segments = self.segments.drop(huge_max_index)

        # double segment in same activity
        double_index = self.segments[self.segments.duplicated()].index
        self.segments = self.segments.drop(double_index)

        # self.segments too long
        too_long_index = self.segments.loc[self.segments['distance'] > 25000].index
        self.segments = self.segments.drop(too_long_index)

        # low heart_rate
        wrong_heart_rate_index = self.segments.loc[self.segments['average_heart_rate'] < 100].index
        self.segments = self.segments.drop(wrong_heart_rate_index)

        self.segments = self.segments.reset_index(drop=True)
        end_shape = self.segments.shape

        self.cleaning_result = {
            'initial_shape': initial_shape,
            'end_shape': end_shape
        }

    def activities_last_30d(self, date: datetime.date) -> pd.DataFrame:
        end_date = date - timedelta(days=1)
        start_date = end_date - timedelta(days=30)
        return self.activities[self.activities['start_date'].between(start_date, end_date)]

    def segments_last_30d(self, date: datetime.date) -> pd.DataFrame:
        end_date = date - timedelta(days=1)
        start_date = end_date - timedelta(days=30)
        return self.segments[self.segments['start_date'].between(start_date, end_date)]

    def time_activities_last_30d(self) -> None:
        time_activities_last_30d = []
        for date in self.segments['start_date']:
            result = self.activities_last_30d(date)
            time_activities = round((result['elapsed_time'].sum() / 60), 2)
            time_activities_last_30d.append(time_activities)
        self.segments['time_activities_last_30d'] = time_activities_last_30d
        self.features_added.append('time_activities_last_30d')

    def type_virtual_ride(self) -> None:
        self.segments = pd.get_dummies(self.segments, columns=['type'], drop_first=True)
        self.segments = self.segments.rename(columns={'type_VirtualRide': 'type_virtual_ride'})
        self.features_added.append('type_virtual_ride')

    def days_since_last_activity(self) -> None:
        days_since_last_activity = []
        for activity_id in self.segments['activity_id']:
            try:
                index_activity = self.activities.loc[self.activities['id'] == activity_id].index
                result = self.activities.loc[index_activity]['start_date'].values[0] - \
                         self.activities.loc[index_activity + 1]['start_date'].values[0]
                result = result.days
            except KeyError:
                result = 0

            days_since_last_activity.append(result)
        self.segments['days_since_last_activity'] = days_since_last_activity
        self.features_added.append('days_since_last_activity')

    def average_climb_cat_last_30d(self) -> None:
        average_climb_cat_last_30d = []
        for date in self.segments['start_date']:
            result = self.segments_last_30d(date)
            avg_climb_cat = result['climb_category'].mean()
            if np.isnan(avg_climb_cat):
                avg_climb_cat = 0
            average_climb_cat_last_30d.append(round(avg_climb_cat, 2))
        self.segments['average_climb_cat_last_30d'] = average_climb_cat_last_30d
        self.features_added.append('average_climb_cat_last_30d')

    # TODO : Par Climb Category ?
    def average_speed_last_30d(self) -> None:
        average_speed_last_30d = []
        for date in self.segments['start_date']:
            result = self.activities_last_30d(date)
            avg_speed = result['average_speed'].mean()
            if np.isnan(avg_speed):
                avg_speed = 0
            average_speed_last_30d.append(round(avg_speed, 2))
        self.segments['average_speed_last_30d'] = average_speed_last_30d
        self.features_added.append('average_speed_last_30d')

    def split_train_test(self, ratio: float) -> Tuple[Any, ...]:
        calendar_days = []
        for date in self.segments['start_date']:
            calendar_day = date.strftime('%j%Y')
            calendar_days.append(calendar_day)
        self.segments['calendar_day'] = calendar_days

        dates_unique = self.segments['calendar_day'].unique()
        dates_unique = dates_unique.tolist()
        ratio_train_test = len(dates_unique) * ratio

        random.seed(42)
        dates_test_set = random.sample(dates_unique, int(ratio_train_test))
        test_set = self.segments[self.segments['calendar_day'].isin(dates_test_set)]
        train_set = self.segments.drop(test_set.index)

        train_set = train_set[self.features_train]
        test_set = test_set[self.features_train]

        y_train = train_set["elapsed_time"]
        x_train = train_set.drop("elapsed_time", axis=1)
        y_test = test_set["elapsed_time"]
        x_test = test_set.drop("elapsed_time", axis=1)

        self.ratio_train_total = round((train_set.shape[0] / self.segments.shape[0]), 2)

        return x_train, y_train, x_test, y_test

    def log_label(self, label: pd.Series) -> pd.Series:
        label = np.log(label)
        self.processing.append("log_label")
        return label

    def fit_predict(self, model, x_train, y_train, x_test):
        self.name = type(model).__name__
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)
        return y_pred

    def metrics(self, y_test, y_pred):
        if "log_label" in self.processing:
            y_pred = np.exp(y_pred)

        self.mae = mean_absolute_error(y_test, y_pred)
        self.mape = mean_absolute_percentage_error(y_test, y_pred)
        self.rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    def pickle_dump(self, model):
        filename = f'./models/{self.id}'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        pickle.dump(model, open(filename, 'wb'))

    def logging_meta_data(self):
        logging.info(f'Initial Features -  {self.features}')
        logging.info(f"Data Cleaning - initial shape :  {self.cleaning_result['initial_shape']}"
                     f" end shape: {self.cleaning_result['end_shape']}")
        logging.info(f'Features added -  {self.features_added}')
        logging.info(f'Ratio train_set/total -  {self.ratio_train_total}')
        logging.info(f'Features Train -  {self.features_train}')
        logging.info(f'Processing -  {self.processing}')
        logging.info(f'Model -  {self.name}')
        logging.info(f'Metrics - MAE :  {self.mae} , MAPE : {self.mape} , RMSE : {self.rmse} ')
        logging.info(f'Training Time : {self.training_time}')

    def train(self):
        start_train = time.perf_counter()

        # format date
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

        # algo
        model = RandomForestRegressor()
        y_pred = self.fit_predict(model,
                                  x_train,
                                  y_train,
                                  x_test)

        # metrics
        self.metrics(y_test, y_pred)

        end_train = time.perf_counter()
        self.training_time = datetime.timedelta(seconds=int(end_train - start_train))
        self.logging_meta_data()

        # save
        self.pickle_dump(model)


class ModelRepository:

    def get(self, id_) -> Model:
        raise NotImplementedError()

    def save(self, model: Model):
        raise NotImplementedError()


repository: ModelRepository
