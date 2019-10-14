from kombu import Connection
import inject
from applauncher.kernel import EventManager, Event
import amqp
import logging
from applauncher.kernel import Kernel
from kombu import Exchange, Queue
import socket


class AmqpBackend(object):

    def __init__(self, group_id=None):
        self.run = True
        self.logger = logging.getLogger("amqp-event-backend")
        self.connection = inject.instance(Connection)
        self.producer = self.connection.Producer(serializer='json')
        self.group_id = group_id

    def shutdown(self):
        self.run = False

    def register_events(self, events):
        kernel = inject.instance(Kernel)
        kernel.run_service(self.listener, events)

    def callback(self, body, message):
        # print(f'From {message.delivery_info["exchange"]}: {body}')
        if body:
            try:
                em = inject.instance(EventManager)
                # event_data = json.loads(body.decode())
                event_data = body
                event = Event()
                event.__dict__ = event_data["data"]
                event._signals = event_data["signals"]
                event._propagated = True
                em.dispatch(event)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)
        message.ack()

    def listener(self, event_list):
        group_id = self.group_id or socket.gethostname()
        # 5 days until the queue expires for inactivity
        queues = [Queue(f"{group_id}_{exchange.name}", exchange=Exchange(exchange.name, 'fanout'), expires=5*24*60*60) for exchange in event_list]
        with self.connection.Consumer(queues, callbacks=[self.callback]):
            # Process messages and handle events on all channels
            while self.run:
                try:
                    self.connection.drain_events(timeout=2)
                except socket.timeout:
                    pass
                except OSError as e:
                    if self.run:
                        # if not running, its because the amqp connection is closed
                        raise e
        self.connection.release()

    def propagate_remote_event(self, event):
        if not hasattr(event, "_propagated"):
            data = event.__dict__
            try:
                self.producer.publish({"data": data, "signals": event._signals}, exchange=event.event_name)
                self.logger.info("Propagated event " + event.event_name)
            except amqp.exceptions.NotFound:
                self.logger.warning(f"Not any listener on the event {event.event_name}")

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)
            event._propagated = True
