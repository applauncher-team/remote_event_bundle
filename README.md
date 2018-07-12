# Remote events for applauncher

This bundle is designed for distributed events among multiple applauncher applications. At this moment
only redis broker is supported

Installation
-----------
```bash
pip install remote_event_bundle 
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

Configuration
-------------
```yml
remote_event:
  events:
    - name: new_file_event
```
Check [redis_bundle](https://github.com/applauncher-team/redis_bundle) documentation if need a custom
redis configuration

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
Now the python code (the receiver can use exacly the same event or another that just uses the same name)
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