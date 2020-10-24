class BaseEvent:
    _fields_ = ()

    @classmethod
    def create_meta(cls, name, attributes=()):
        return type(name, (cls, ), {'_fields_': cls._fields_ + attributes})

    def __init__(self, *args, instant=False):
        self.instant = instant
        for field, arg in zip(self._fields_, args):
            setattr(self, field, arg)


class BaseEventReceiver:
    _event_subscriptions_ = ()

    def __init__(self):
        for evt_type in self._event_subscriptions_:
            MainEventManager.add_handler(self, evt_type)

    def on_event(self, evt: BaseEvent):
        pass

    def __del__(self):
        pass  # todo unsubscribe from events and move it from __del__
              # (it will not be called because object stored in event manager


class EventManager:
    def __init__(self):
        self.handlers = {}
        self.events = []

    def poll_events(self):
        for evt in self.events:
            self._poll_event(evt)
        self.events.clear()

    def _poll_event(self, evt):
        try:
            handlers = self.handlers[evt.__class__]
        except KeyError:
            pass
        else:
            for handler in handlers:
                handler.on_event(evt)

    def add_event(self, event: BaseEvent):
        if event.instant:
            self._poll_event(event)
        else:
            self.events.append(event)

    def add_handler(self, obj: BaseEventReceiver, event_type: BaseEvent):
        try:
            self.handlers[event_type].append(obj)
        except KeyError:
            self.handlers[event_type] = [obj]


# todo make event manager pinned to scene
MainEventManager = EventManager()
