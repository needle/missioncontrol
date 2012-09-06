from django.db import models
import operator
import simplejson
from missioncontrol import settings
from missioncontrol import plugins
from collections import defaultdict


class GraphiteServer(models.Model):
    name = models.CharField(max_length=64)
    base_url = models.CharField(max_length=128)
    username = models.CharField(max_length=64, null=True, blank=True)
    password = models.CharField(max_length=64, null=True, blank=True)

    def __unicode__(self):
        return self.name


class MetricAlert(models.Model):

    KIND_CHOICES = (
        ('avg', 'Average'),
        ('total', 'Total'),
        ('single', 'Single')
    )

    OPERATOR_CHOICES = (
        ('gt', '>'),
        ('ge', '>='),
        ('lt', '<'),
        ('le', '<='),
        ('eq', '==')
    )

    target = models.CharField(max_length=256, help_text="The graphite target path")
    _from = models.CharField(max_length=64,
        help_text="http://graphite.readthedocs.org/en/1.0/url-api.html#from-until")
    threshold = models.IntegerField()
    operator = models.CharField(choices=OPERATOR_CHOICES, max_length=2,
        help_text='The operator used to compare the data with the threshold (i.e. data > threshold)')
    kind = models.CharField(choices=KIND_CHOICES, max_length=16,
        help_text='Average is the average of all data points returned, total is the total')
    server = models.ForeignKey('GraphiteServer', related_name='metric_alerts')
    notify_every = models.IntegerField(help_text="Number of checks to notify after", default=30)

    def do_alert(self, alert_type="alert", value=0, target=None, **kwargs):
        if alert_type == "alert":
            message = "%s is %s %i (actual: %i)" % (
                target, self.operator, self.threshold, value)
        elif alert_type == "recovery":
            message = "%s is within normal again" % target
        plugin_registry.notify_plugins(message, instance=self,
            alert_type=alert_type, target=target, **kwargs)

    def check(self, json):
        _operator = getattr(operator, self.operator, operator.eq)
        for target in json:
            values = defaultdict(int)
            datapoints = [x[0] for x in target['datapoints'] if x[0] is not None]
            for value in datapoints:
                values['total'] += value
                if _operator(value, values['single']):
                    values['single'] = value
            values['average'] = values['total'] / len(datapoints)

            if _operator(values[self.kind], self.threshold):
                self.do_alert(alert_type="alert",
                    value=values[self.kind],
                    target=target['target'])
            else:
                self.do_alert(alert_type="recovery",
                    value=values[self.kind],
                    target=target['target'])


plugin_registry = plugins.init()
