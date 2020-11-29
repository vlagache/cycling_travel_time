import numpy as np
import pandas as pd


class Segment:

    def __init__(self, records_df):
        self.records_df = records_df
        self.date = None
        self.duration = None
        self.average_power = None
        self.average_speed = None
        self.average_heart_rate = None
        self.average_cadence = None
        self.gain_altitude = None
        self.distance = None
        self.vertical_drop = None
        self.type_previous_segment = None

    def compute_metrics(self, first_segment=False):
        self.set_date()
        self.set_duration()
        self.set_average_power()
        self.set_average_speed()
        self.set_average_heart_rate()
        self.set_average_cadence()
        self.set_gain_altitude()
        if first_segment:
            self.set_distance(True)
        else:
            self.set_distance(False)
        self.set_vertical_drop()

    def set_date(self):
        """
        datetime.date
        """
        self.date = pd.to_datetime(self.records_df['timestamp'].head(1).values[0]).date()

    def set_duration(self):
        """
        seconds
        """
        self.duration = (self.records_df['timestamp'].tail(1).values[0] -
                         self.records_df['timestamp'].head(1).values[0]) / np.timedelta64(1, 's')

    def set_average_power(self):
        """
        watts
        """
        self.average_power = round(self.records_df['power'].mean(), 2)

    def set_average_speed(self):
        """
        km/h
        """
        self.average_speed = round(self.records_df['speed'].mean() * 3.6, 2)

    def set_average_heart_rate(self):
        """
        bpm
        """
        self.average_heart_rate = round(int(self.records_df['heart_rate'].mean()), 2)

    def set_average_cadence(self):
        """
        rpm
        """
        self.average_cadence = round(int(self.records_df['cadence'].mean()), 2)

    def set_gain_altitude(self):
        """
        m
        """
        self.gain_altitude = round((self.records_df.tail(1)['altitude'].values[0] -
                                    self.records_df.head(1)['altitude'].values[0]), 2)

    def set_distance(self, first_segment=False):
        """
        m

        The logic is different depending on whether it is the first segment of a road or not.

        Ex : first point of segment , distance = 1.85m
        We have already done 1m, which must be taken into account in the distance.
        We take the distance to the last point.

        For other differences between the distance between the last and the first point
        """
        if first_segment:
            self.distance = self.records_df.tail(1)['distance'].values[0]
        else:
            self.distance = round((self.records_df.tail(1)['distance'].values[0] -
                                   self.records_df.head(1)['distance'].values[0]), 2)

    def set_vertical_drop(self):
        """
        %
        """
        self.vertical_drop = round(((self.gain_altitude * 100) / self.distance), 2)
