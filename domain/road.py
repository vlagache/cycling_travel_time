import fitparse
import numpy as np
import pandas as pd

from utils.functions import sign_equal


class Road:

    def __init__(self, fit_file):
        self.fit_file = fitparse.FitFile(fit_file)
        self.records = []
        self.segmented_records = []

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
            "datetime" (datetime),
        }

        """
        duplicate_infos = ['enhanced_altitude',
                           'enhanced_speed']
        for record in self.fit_file.get_messages("record"):
            record_dict = {}
            for data in record:
                if data.value is not None:
                    if data.name in duplicate_infos:
                        continue
                    record_dict[data.name] = data.value
            self.records.append(record_dict)

    def compute_segmentation(self):

        self.get_records_from_fit_file()

        df = pd.DataFrame(self.records)

        # Reducing the size of the dataframe
        reduced_dataframe = df.iloc[::20, :]
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

        self.segmented_records = segmented_df.to_dict('records')

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
