import datetime

import numpy as np


def sign_equal(a, b):
    """
    Compares the two-digit sign and indicates whether they are identical
    Takes the 0 as a separate value
    ex : sign_equal(0,-5) >>> False
    Return True/False
    """
    return np.sign(a) == np.sign(b)


def transforms_string_in_datetime(str_date):
    format_date = datetime.datetime.strptime(str_date, "%Y-%m-%dT%H:%M:%SZ")
    new_format = "%d/%m/%Y à %H:%M:%S"
    format_date = format_date.strftime(new_format)
    return format_date
