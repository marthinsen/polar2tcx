import unittest
import datetime

import polar2tcx

class Polar2tcxTest(unittest.TestCase):

    def test_ceilTime(self):
        t = datetime.datetime(2015, 7, 15)
        self.assertEqual(t, polar2tcx.ceilTime(t))

        t = datetime.datetime(2015, 7, 15, second=59, microsecond=1)
        tr = datetime.datetime(2015, 7, 15, minute=1)
        self.assertEqual(tr, polar2tcx.ceilTime(t))
