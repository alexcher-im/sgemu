from .base import BaseEvent

TickEvent = BaseEvent.create_meta('TickEvent', ('delta_time', ))
