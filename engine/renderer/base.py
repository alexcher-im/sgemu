from typing import Iterable

from ..gl.shader import ShaderProgram
from ..model.model import RenderCompound
from ..gl.framebuffer import StaticFrameBuffer, FrameBuffer


# todo add forward renderer preset and remove this class
class FirstPassRenderer:
    def __init__(self, out_fbo=None):
        if out_fbo is None:
            out_fbo = StaticFrameBuffer
        else:
            out_fbo.add_depth_buffer()
        self.out_fbo = out_fbo
        self.shader_prog = None

    def draw(self, draw_func):
        self.out_fbo.use()
        self.out_fbo.clear()
        self.shader_prog.use()
        draw_func()

    def resize(self, width, height):
        pass


class RenderStage:
    def draw(self, out_fbo, data) -> int:
        pass

    def on_created_uniformed(self, uniformed):
        pass


# base renderer instances should not be used
class BaseRenderer(RenderStage):
    """
    Has program and can render to out_fbo in got via args
    """
    signature = {'in': (), 'out': ()}
    load_params = {}  # e.g. {'diffuse': {'anisotropic_filtering': 16, 'gamma_corr': True}}
    shader_prog: ShaderProgram

    def draw(self, out_fbo, data) -> int:
        out_fbo.use()
        out_fbo.clear()
        self.shader_prog.use()
        i = 0
        for i, elem in enumerate(data):
            elem.draw()
        return i

    def resize(self, width, height):
        pass


# difference from BaseRenderer: controls output framebuffer
class SecondPassRenderer(BaseRenderer):
    # todo remove this article
    """
    Previous stage has drawn into this renderer FBO and this renderer draws to fbo of next stage.
    //Warning: when you override this class don't forget that current function clears this renderer
    // FBO, so it can decrease speed, may be you would like to call BaseRenderer.draw(self, data, out_fbo)

    `data` argument can be easily replaced with `self.meshes`, but due to compatibility issues
     function accepts 2 arguments
    """

    fbo: FrameBuffer
    meshes: Iterable[RenderCompound]

    # todo second pass renderers should have draw() without `data` parameter (it will be automatically `self.meshes`)

    def resize(self, width, height):
        self.fbo.resize(width, height)
