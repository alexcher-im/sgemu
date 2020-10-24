from ctypes import POINTER, c_int32

from glm import cos

from .base import BaseRendererDependence
from ...scene.component import ComponentAddEvent
from ...scene.components.light import LightDataUpdateEvent, SpotLightComponent


class CurrentDependence(BaseRendererDependence):
    _event_subscriptions_ = (LightDataUpdateEvent, ComponentAddEvent)
    BUFFER_IS_ARRAY = True
    DEPENDENCY_NAME = 'SpotLightStorage'

    def __init__(self, scene, *args, **kwargs):
        super(CurrentDependence, self).__init__(scene, *args, struct_offset=4,
                                                structure=[['diffuse_color', 3],  ['linear', 1],
                                                           ['specular_color', 3], ['quadratic', 1],
                                                           ['pos', 3],            ['cut_off', 1],
                                                           ['direction', 3],      ['outer_cut_off', 1]],
                                                **kwargs)
        self.component_dict = {}

    def on_event(self, evt):
        component = evt.component
        if not isinstance(component, SpotLightComponent):
            return
        if isinstance(evt, ComponentAddEvent):
            self.buffer.add_frame(diffuse_color=component.diffuse_color, linear=0, quadratic=0,
                                  specular_color=component.specular_color, pos=component.game_object.abs_pos,
                                  cut_off=cos(component.cut_off), outer_cut_off=cos(component.outer_cut_off),
                                  direction=component.direction)
            self.component_dict[id(component)] = len(self.component_dict)
            self.buffer.get_raw_memory_data_setter(POINTER(c_int32))[0] = len(self.component_dict)
            self.full_upload()
        elif isinstance(evt, LightDataUpdateEvent):
            index = self.component_dict[id(component)]
            setter = self.buffer[index]
            setter.diffuse_color = component.diffuse_color
            setter.specular_color = component.specular_color
            setter.direction = component.direction
            setter.cut_off = cos(component.cut_off)
            setter.outer_cut_off = cos(component.outer_cut_off)
            setter.pos = component.game_object.abs_pos
            start, size = self.buffer.struct.get_frame_pointer(index)
            self.buffer.chunk_upload(4+start, size)

    def add_setter(self, *_, **__):
        pass

    def full_upload(self):
        self.buffer.upload()
        self.buffer.force_upload()
