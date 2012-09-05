from django.db import models
import operator
import simplejson
from missioncontrol import settings
from missioncontrol import plugins


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

    def do_alert(self, alert):
        plugin_registry.notify_plugins(alert)

    def check(self, json):
        if isinstance(json, basestring):
            json = simplejson.loads(json)
        _operator = getattr(operator, self.operator, operator.eq)
        for target in json:
            total = 0
            single = 0
            datapoints = [x[0] for x in target['datapoints'] if x[0] is not None]
            for value in datapoints:
                total += value
                if value > single:
                    single = value
            average = total / len(datapoints)

            if self.kind == 'avg':
                if _operator(average, self.threshold):
                    return self.do_alert("%s is %s than %i (%i)" %
                        (target['target'], self.operator, self.threshold, average))
            elif self.kind == 'total':
                if _operator(total, self.threshold):
                    return self.do_alert("%s is %s than %i (%i)" %
                        (target['target'], self.operator, self.threshold, total))
            elif self.kind == 'single':
                if _operator(single, self.threshold):
                    return self.do_alert("%s is %s than %i (%i)" %
                        (target['target'], self.operator, self.threshold, single))


plugin_registry = plugins.init()
