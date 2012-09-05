from missioncontrol import settings


class PluginRegistry(object):

    def _do_import(self, name):
        name = name.split('.')
        klass = name.pop()
        obj = getattr(__import__('.'.join(name), globals(), locals(), [str(klass)], -1), str(klass))()
        return obj

    def __init__(self):
        self._plugins = [self._do_import(plugin)
            for plugin in getattr(settings, "NOTIFICATION_PLUGINS", [])]

    def notify_plugins(self, message):
        for plugin in self._plugins:
            plugin.send_alert(message)


def init():
    return PluginRegistry()
