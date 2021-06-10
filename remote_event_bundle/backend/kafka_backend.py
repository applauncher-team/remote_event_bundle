import json
import logging


from dependency_injector import containers, providers
from applauncher.applauncher import ServiceContainer
from applauncher.event import Event

logger = logging.getLogger("kafka-event")


def propagate_remote_event(event, producer):
    if not hasattr(event, "_propagated"):
        data = event.__dict__
        try:
            producer.produce(topic=event.event_name, value=json.dumps(data).encode(), headers={"signals": json.dumps(event._signals)})
            logger.info("Propagated event " + event.event_name)
            event._propagated = True
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(str(e))


def producer_resource():
    producer = ServiceContainer.kafka.producer()
    logger.info("Producer ready")
    yield producer
    logger.info("Flushing pending messages before exit")
    producer.flush()


def consumer_resource():
    consumer = ServiceContainer.kafka.consumer()
    logger.info("Kafka consumer created")
    yield consumer
    logger.info("Closing consumer")
    consumer.close()


def dispatch_event(message):
    try:
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
        ServiceContainer.event_manager.dispatch(event)
    except Exception as e:
        logger.error(str(e))

def listener(consumer, configuration):
    events = [i.name for i in configuration.remote_event.events]
    if len(events) > 0:
        consumer.subscribe(events)
        logger.info("Listening consumer events %s", events)
        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    print("Consumer error: {}".format(msg.error()))
                    continue
                dispatch_event(msg)
        except RuntimeError as e:
            logger.info("Listener finished: %s", str(e))
    else:
        logger.info("No events to listen")


class KafkaBackendContainer(containers.DeclarativeContainer):
    configuration = providers.Dependency()

    producer = providers.Resource(
        producer_resource
    )

    consumer = providers.Resource(
        consumer_resource
    )

    propagate_remote_event = providers.Callable(
        propagate_remote_event,
        producer=producer
    )

    listen = providers.Callable(
        listener,
        consumer=consumer,
        configuration=configuration
    )

    # backend = providers.Resource(
    #     providers.Callable(
    #         backend_loader,
    #         configuration=configuration
    #     )
    # )

#
# class KafkaBackend(object):
#
#     def __init__(self, group_id=None):
#         self.run = True
#         self.kafka = inject.instance(KafkaManager)
#         self.logger = logging.getLogger("kafka-event-backend")
#         self.group_id = group_id if group_id else socket.gethostname()
#
#     def shutdown(self):
#         self.run = False
#
#     def register_events(self, events):
#         kernel = inject.instance(Kernel)
#         if len(events) > 0:
#             kernel.run_service(lambda event_list, gid: self.kafka.subscribe(
#                 topics=[i.name for i in event_list],
#                 group_id=gid,
#                 consumer_callback=self.callback,
#                 poll_timeout=2
#             ), events, self.group_id)
#
#     def callback(self, message):
#         em = inject.instance(EventManager)
#         event = Event()
#         event.__dict__ = json.loads(message.value())
#         headers = message.headers()
#         signals = []
#         if headers:
#             for key, value in headers:
#                 if key == "signals":
#                     signals = json.loads(value)
#         event._signals = signals
#         event._propagated = True
#         em.dispatch(event)
#
#     def propagate_remote_event(self, event):
#         if not hasattr(event, "_propagated"):
#             data = event.__dict__
#             try:
#                 r = self.kafka.produce(topic=event.event_name, message=json.dumps(data).encode(), headers={"signals": json.dumps(event._signals)})
#                 self.logger.info("Propagated event " + event.event_name)
#                 event._propagated = True
#             except Exception as e:
#                 import traceback
#                 traceback.print_exc()
#                 print(e)
