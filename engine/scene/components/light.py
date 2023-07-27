from glm import vec3, radians, normalize

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
        self._direction = normalize(vec3(direction))

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


class AreaLightComponent(Component):
    def __init__(self, game_object=None, color=(1, 1, 1), intensity=1, points=(vec3(0, 0, 0),
                                                                               vec3(1, 0, 0),
                                                                               vec3(0, 0, 1),
                                                                               vec3(1, 0, 1))):
        super().__init__(game_object)
        self._color = vec3(color)
        self._intensity = intensity
        self._points = points

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self, value):
        if self._intensity != value:
            self._intensity = float(value)
            self.update()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        if self._color != value:
            self._color = vec3(value)
            self.update()

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, value):
        if self._points != value:
            self._points = tuple(vec3(pos) for pos in value)
            self.update()
