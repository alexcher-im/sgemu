from glm import vec3, radians

from ..component import Component, ComponentUpdateEvent
from ...event.base import MainEventManager

LightDataUpdateEvent = ComponentUpdateEvent.create_meta('LightDataUpdateEvent')


class LightComponent(Component):
    def __init__(self, game_object=None, diffuse_color=vec3(1), specular_color=None):
        if specular_color is None:
            specular_color = diffuse_color
        super(LightComponent, self).__init__(game_object)
        self._diffuse_color = diffuse_color
        self._specular_color = specular_color

    @property
    def diffuse_color(self):
        return self._diffuse_color

    @diffuse_color.setter
    def diffuse_color(self, value):
        if self._diffuse_color != value:
            self._diffuse_color = vec3(value)
            self.update()

    @property
    def specular_color(self):
        return self._specular_color

    @specular_color.setter
    def specular_color(self, value):
        if self._specular_color != value:
            self._specular_color = vec3(value)
            self.update()

    def update(self):
        # raise Exception()
        MainEventManager.add_event(LightDataUpdateEvent(self))


class SpotLightComponent(LightComponent):
    # todo add linear and quadratic coefficients
    def __init__(self, game_object=None, cut_off=0, outer_cut_off=None, direction=vec3(0), *args, **kwargs):
        if outer_cut_off is None:
            outer_cut_off = cut_off * 1.1
        super(SpotLightComponent, self).__init__(game_object, *args, **kwargs)
        self._cut_off = radians(cut_off)
        self._outer_cut_off = radians(outer_cut_off)
        self._direction = direction

    @property
    def cut_off(self):
        return self._cut_off

    @cut_off.setter
    def cut_off(self, value):
        if self._cut_off != value:
            self._cut_off = radians(value)
            self.update()

    @property
    def outer_cut_off(self):
        return self._outer_cut_off

    @outer_cut_off.setter
    def outer_cut_off(self, value):
        if self._outer_cut_off != value:
            self._outer_cut_off = radians(value)
            self.update()

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        if self._direction != value:
            self._direction = vec3(value)
            self.update()
