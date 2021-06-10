import logging
import importlib
from typing import List
from pydantic import BaseModel
from dependency_injector import containers, providers
from applauncher.event import KernelReadyEvent
from applauncher.applauncher import Configuration, ServiceContainer
from .event import RemoteEvent

logger = logging.getLogger("remote-event")


class EventConfig(BaseModel):
    name: str


class RemoteEventConfig(BaseModel):
    backend: str = "kafka"
    events: List[EventConfig] = []


def backend_loader(configuration):
    logger.info("Initializing backend")
    backend_module = \
        importlib.import_module(f'remote_event_bundle.backend.{configuration.remote_event.backend}_backend')
    backend_class = getattr(backend_module, f"{configuration.remote_event.backend.capitalize()}BackendContainer")
    backend = backend_class(
        configuration=configuration
    )
    yield backend
    logger.info("Stopping backend")
    backend.shutdown_resources()


class RemoteEventContainer(containers.DeclarativeContainer):
    config = providers.Dependency(instance_of=RemoteEventConfig)
    configuration = Configuration()

    backend = providers.Resource(
        backend_loader,
        configuration=configuration
    )


class RemoteEventBundle(object):

    def __init__(self):
        self.logger = logging.getLogger("remote-event")
        self.config_mapping = {
            "remote_event": RemoteEventConfig
        }

        self.injection_bindings = {
            "remote_event": RemoteEventContainer
        }

        self.event_listeners = [
            (RemoteEvent, self.propagate_remote_event)
        ]

        self.services = [
            ("remote-event-listener", self.event_listener, [], {})
        ]

    def event_listener(self):
        ServiceContainer.remote_event.backend().listen()

    def propagate_remote_event(self, event):
        ServiceContainer.remote_event.backend().propagate_remote_event(event)

