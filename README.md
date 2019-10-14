# Remote events for applauncher

This bundle is designed for distributed events among multiple applauncher applications. At this moment
redis and kafka backend are supported

Installation
-----------
Using redis backend
```bash
pip install remote_event_bundle 
pip install redis_bundle 
```
Then add to your main.py
```python
import remote_event_bundle
import redis_bundle

bundle_list = [
    redis_bundle.RedisBundle(),
    remote_event_bundle.RemoteEventBundle()
]
```
and for kafka
```bash
pip install remote_event_bundle 
pip install kafka_bundle 
```
Then add to your main.py
```python
import remote_event_bundle
import kafka_bundle

bundle_list = [
    kafka_bundle.KafkaBundle(),
    remote_event_bundle.RemoteEventBundle()
]
```

you can also use mqtt
```bash
pip install remote_event_bundle 
pip install mqtt_bundle 
```
```python
import remote_event_bundle
import mqtt_bundle

bundle_list = [
    mqtt_bundle.MqttBundle(),
    remote_event_bundle.RemoteEventBundle()
]
```

Configuration
-------------
There default backend is redis. This configuration is suitable for redis
```yml
remote_event:
  events:
    - name: new_file_event
```
Check [redis_bundle](https://github.com/applauncher-team/redis_bundle) documentation if need a custom
redis configuration

For kafka, you can use this config
```yml
remote_event:
  backend: kafka
  group_id: file-consumer  # hostname is used by default if no group_id is provided
  events:
    - name: new_file_event
```
Check [kafka_bundle](https://github.com/applauncher-team/kafka_bundle) for the kafka configuration

For mqtt, you can use this config
```yml
remote_event:
  backend: mqtt
  events:
    - name: new_file_event
```
Check [mqtt_bundle](https://github.com/applauncher-team/mqtt_bundle) for mqtt configuration

How does it work?
-----------------
This bundle provides a special event called `remote_event_bundle.RemoteEvent`. If you want to propagate your event, it must
inherit this class.

Of course, not all instances can listen all kind of event. The idea is that some instances do some
specific tasks (process a big file, are under a firewall...) so this is the reason because you have to
specify the events (otherwise, some events could be received by the wrong instance that will ignore them).

In one instance we have this code
```python
from remote_event_bundle import RemoteEvent
from applauncher.kernel import EventManager
import inject

class NewFileEvent(RemoteEvent):
    event_name = 'new_file_event'
    def __init__(self, path):
        self.path = path

em = inject.instance(EventManager)
em.dispatch(NewFileEvent("/uploads/video1.mp4"))

```

The instance that will receive this event:
First configure the bundle:
```yml
remote_event:
  events:
    - name: new_file_event
```
Now the python code (the receiver can use exactly the same event or another that just uses the same name)
```python
from applauncher.kernel import Event, EventManager
import inject

class NewFileEvent(Event):
    event_name = 'new_file_event'
    def __init__(self, path):
        self.path = path

def listener(event):
    print("New file received", event.path)
    
em = inject.instance(EventManager)
em.add_listener(NewFileEvent, listener)

```

Behind the scenes, this bundle will listen all RemoteEvents. Once a RemoteEvent is dispatched, the bundle
will serialize it and send it to a redis queue. The other instance will be listening the queues that you
configured, then receive the message, deserialize and dispatch this event. 

Full example
============
A final example could be something like this. Of course, the code is the same for all backends

file `example_bundle/__init__.py`

```python
from applauncher.kernel import KernelReadyEvent, EventManager
import inject
from remote_event_bundle import RemoteEvent

# Defining the event
class MyEvent(RemoteEvent):
    event_name = "my_event"

    def __init__(self, payload):
        self.payload = payload

class ExampleBundle(object):

    def __init__(self):
        self.event_listeners = [
            (KernelReadyEvent, self.kernel_ready),
            (MyEvent, self.new_event)
        ]
    
    # Receving the event
    def new_event(self, event):
        print(f"NEW EVENT {event.payload}")

    # Sending the event
    def kernel_ready(self, event):
        em = inject.instance(EventManager)  #  type: EventManager
        em.dispatch(MyEvent("This is the payload"))
```

file `main.py`
```python
from applauncher.kernel import Environments, Kernel
import mqtt_bundle
import example_bundle
import remote_event_bundle

bundle_list = [
    mqtt_bundle.MqttBundle(),
    example_bundle.ExampleBundle(),
    remote_event_bundle.RemoteEventBundle()
]

with Kernel(Environments.DEVELOPMENT, bundle_list) as kernel:
    kernel.wait()

```

and finally the `config/config.yml`

```yml
# We are going to use the mqtt, so we have to configure the mqtt_bundle
mqtt:
  host: my_mqtt_host
  username: my_username_if_any
  password: my_password_if_any

remote_event:
  backend: mqtt  # remember that here you can use any of the available backends
  events:
    - name: my_event
```

and run `python main.py`