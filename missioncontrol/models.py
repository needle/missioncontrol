from django.db import models
import operator
from collections import defaultdict
from pencil import Pencil
import datetime
from missioncontrol import plugins

plugin_registry = plugins.init()


class GraphiteServer(models.Model):
    name = models.CharField(max_length=64)
    base_url = models.CharField(max_length=128)
    username = models.CharField(max_length=64, null=True, blank=True)
    password = models.CharField(max_length=64, null=True, blank=True)

    def __unicode__(self):
        return self.name


class ThresholdViolation(models.Model):

    STATUS_CHOICES = (
        ('resolved', 'Resolved'),
        ('ongoing', 'Ongoing'),
    )

    target = models.CharField(max_length=256)
    metricalert = models.ForeignKey('MetricAlert')
    first_violation = models.DateTimeField(blank=True, auto_now_add=True)
    last_violation = models.DateTimeField(blank=True, auto_now_add=True)
    current_status = models.CharField(choices=STATUS_CHOICES, max_length=64)
    threshold_violated = models.IntegerField()

    @property
    def graph_url(self):
        at = "%H:%M_%Y%m%d"
        graph_url = Pencil(begin=self.first_violation.strftime(at),
            until=self.last_violation.strftime(at))
        graph_url.add_metric(self.metricalert.target)
        graph_url.add_metric("threshold(%i)" % self.threshold_violated,
            alias="Threshold", colors="blue,red")

        return graph_url.url(self.metricalert.server.base_url, 586, 306)


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

    def update_or_create_threshold_violation(self, target, alert_type):
        # TODO: Separate this out into different functions
        if alert_type == "alert":
            viol, created = ThresholdViolation.objects.get_or_create(
                target=target,
                metricalert=self,
                current_status="ongoing",
                threshold_violated=self.threshold
            )
            viol.last_violation = datetime.datetime.now()
            viol.save()
        elif alert_type == "recovery":
            try:
                viol = ThresholdViolation.objects.get(
                    target=target,
                    metricalert=self,
                    current_status="ongoing")
                viol.current_status = "resolved"
                viol.save()
            except ThresholdViolation.DoesNotExist:
                pass

    def _do_alert(self, alert_type="alert", value=0, target=None, **kwargs):
        if alert_type == "alert":
            message = "%s %s is %s %i (actual: %i)" % (
                target, self.kind, self.operator, self.threshold, value)
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
                self._do_alert(alert_type="alert",
                    value=values[self.kind],
                    target=target['target'])
            else:
                self._do_alert(alert_type="recovery",
                    value=values[self.kind],
                    target=target['target'])
