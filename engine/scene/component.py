from ..event.base import MainEventManager
from ..event.scene import ComponentEvent

ComponentAddEvent = ComponentEvent.create_meta('ComponentAddEvent')
ComponentUpdateEvent = ComponentEvent.create_meta('ComponentUpdateEvent')


class Component:
    def __init__(self, game_object=None):
        self.game_object = game_object

    @property
    def copy(self):
        copy_obj = Component()
        copy_obj.__dict__ = self.__dict__
        copy_obj.game_object = None
        copy_obj.on_copied()
        return copy_obj

    def on_copied(self):
        pass

    def update(self):
        pass

    def on_attach(self, game_object):
        self.game_object = game_object
        MainEventManager.add_event(ComponentAddEvent(self))
        self.update()


class CollideComponent(Component):
    pass


class SoundComponent(Component):
    pass
