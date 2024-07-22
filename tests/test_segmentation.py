import unittest
import warnings

import pandas as pd

from prediction.utils.functions import gpx_parser, compute_segmentation, haversine

warnings.filterwarnings('ignore')


class SegmentationTests(unittest.TestCase):

    def setUp(self):
        road_directory = './datas/example.gpx'
        gpx_file = open(road_directory, 'r')
        gpx = gpx_file.read()
        self.road = gpx_parser(gpx)
        gpx_file.close()

    def test_segmentation_distance(self):
        """
        makes sure that the sum of the segments is equal
        to the length of the initial route
        """
        df = pd.DataFrame(self.road)
        for i in range(df.shape[0]):
            if i == 0:
                df.loc[i, "distance_to_last_point"] = 0
            else:
                df.loc[i, "distance_to_last_point"] = round(
                    haversine(df['longitude'][i], df['latitude'][i], df['longitude'][i - 1], df['latitude'][i - 1]), 2)
        df['total_distance'] = round(df['distance_to_last_point'].cumsum(), 2)
        expected = df["total_distance"].tail(1).values[0]

        segmentation = compute_segmentation(self.road)
        distance_segmentation = [segment.get("distance") for segment in segmentation]
        actual = sum(distance_segmentation)
        self.assertEqual(actual, expected)
