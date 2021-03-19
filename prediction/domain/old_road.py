import fitparse
import numpy as np
import pandas as pd

from prediction.domain.old_segment import Segment
from prediction.utils.functions import sign_equal

pd.options.mode.chained_assignment = None  # default='warn'


class Road:
    """
    fit_file = .fit file
    fit_parse = parsed .fit file
    records = list with the data of each .fit point
    segments_schedule = the start and end time of each segment
    segments = object list Segment
    """
    mandatory_information = [
        'altitude',
        'distance',
        'timestamp',
        'speed',
        'power',
        'position_lat',
        'position_long',
        'heart_rate',
        'cadence']

    def __init__(self, fit_file):
        self.fit_file = fit_file
        self.fit_parse = None
        self.records = []
        self.segments_schedule = None
        self.segments = []

    def parsing_from_fit_file(self):
        self.fit_parse = fitparse.FitFile(self.fit_file)

    def get_records_from_fit_file(self):
        """
        recovers all the points of a fit file ( one every second )
        returns a list of dictionaries for each point

        dict = {
            "altitude" (m),
            "cadence" (rpm) ,
            "distance" (m) ,
            "heart_rate" (bpm) ,
            "position_lat" (semicircle),
            "position_long" (semicircle),
            "power" (watts) ,
            "speed" (m/s) ,
            "timestamp" (datetime),
        }

        """

        for record in self.fit_parse.get_messages("record"):
            record_dict = {}
            for data in record:
                if data.value is not None:
                    if data.name in self.mandatory_information:
                        record_dict[data.name] = data.value
            self.records.append(record_dict)

    def get_device_info_from_fit_file(self):
        for record in self.fit_parse.get_messages("device_info"):
            for data in record:
                if data.name == 'manufacturer':
                    print(data)

    def compute_segmentation(self, time_between_each_records=20):

        """
        calculates logical ( ascent, descent, flat )  segments from a route
        time_between_each_records : reduction of the number of points to one point every x seconds
        """

        self.get_records_from_fit_file()

        df = pd.DataFrame(self.records)

        # Reducing the size of the dataframe
        reduced_dataframe = df.iloc[::time_between_each_records, :]
        reduced_dataframe = reduced_dataframe.reset_index(drop=True)

        reduced_dataframe = self.compute_altitude_gain(reduced_dataframe)

        # Before segmentation, we keep the first line with an altitude_gain = np.nan
        # (whose altitude_gain cannot be compared ) and it's deleted from the dataframe
        # Segment for this point = 0

        first_row = reduced_dataframe.head(1)
        first_row['segment'] = 0
        reduced_dataframe = reduced_dataframe.drop(first_row.index)
        reduced_dataframe = reduced_dataframe.reset_index(drop=True)

        segmented_df = self.segmentation(reduced_dataframe)
        # We add the first line after segmentation
        segmented_df = first_row.append(segmented_df, ignore_index=True)

        # compute the start and end time of each segment
        self.compute_start_end_time_of_segments(segmented_df)

    def compute_start_end_time_of_segments(self, dataframe):
        """
        Aggregates segmented information to have
        the start and end point of each segment.

        ex :
                      altitude distance cadence timestamp   ...
        segment first 88.8     1.85     74       18:33:40
        0       last  98.2     367.4    91       18:35:00
        1       first  ...      ...     ...         ...
                last   ...      ...     ...         ...

        returns a dict with the start and end time for each segment.
        { "segment_0" : {"start": 18:33:40 , "end": 18:35:00 .... }, ...

        """
        # segments_time = OrderedDict()
        segments_schedule = {}
        df_start_end_segments = dataframe.groupby('segment').agg(['first', 'last']).stack()
        for i in range(len(df_start_end_segments.xs('first', level=1))):
            segment_time = {'start': df_start_end_segments.xs('first', level=1)['timestamp'][i],
                            'end': df_start_end_segments.xs('last', level=1)['timestamp'][i]}
            segments_schedule[f'segment_{i}'] = segment_time

        self.segments_schedule = segments_schedule

    def get_all_points_of_one_segment(self, start, end):
        """
        Segments all the recordings of a route
        according to a start and end time
        returns a dataframe.
        """
        df = pd.DataFrame(self.records)
        all_points_segment = df[df['timestamp'].between(start, end)]
        return all_points_segment

    def compute_metrics_segments(self, activity_number):
        """
        From the information of the start and end time of each segment and
        of all the points composing it, calculation of the metrics of each segment.


        """
        for i, start_end_segment in enumerate(self.segments_schedule):
            # First segment of road
            # We take the points between the beginning
            # and the end of the segment
            if i == 0:
                all_points_segment_df = self.get_all_points_of_one_segment(
                    start=self.segments_schedule[f'segment_{i}']['start'],
                    end=self.segments_schedule[f'segment_{i}']['end']
                )
                segment = Segment(all_points_segment_df, activity_number)
                segment.compute_metrics(first_segment=True)
                self.segments.append(segment)

            # For all other segments
            # We take the points between the end of the segment
            # and the end of the previous segment.
            else:
                all_points_segment_df = self.get_all_points_of_one_segment(
                    start=self.segments_schedule[f'segment_{i - 1}']['end'],
                    end=self.segments_schedule[f'segment_{i}']['end'])
                segment = Segment(all_points_segment_df, activity_number)
                segment.compute_metrics()
                self.segments.append(segment)

    def compute_type_previous_segment(self):

        """
        Calculates the type of the previous segment with a list of instances of class Segment
        """

        for i, segment in enumerate(self.segments):
            if i == 0:
                self.segments[i].type_previous_segment = 'start'
            elif self.segments[i - 1].gain_altitude < 0:
                self.segments[i].type_previous_segment = 'downhill'
            elif self.segments[i - 1].gain_altitude > 0:
                self.segments[i].type_previous_segment = 'uphill'
            else:
                self.segments[i].type_previous_segment = 'flat'

    def debug_strava(self):

        df = pd.DataFrame()
        for segment in self.segments:
            metrics = {
                "activity_number": segment.activity_number,
                "date": segment.date,
                "duration": segment.duration,
                "average_power": segment.average_power,
                "average_speed": segment.average_speed,
                "average_heart_rate": segment.average_heart_rate,
                "average_cadence": segment.average_cadence,
                "gain_altitude": segment.gain_altitude,
                "distance": segment.distance,
                "vertical_drop": segment.vertical_drop
            }
            df = df.append(metrics, ignore_index=True)

        total_duration = df['duration'].sum()
        total_distance = df['distance'].sum()
        mean_speed = ((total_distance * 3600) / total_duration) / 1000
        gain_altitude_positive = df.loc[df['gain_altitude'] >= 0]
        gain_altitude = gain_altitude_positive['gain_altitude'].sum()
        mean_power = df['average_power'].mean()
        mean_cadence = df['average_cadence'].mean()

        print(df)
        print(f'Durée totale(sec) : {total_duration}')
        print(f'Distance totale(km) : {(total_distance / 1000).round(2)}')
        print(f'Vitesse moyenne(km/h): {mean_speed.round(2)}')
        print(f'Denivelée: {gain_altitude}')
        print(f'Puissance moyenne : {mean_power.round(2)}')
        print(f'Cadence moyenne: {mean_cadence.round(2)}')

    @staticmethod
    def compute_altitude_gain(dataframe):
        """
        Calculation of the altitude difference between n and n-1
        Takes a dataframe as input
        Return a dataframe with a new column 'altitude_gain'
        """
        altitude_gain = [np.nan]
        for i in range(dataframe.shape[0]):
            if i > 0:
                altitude_gain.append(dataframe['altitude'][i] -
                                     dataframe["altitude"][i - 1])
        dataframe['altitude_gain'] = altitude_gain
        return dataframe

    @staticmethod
    def segmentation(dataframe):
        """
        Takes a dataframe from a .fit with an altitude_gain column as an input.

        altitude_gain for n equals the difference in altitude between n and n-1
        Calculation of the logical segments (ascent, flat, descent) as a function of altitude gain.
        Compare for each line the altitude gain sign n & n-1.

        Same sign, same segment (ex 8 and 5, same ascent segment)
        Change of sign change of segment (ex 8 and -5, from a downhill segment to an uphill segment)

        Special case for zeros :
        if n = 0 et n-1 != 0 : same segment
        In case of a succession of zeros ( from two ): flat segment

        Returns a dataframe with a segment column
        """
        for i in range(len(dataframe['altitude_gain'])):

            # First row starts at segment zero.
            if i == 0:
                dataframe.loc[i, "segment"] = 0

            # For all other rows
            else:

                # if n and n-1 have the same sign
                if sign_equal(dataframe.loc[i, "altitude_gain"], dataframe.loc[i - 1, "altitude_gain"]):

                    # In the case where n and n-1 are zero
                    if dataframe.loc[i, 'altitude_gain'] == 0 and dataframe.loc[i - 1, 'altitude_gain'] == 0:

                        # In case we are on the second line, we cannot check n-2 if n and n-1 = 0.
                        if i == 1:
                            dataframe.loc[i, "segment"] = dataframe.loc[i - 1, "segment"]
                        else:

                            # if n-2 is not equal to zero
                            # Flat segment, we want to make a new segment, and change it retrospectively,
                            # the segment of n-1 which is no longer a "alone" zero anymore
                            if dataframe.loc[i - 2, 'altitude_gain'] != 0:
                                dataframe.loc[i, "segment"] = dataframe.loc[i - 1, "segment"] + 1
                                dataframe.loc[i - 1, "segment"] = dataframe.loc[i - 1, "segment"] + 1
                            # if n , n-1 , n-2 = 0 , you don't want to change segment
                            # succession of zero
                            else:
                                dataframe.loc[i, "segment"] = dataframe.loc[i - 1, "segment"]

                    # If the same sign without any special case, same segment
                    else:
                        dataframe.loc[i, "segment"] = dataframe.loc[i - 1, "segment"]

                # If not same sign
                else:
                    if dataframe.loc[i, 'altitude_gain'] == 0 and dataframe.loc[i - 1, 'altitude_gain'] != 0:
                        dataframe.loc[i, "segment"] = dataframe.loc[i - 1, "segment"]
                    # Otherwise we change segment
                    else:
                        dataframe.loc[i, "segment"] = dataframe.loc[i - 1, "segment"] + 1
        return dataframe
