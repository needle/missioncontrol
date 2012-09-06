from missioncontrol.plugins.base import BasePlugin
from missioncontrol import settings
import requests

HIPCHAT_API_URL = 'https://api.hipchat.com/v1'


class HipChatPlugin(BasePlugin):

    def __init__(self, **kwargs):
        self.token = kwargs.get('token', getattr(settings, "HIPCHAT_TOKEN", None))
        self.room = kwargs.get('room', getattr(settings, "HIPCHAT_ROOM", None))
        self._from = kwargs.get('_from', getattr(settings, "HIPCHAT_FROM", None))

    def _send_hipchat_message(self, message, **kwargs):
        params = {'room_id': self.room,
            'from': self._from,
            'message': message
        }
        params.update(**kwargs)

        return requests.post('%s/rooms/message?auth_token=%s&format=json' %
            (HIPCHAT_API_URL, self.token),
            params=params
        )

    def send_alert(self, alert, *args, **kwargs):
        alert_type = kwargs.get('alert_type', 'alert')
        if alert_type == "alert":
            kwargs['notify'] = 1
            kwargs['color'] = "red"
        elif alert_type == "recovery":
            kwargs['notify'] = 0
            kwargs['color'] = "green"

        return self._send_hipchat_message(alert, **kwargs)
