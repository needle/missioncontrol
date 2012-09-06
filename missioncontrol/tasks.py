from celery.decorators import periodic_task
from pencil import Pencil
import requests
from missioncontrol import settings
from datetime import timedelta


@periodic_task(run_every=timedelta(seconds=settings.POLL_INTERVAL))
def check_graphite_servers():
    from missioncontrol.models import GraphiteServer
    for server in GraphiteServer.objects.all():
        for metricalert in server.metric_alerts.all():
            metric_url = Pencil(begin=metricalert._from).add_metric(
                metricalert.target).format('json').url(
                server.base_url, 0, 0)
            metric_resp = requests.get(metric_url,
                auth=(server.username, server.password))

            metricalert.check(metric_resp.json)
