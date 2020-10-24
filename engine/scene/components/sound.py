from glm import vec3

from ...event.base import MainEventManager, BaseEventReceiver
from ...event.tick import TickEvent
from ..component import Component, ComponentUpdateEvent
from ...al.listener import SoundListener
from ...al.source import SoundSource

SoundUpdateEvent = ComponentUpdateEvent.create_meta('SoundUpdateEvent')
SoundSourceUpdateEvent = SoundUpdateEvent.create_meta('SoundSourceUpdateEvent')
SoundListenerUpdateEvent = SoundUpdateEvent.create_meta('SoundListenerUpdateEvent')


class SoundSourceComponent(Component, BaseEventReceiver):
    _event_subscriptions_ = (TickEvent, )

    def __init__(self, game_object=None):
        Component.__init__(self, game_object)
        BaseEventReceiver.__init__(self)
        self.source = SoundSource()

    def update(self):
        self.source.set_position(self.game_object.abs_pos)
        MainEventManager.add_event(SoundSourceUpdateEvent(self))

    def play(self, sound):
        sound.bind(self.source)
        self.source.play()

    # todo add a SoundSource methods to this class (aka set_direction)
    def pause(self):
        pass

    def resume(self):
        pass

    def set_gain(self, gain: float):
        pass

    def set_direction(self, direction: vec3):
        pass

    def on_event(self, evt: TickEvent):
        self.source.update()

    def on_attach(self, game_object):
        super(SoundSourceComponent, self).on_attach(game_object)
        self.update()

    # todo add control methods like stopping, pausing, etc


# todo add a MultiSoundSourceComponent that can play more than 1 sound at the same time


class SoundListenerComponent(Component):
    def __init__(self, game_object=None, activate=True):
        super(SoundListenerComponent, self).__init__(game_object)
        self.activate = activate
        self.listener = None

    def on_attach(self, game_object):
        self.listener = SoundListener(game_object.scene.sound_context, self.activate)
        del self.activate
        super(SoundListenerComponent, self).on_attach(game_object)

    def update(self):
        self.listener.set_position(self.game_object.abs_pos)
        self.listener.set_direction(self.game_object.direction)
