from redis import Redis
from .event import RemoteEvent, Event
import inject
from applauncher.kernel import Configuration, InjectorReadyEvent, EventManager, Kernel, KernelShutdownEvent
import json
import logging


class RemoteEventBundle(object):

    def __init__(self):
        self.logger = logging.getLogger("remote-event")
        self.config_mapping = {
            "remote_event": {
                "events": [{"name": {"type": "string"}}]
            }
        }

        self.event_listeners = [
            (InjectorReadyEvent, self.injector_ready),
            (RemoteEvent, self.propagate_remote_event),
            (KernelShutdownEvent, self.kernel_shutdown)
        ]

        self.run = True

    @inject.params(config=Configuration)
    @inject.params(kernel=Kernel)
    def injector_ready(self, event, config, kernel: Kernel):
        for i in config.remote_event.events:
            kernel.run_service(self.redis_listener, i.name)

    def redis_listener(self, queue_name):
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


    @inject.params(redis=Redis)
    def propagate_remote_event(self, event, redis: Redis):
        if not hasattr(event, "_propagated"):
            data = event.__dict__
            try:
                r = redis.lpush(event.event_name, json.dumps({"data": data, "signals": event._signals}).encode())
                self.logger.info("Propagated event" + event.event_name)
                event._propagated = True
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)

    def kernel_shutdown(self, event):
        self.run = False
