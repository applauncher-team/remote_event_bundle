from kafka_bundle import KafkaManager
import inject
from applauncher.kernel import EventManager, Event
import json
import logging
from applauncher.kernel import Kernel
import socket

class KafkaBackend(object):

    def __init__(self, group_id=None):
        self.run = True
        self.kafka = inject.instance(KafkaManager)
        self.logger = logging.getLogger("kafka-event-backend")
        self.group_id = group_id if group_id else socket.gethostname()

    def shutdown(self):
        self.run = False

    def register_events(self, events):
        kernel = inject.instance(Kernel)
        if len(events) > 0:
            kernel.run_service(lambda event_list, gid: self.kafka.subscribe(
                topics=[i.name for i in event_list],
                group_id=gid,
                consumer_callback=self.callback,
                poll_timeout=2
            ), events, self.group_id)

    def callback(self, message):
        em = inject.instance(EventManager)
        event = Event()
        event.__dict__ = json.loads(message.value())
        headers = message.headers()
        signals = []
        if headers:
            for key, value in headers:
                if key == "signals":
                    signals = json.loads(value)
        event._signals = signals
        event._propagated = True
        em.dispatch(event)

    def propagate_remote_event(self, event):
        if not hasattr(event, "_propagated"):
            data = event.__dict__
            try:
                r = self.kafka.produce(topic=event.event_name, message=json.dumps(data).encode(), headers={"signals": json.dumps(event._signals)})
                self.logger.info("Propagated event" + event.event_name)
                event._propagated = True
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)
