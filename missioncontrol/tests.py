from django.utils import unittest
from missioncontrol import models


class MetricAlertTestCase(unittest.TestCase):
    JSON = """[
            {
                "target": "test",
                "datapoints": [
                    [
                        null,
                        1346816040
                    ],
                    [
                        1,
                        1346816100
                    ],
                    [
                        1,
                        1346816160
                    ],
                    [
                        1,
                        1346816220
                    ],
                    [
                        2,
                        1346816280
                    ]
                ]
            }
        ]"""

    def setUp(self):
        self.server = models.GraphiteServer.objects.create(name="test",
            base_url="http://test/render")
        self.alert = models.MetricAlert.objects.create(target="test", _from="-5min",
            threshold=1, operator="ge", kind="avg", server=self.server)

    def test_avg(self):
        alert = models.MetricAlert.objects.create(
            target="test",
            _from="-5min",
            threshold=1,
            operator="ge",
            kind="avg",
            server=self.server)
        self.assertIsNotNone(alert.check(self.JSON))

    def test_total(self):
        alert = models.MetricAlert.objects.create(
            target="test",
            _from="-5min",
            threshold=5,
            operator="eq",
            kind="total",
            server=self.server)
        self.assertIsNotNone(alert.check(self.JSON))

    def test_single(self):
        alert = models.MetricAlert.objects.create(
            target="test",
            _from="-5min",
            threshold=2,
            operator="ge",
            kind="total",
            server=self.server)
        self.assertIsNotNone(alert.check(self.JSON))
