from mqtt_bundle.bundle import MqttMessageEvent
import paho.mqtt.client as mqtt
import inject
import logging
import socket
from applauncher.kernel import Kernel, EventManager, Event
import json


class MqttBackend(object):

    def __init__(self, group_id=None):
        self.run = True
        self.client = inject.instance(mqtt.Client)
        self.logger = logging.getLogger("mqtt-event-backend")
        self.group_id = group_id if group_id else socket.gethostname()

    def shutdown(self):
        self.run = False

    @inject.params(event_manager=EventManager)
    def register_events(self, events, event_manager: EventManager):
        event_manager.add_listener(MqttMessageEvent, self.callback)
        for i in events:
            self.client.subscribe(i.name)
            print("subscribed to", i.name)

    def callback(self, event: MqttMessageEvent):
        em = inject.instance(EventManager)
        print(event.event_name)
        print(event.message)
        print(event.userdata)
        return
        event_data = json.loads(message.value())
        event = Event()
        event.__dict__ = event_data["data"]
        event._signals = event_data["signals"]
        event._propagated = True
        em.dispatch(event)

    def propagate_remote_event(self, event):
        if not hasattr(event, "_propagated"):
            data = event.__dict__
            try:
                r = self.topic_manager.publish(event.event_name, json.dumps({"data": data, "signals": event._signals}).encode())
                self.logger.info("Propagated event" + event.event_name)
                event._propagated = True
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)
