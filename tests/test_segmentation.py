import unittest

import pandas as pd

import segmentation


class SegmentationTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_segmentation(self):
        df = pd.DataFrame({'altitude_gain': [1, 50, 2, 0, -1, -20, 2, 0, 0, 0]})
        df = segmentation.segmentation(df)
        expected = [0, 0, 0, 0, 1, 1, 2, 3, 3, 3]
        actual = df['segment'].tolist()
        self.assertEqual(actual, expected)
