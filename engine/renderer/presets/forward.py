from ...gl.framebuffer import StaticFrameBuffer
from ...gl.shader import ShaderProgram
from ...lib.pathlib import get_rel_path
from ..base import FirstPassRenderer


class RawForwardRenderer(FirstPassRenderer):
    def __init__(self, out_fbo=StaticFrameBuffer, shader_prog: ShaderProgram=None):
        super(RawForwardRenderer, self).__init__(out_fbo)
        self.shader_prog = shader_prog
        if shader_prog is None:
            vsh_path = get_rel_path(__file__, '..', '..', 'shaders', 'texture_square.vsh.glsl')
            fsh_path = get_rel_path(__file__, '..', '..', 'shaders', 'texture_square.fsh.glsl')
            self.shader_prog = ShaderProgram.from_files(vsh_path, fsh_path)
