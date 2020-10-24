import numpy as np
from glm import vec2

from ....model.model import Material, RenderCompound
from ....gl.framebuffer import FrameBuffer, FB_NONE
from ....gl.shader import ShaderProgram
from ...base import SecondPassRenderer
from ...util import sample_vertex_shader, gen_screen_mesh

# Separable convolution
vert_shader = sample_vertex_shader
# language=GLSL
frag_shader = '''\
#version 430 core

in vec2 tex_coords;

out vec4 out_color;

uniform sampler2D tex_img;
uniform vec2 direction;

void main() {
    out_color = vec4(0);
    {000;}
}'''
injectable_code = 'out_color.xyz += texture(tex_img, tex_coords + direction * {dir_offset}).xyz * {distr_value};\n'


class SeparableConvolutionSession(SecondPassRenderer):
    def __init__(self, distribution, width, height, color_buffer_type=1):
        self.radius = 1
        self._make_shader(distribution)
        self.first = SeparableConvolutionPass(width, height, self.shader_prog, color_buffer_type, vec2(1, 0) / width)
        self.second = SeparableConvolutionPass(width, height, self.shader_prog, color_buffer_type, vec2(0, 1) / height)

        self.meshes = self.first.meshes
        self.fbo = self.first.fbo

    def _make_shader(self, distr_values):
        start_value = len(distr_values) // 2
        inj_code = ''.join((injectable_code.format(dir_offset=offset, distr_value=value)
                            for value, offset in zip(distr_values, range(-start_value, start_value + 1))))
        print('shader', frag_shader.replace('{000;}', inj_code))
        self.shader_prog = ShaderProgram(vert_shader, frag_shader.replace('{000;}', inj_code))

    def draw(self, out_fbo, data):
        self.first.draw(self.second.fbo, data)
        self.second.draw(out_fbo, self.second.meshes)

    def set_radius(self, value):
        self.radius = value
        self.first.direction = vec2(1, 0) / self.first.fbo.width * value
        self.second.direction = vec2(0, 1) / self.second.fbo.height * value


class SeparableConvolutionPass(SecondPassRenderer):
    def __init__(self, width, height, program, color_buffer_type, direction):
        self.shader_prog = program
        self.fbo = FrameBuffer(width, height, color_buffer_type, FB_NONE)
        self.meshes = (RenderCompound(gen_screen_mesh(), Material(self.fbo.color_buffers)), )
        self.direction_setter = self.shader_prog.get_uniform_setter('direction', '2f')
        self.direction = direction

    def draw(self, out_fbo, data) -> int:
        out_fbo.use()
        self.shader_prog.use()
        self.direction_setter(*self.direction)
        i = 0
        for i, elem in enumerate(data):
            elem.draw()
        return i


class GaussianBlur(SeparableConvolutionSession):
    def __init__(self, width, height, values, color_buffer_type=1):
        self.values = np.blackman(values)
        self.values /= self.values.sum()
        super(GaussianBlur, self).__init__(self.values, width, height, color_buffer_type)


class BoxBlur(SeparableConvolutionSession):
    def __init__(self, width, height, values, color_buffer_type=1):
        self.values = np.full(values, 1.0)
        self.values /= self.values.sum()
        super(BoxBlur, self).__init__(self.values, width, height, color_buffer_type)
