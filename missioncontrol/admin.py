from django.contrib import admin
from missioncontrol.models import GraphiteServer, MetricAlert


class MetricAlertAdmin(admin.TabularInline):
    model = MetricAlert


class GraphiteServerAdmin(admin.ModelAdmin):
    model = GraphiteServer

    inlines = [
        MetricAlertAdmin,
    ]


admin.site.register(GraphiteServer, GraphiteServerAdmin)
