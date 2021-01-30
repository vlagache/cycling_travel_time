import datetime
import unittest

import fitparse
import numpy as np
import pandas as pd

from prediction.domain.old_road import Road
from prediction.domain.old_segment import Segment


class RoadTests(unittest.TestCase):

    def setUp(self):
        self.road = Road(fit_file="../fit_files/alpes.fit")

    def assertNotEmpty(self, obj, message):
        self.assertTrue(obj, message)

    def test_parsing_fit_file(self):
        """
        makes sure the parsing of the fit works and returns a FitFile object
        """
        message = "Echec du parse du .fit"
        self.road.parsing_from_fit_file()

        self.assertIsNotNone(self.road.fit_parse,
                             message)
        self.assertIsInstance(self.road.fit_parse,
                              fitparse.base.FitFile,
                              message)

    def test_get_records_from_fit_file(self):
        """
        makes sure that recovering .fit points does not return an empty list.
        """
        self.road.parsing_from_fit_file()
        self.road.get_records_from_fit_file()
        message = "Echec de la récupération des records du .fit"
        self.assertNotEmpty(self.road.records, message)

    def test_get_all_points_of_one_segment(self):
        """
        makes sure that the cutting of the segments is well done
        """
        list_datetime = [
            datetime.datetime(2020, 1, 1),
            datetime.datetime(2020, 1, 2),
            datetime.datetime(2020, 1, 3),
            datetime.datetime(2020, 1, 4),

        ]
        self.road.records = {'timestamp': list_datetime}
        start = datetime.datetime(2020, 1, 1)
        end = datetime.datetime(2020, 1, 3)
        expected_shape = (3, 1)
        all_points_segment = self.road.get_all_points_of_one_segment(start, end)
        message = "Echec de la récupération de tout les points d'un segment"
        self.assertEqual(all_points_segment.shape, expected_shape, message)

    def test_compute_altitude_gain(self):
        """
        makes sure that the dataframe has an extra column,
        that the calculations are correct and that the
        first value of gain_altitude is np.nan
        """
        df = pd.DataFrame({'altitude': [1, 5, 12, -8]})
        df = self.road.compute_altitude_gain(df)
        message = "Echec du calcul des differences d'altitude"
        expected_shape = (4, 2)
        expected_value = df.loc[1, 'altitude'] - df.loc[0, 'altitude']
        self.assertEqual(df.shape, expected_shape, message)
        self.assertEqual(df.loc[1, 'altitude_gain'], expected_value, message)
        self.assertTrue(np.isnan(df.loc[0, 'altitude_gain']))

    def test_segmentation(self):
        """
        makes sure that the logical block segmentation is correct
        """
        df = pd.DataFrame({'altitude_gain': [1, 50, 2, 0, -1, -20, 2, 0, 0, 0]})
        # df = pd.DataFrame({'altitude_gain': [0, 0, 2]})
        df = self.road.segmentation(df)
        expected = [0, 0, 0, 0, 1, 1, 2, 3, 3, 3]
        actual = df['segment'].tolist()
        self.assertEqual(actual, expected)

    def test_compute_segmentation(self):
        self.road.parsing_from_fit_file()
        self.road.compute_segmentation()
        message = "Echec du calcul de l'heure de début et de fin de chaque segment"
        self.assertNotEmpty(self.road.segments_schedule, message)

    def test_compute_metrics_segments(self):
        self.road.parsing_from_fit_file()
        self.road.compute_segmentation()
        self.road.compute_metrics_segments(activity_number=1)
        message = 'Echec de la création et du calcul des métriques de chaque segment'
        for segment in self.road.segments:
            self.assertIsInstance(segment,
                                  Segment,
                                  message)
            self.assertIsNotNone(segment.average_speed, message)

    def test_compute_type_previous_segment(self):
        self.road.parsing_from_fit_file()
        self.road.compute_segmentation()
        self.road.compute_metrics_segments(activity_number=1)
        self.road.compute_type_previous_segment()
        message = 'Echec du calcul du type du segment précédent'
        for segment in self.road.segments:
            self.assertIsNotNone(segment.type_previous_segment, message)
