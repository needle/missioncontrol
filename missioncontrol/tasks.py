from celery import task
from pencil import Pencil
import requests
import simplejson


@task()
def check_graphite_servers():
    from missioncontrol.models import GraphiteServer
    for server in GraphiteServer.objects.all():
        for metricalert in server.metric_alerts.all():
            possibly_alert.delay(metricalert, server)


@task()
def possibly_alert(metricalert, server):
    metric_url = Pencil(begin=metricalert._from).add_metric(
        metricalert.target).format('json').url(
        server.base_url, 0, 0)
    metric_resp = requests.get(metric_url,
        auth=(server.username, server.password))

    metric_json = simplejson.loads(metric_resp.text)
    metricalert.check(metric_json)
