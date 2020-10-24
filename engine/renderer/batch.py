from typing import List, Tuple

import numpy as np

from engine.renderer.base import RenderStage, BaseRenderer


class WindowContainer:
    def __init__(self, window):
        self.fbo = window.framebuffer


def chains2blocks(*chains):
    pass


class RenderBatch:
    def __init__(self, passes: List[Tuple[RenderStage, BaseRenderer, bool]]):
        """
        Here's little optimisation: some of the renderers will not be called:
        previous render stage must allow some of the next stage to be executed
        if current render stage does not draw anything: target stage will not be unlocked

        :param passes:
        [0] - renderer to be used
        [1] - container whose framebuffer will be used by the renderer. also it is a stage to be allowed to execute
        [2] - indicator about forcing drawing this stage (not disabled by default)
              (should be used for geometry-pass renderers)
        """
        allowed = [f[2] if len(f) >= 3 else True for f in passes]
        self.passes = [[f[0], f[1], None] for f in passes]
        self.stages_allowed_original = np.array(allowed, 'bool')
        self.stages_allowed = self.stages_allowed_original.copy()
        self.stage_dict = {f[0]: i for i, f in enumerate(self.passes)}
        print('dict', self.stage_dict)

    def set_renderer_in(self, renderer, value):
        self.passes[self.stage_dict[renderer]][2] = value

    def draw(self):
        memoryview(self.stages_allowed)[:] = memoryview(self.stages_allowed_original)
        for i, (render_pass, target_container, draw_list) in enumerate(self.passes):
            if not self.stages_allowed[i]:
                continue
            meshes = draw_list if draw_list is not None else render_pass.meshes

            if render_pass.draw(target_container.fbo, meshes):
                pass  # todo enable next renderer
