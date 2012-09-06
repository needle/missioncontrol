from missioncontrol import settings
from collections import defaultdict


class PluginRegistry(object):

    def _do_import(self, name):
        name = name.split('.')
        klass = name.pop()
        obj = getattr(__import__('.'.join(name), globals(), locals(), [str(klass)], -1), str(klass))()
        return obj

    def __init__(self):
        self._plugins = [self._do_import(plugin)
            for plugin in getattr(settings, "NOTIFICATION_PLUGINS", [])]

        self._alert_status = defaultdict(lambda: defaultdict(int))

    def _decide_to_notify(self, plugin, instance, target):
        notify = False
        if target not in self._alert_status:
            notify = True
        elif target in self._alert_status and self._alert_status[target][plugin] % instance.notify_every == 0:
            notify = True
        return notify

    def notify_plugins(self, message, alert_type="alert", instance=None, **kwargs):
        target = kwargs.get('target')
        instance.update_or_create_threshold_violation(target, alert_type)
        for plugin in self._plugins:
            if alert_type == "alert":
                if self._decide_to_notify(plugin, instance, target):
                    plugin.send_alert("%s (failed %i times)" % (message,
                        self._alert_status[target][plugin]),
                        alert_type=alert_type, **kwargs)
                self._alert_status[target][plugin] += 1
            elif alert_type == "recovery":
                if target in self._alert_status and plugin in self._alert_status[target]:
                    plugin.send_alert(message, alert_type=alert_type, **kwargs)
                    del self._alert_status[target][plugin]


def init():
    return PluginRegistry()
