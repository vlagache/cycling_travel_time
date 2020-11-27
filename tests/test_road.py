import unittest

import fitparse
import numpy as np
import pandas as pd

from domain.road import Road


class RoadTests(unittest.TestCase):

    def setUp(self):
        self.road = Road("../fit_files/alpes.fit")

    def assertNotEmpty(self, obj, message):
        self.assertTrue(obj, message)

    def test_parse_fit_file(self):
        """
        makes sure the parsing of the fit works and returns a FitFile object
        """
        message = "Echec du parse du .fit"
        self.assertIsNotNone(self.road.fit_file,
                             message)
        self.assertIsInstance(self.road.fit_file,
                              fitparse.base.FitFile,
                              message)

    def test_get_records_from_fit_file(self):
        """
        makes sure that recovering .fit points does not return an empty list.
        """
        self.road.get_records_from_fit_file()
        message = "Echec de la récupération des records du .fit"
        self.assertNotEmpty(self.road.records, message)

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
        df = self.road.segmentation(df)
        expected = [0, 0, 0, 0, 1, 1, 2, 3, 3, 3]
        actual = df['segment'].tolist()
        self.assertEqual(actual, expected)
