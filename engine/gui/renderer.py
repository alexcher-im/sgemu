from glm import vec2

from ..gl.framebuffer import FrameBuffer
from ..gl.mesh import VAOMesh
from ..gl.shader import ShaderProgram
from .base import RootElement


class UIRenderer:
    # language=GLSL
    _vert_shader = '''\
#version 430 core

in vec2 i_pos;
in vec2 i_uv;

out vec2 uv;

uniform vec2 norm_pos;
uniform vec2 norm_size;

void main() {
    vec2 pos = i_pos * norm_size + norm_pos;
    pos *= 2;
    pos = vec2(pos.x - 1, -pos.y + 1);
    gl_Position = vec4(pos, 1, 1);
    uv = i_uv;
}
'''
    # language=GLSL
    _frag_shader = '''\
#version 430 core

in vec2 uv;

uniform sampler2D tex;
uniform vec4 color_mult;

out vec4 color;

void main() {
    color = texture(tex, uv) * color_mult;
}
'''

    def __init__(self, framebuffer: FrameBuffer):
        self.root = RootElement((framebuffer.width, framebuffer.height))
        self.fbo = framebuffer
        self.mesh = VAOMesh([0, 0, 0, 1,
                             0, 1, 0, 0,
                             1, 1, 1, 0,
                             1, 0, 1, 1],
                            [0, 1, 2, 2, 3, 0], (2, 2))
        self.shader = ShaderProgram(self._vert_shader, self._frag_shader, use=True)
        self.pos_setter = self.shader.get_uniform_setter('norm_pos', '2f')
        self.size_setter = self.shader.get_uniform_setter('norm_size', '2f')
        self.color_setter = self.shader.get_uniform_setter('color_mult', '4f')

    def draw(self):
        self.fbo.use()
        self.shader.use()
        for elem in self.root.get_active_nodes():
            if not elem:
                continue
            norm_size = vec2(elem.size) / self.root.size
            norm_pos = vec2(elem.metrics.abs_pos) / self.root.size
            self.pos_setter(*norm_pos)
            self.size_setter(*norm_size)
            self.color_setter(*elem.render_data.color)
            elem.render_data.opengl_texture.use()

            elem.render_data.mesh.draw()
