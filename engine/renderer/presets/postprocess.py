from ...gl.shader import ShaderProgram
from ...gl.framebuffer import FrameBuffer, FB_NONE, ColorTextureBuffer, ColorFloatTextureBuffer
from ...lib.pathlib import get_rel_path
from ...model.model import RenderCompound, Material
from ..base import BaseRenderer
from ..util import gen_screen_mesh


class RawPostProcess(BaseRenderer):
    def __init__(self, width, height, out_fbo=None, shader_program: ShaderProgram=None,
                 color_buffer='int'):
        super(RawPostProcess, self).__init__(out_fbo)
        color_buffer = {'int': ColorTextureBuffer, 'float': ColorFloatTextureBuffer}[color_buffer]
        self.fbo = FrameBuffer(width, height, [color_buffer], FB_NONE, FB_NONE, (0, ))
        self.shader_prog = shader_program
        if shader_program is None:
            vsh_path = get_rel_path(__file__, '..', '..', 'shaders', 'postproc.vsh.glsl')
            fsh_path = get_rel_path(__file__, '..', '..', 'shaders', 'postproc.fsh.glsl')
            self.shader_prog = ShaderProgram.from_files(vsh_path, fsh_path)
        self.screen_mesh = RenderCompound(gen_screen_mesh(), Material(self.fbo.color_buffers))

    def resize(self, width, height):
        self.fbo.resize(width, height)
