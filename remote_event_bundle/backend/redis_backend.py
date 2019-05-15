from redis import Redis
import inject
from applauncher.kernel import EventManager, Event
import json
import logging
from applauncher.kernel import Kernel


class RedisBackend(object):

    def __init__(self, group_id=None):
        self.run = True
        self.logger = logging.getLogger("redis-event-backend")

    def shutdown(self):
        self.run = False

    def register_events(self, events):
        kernel = inject.instance(Kernel)
        for i in events:
            kernel.run_service(self.listener, i.name)

    def listener(self, queue_name):
        r = inject.instance(Redis)
        em = inject.instance(EventManager)

        while self.run:
            m = r.brpop(queue_name, timeout=2)
            if m is not None:
                event_name, event_data = m
                event_data = json.loads(event_data.decode())
                event = Event()
                event.__dict__ = event_data["data"]
                event._signals = event_data["signals"]
                event._propagated = True
                em.dispatch(event)

    def propagate_remote_event(self, event):
        redis = inject.instance(Redis)
        if not hasattr(event, "_propagated"):
            data = event.__dict__
            try:
                r = redis.lpush(event.event_name, json.dumps({"data": data, "signals": event._signals}).encode())
                self.logger.info("Propagated event " + event.event_name)
                event._propagated = True
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)
