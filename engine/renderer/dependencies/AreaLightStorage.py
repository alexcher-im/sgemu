from ctypes import POINTER, c_int32

from .base import BaseRendererDependence
from ...scene.component import ComponentAddEvent
from ...scene.components.light import LightDataUpdateEvent, AreaLightComponent


class CurrentDependence(BaseRendererDependence):
    _event_subscriptions_ = (LightDataUpdateEvent, ComponentAddEvent)
    BUFFER_IS_ARRAY = True
    DEPENDENCY_NAME = 'AreaLightStorage'

    def __init__(self, scene, *args, **kwargs):
        super(CurrentDependence, self).__init__(scene, *args, struct_offset=4,
                                                structure=[['color', 3],  ['intensity', 1],
                                                           ['point0', 3], ['_', 1],
                                                           ['point1', 3], ['__', 1],
                                                           ['point2', 3], ['___', 1],
                                                           ['point3', 3], ['____', 1]],
                                                **kwargs)
        self.component_dict = {}

    def on_event(self, evt):
        component = evt.component
        if not isinstance(component, AreaLightComponent):
            return
        if isinstance(evt, ComponentAddEvent):
            self.buffer.add_frame(color=component.color, intensity=component.intensity,
                                  point0=component.points[0],
                                  point1=component.points[1],
                                  point2=component.points[2],
                                  point3=component.points[3])
            self.component_dict[id(component)] = len(self.component_dict)
            self.buffer.get_raw_memory_data_setter(POINTER(c_int32))[0] = len(self.component_dict)
            self.full_upload()
        elif isinstance(evt, LightDataUpdateEvent):
            index = self.component_dict[id(component)]
            setter = self.buffer[index]
            setter.color = component.color
            setter.intensity = component.intensity
            setter.point0 = component.points[0]
            setter.point1 = component.points[1]
            setter.point2 = component.points[2]
            setter.point3 = component.points[3]
            start, size = self.buffer.struct.get_frame_pointer(index)
            self.buffer.chunk_upload(4+start, size)

    def add_setter(self, *_, **__):
        pass

    def full_upload(self):
        self.buffer.upload()
        self.buffer.force_upload()
