from ..sound.context import AudioContext
from ..event.base import MainEventManager, BaseEventReceiver
from ..event.tick import TickEvent
from .game_object import GameObject
from .component import ComponentUpdateEvent, ComponentAddEvent
from .components.camera import CameraComponent
from .components.render import RenderComponent, CachedComponentsGroup

SetCameraEvent = ComponentUpdateEvent.create_meta('SetCameraEvent', ('camera', ))


class Scene(BaseEventReceiver):
    _event_subscriptions_ = (ComponentAddEvent, TickEvent)

    def __init__(self, sound_context=True):
        # todo move all cached to other dedicated class
        # todo implement removing renderers, dependencies, cached render components
        super(Scene, self).__init__()
        self.root_obj = GameObject(scene=self)
        self.events = []
        self.active_renderers = []
        self.active_camera = None
        self.sound_context = None
        if sound_context is True:
            self.sound_context = AudioContext()
        elif isinstance(sound_context, AudioContext):
            self.sound_context = sound_context
        else:
            raise ValueError("Not Supported")  # todo log this instead of exception

        self.renderer_dependencies = {}
        self._cached_render_components = []
        self.static_data = {'camera_pos': None}
        self.event_manager = MainEventManager

    def set_active_camera(self, obj):
        component = obj
        if isinstance(obj, GameObject):
            component = obj.get_component(CameraComponent)
        if not isinstance(component, CameraComponent):
            raise TypeError("No camera component found")
        self.active_camera = component
        MainEventManager.add_event(SetCameraEvent(component))

    def draw(self):
        # group must not be empty: remove it if so
        for group in self._cached_render_components:
            group.draw()

        for item in self.active_renderers:
            item.second_pass(self.active_camera.render_target)
        self.active_camera.render_target.finish()

    def add_render_component(self, component: RenderComponent):
        if component.renderer not in self.active_renderers:
            self.active_renderers.append(component.renderer)
            self._cached_render_components.append(CachedComponentsGroup())
        self._cached_render_components[self.active_renderers.index(component.renderer)].append(component)

    def on_tick(self):
        self.static_data['camera_pos'] = self.active_camera.game_object.abs_pos

    def on_event(self, evt):
        if isinstance(evt, ComponentAddEvent):
            if isinstance(evt.component, RenderComponent):
                self.add_render_component(evt.component)
        elif isinstance(evt, TickEvent):
            self.on_tick()
