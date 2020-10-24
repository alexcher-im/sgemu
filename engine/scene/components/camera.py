from glm import pi as pi_func, vec3, normalize, clamp, acos, asin, cross, rotate, mat4, vec4, cos, sin, radians

from ...event.base import MainEventManager
from ..component import ComponentUpdateEvent, Component

pi = pi_func()
CameraDataUpdateEvent = ComponentUpdateEvent.create_meta('CameraDataUpdateEvent')


class CameraComponent(Component):
    def __init__(self, game_object=None, render_target=None, render_distance=10000, activate=False, fov=0.0):
        super(CameraComponent, self).__init__(game_object)
        self.render_target = render_target
        self.fov = radians(fov)  # radians
        self.render_distance = render_distance
        self.activate = activate
    
    def on_attach(self, game_object):
        super(CameraComponent, self).on_attach(game_object)
        if self.activate:
            self.game_object.scene.set_active_camera(self)
        del self.activate

    def set_fov(self, fov):
        self.fov = radians(fov)

    def set_render_target(self, render_target):
        self.render_target = render_target

    def update(self):
        MainEventManager.add_event(CameraDataUpdateEvent(self))
