import numpy as np

from ..event.base import BaseEventReceiver
from ..event.tick import TickEvent
from ..event.scene import SceneChangeEvent
from .uniformed import UniformedRenderer


class SceneRenderer(BaseEventReceiver):
    # todo remove scene change event (accept events only from specific scene)
    _event_subscriptions_ = (TickEvent, SceneChangeEvent)

    def __init__(self, scene, uniformed: UniformedRenderer):
        self.scene = scene
        super(SceneRenderer, self).__init__()
        self.uniformed = uniformed
        self.uniformed.process_deps(scene)

        self.raw = uniformed.src_renderer
        # todo may be it will be better to remove this
        self.sampler_data = uniformed.sampler_data  # must be in chain
        self.attribute_data = uniformed.attribute_data  # must be in chain

        # methods
        self.draw = self.raw.draw  # must be in chain

    @property
    def fbo(self):
        return self.raw.fbo

    @property
    def meshes(self):
        return self.raw.meshes

    def on_event(self, evt):
        if isinstance(evt, TickEvent) or isinstance(evt, SceneChangeEvent):
            self.raw.shader_prog.use()
            for name, setter in self.uniformed.setters.items():
                setter, np_type = setter
                setter(1, np.array(self.scene.static_data[name]), np_type)  # todo get count from numpy array length
