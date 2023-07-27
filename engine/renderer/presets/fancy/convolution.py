import numpy as np
from PIL import Image
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
    //out_color.xyz = pow(out_color.xyz, vec3(1));
    //out_color = abs(out_color);
}'''
injectable_code = 'out_color.xyz += texture(tex_img, tex_coords + direction * {dir_offset}).xyz * {distr_value};\n'


# language=GLSL
dof_frag_shader = '''\
#version 430 core

in vec2 tex_coords;

out vec4 out_color;

layout (binding = 0) uniform sampler2D tex_img;
layout (binding = 1) uniform sampler2D depth_source;
uniform float near_z_cut;

float lin_depth(float z) {
    z = z * 2 - 1;
    float zNear = 0.1;
    float zFar = 10000;
    float z_e = 2.0 * zNear * zFar / (zFar + zNear - z * (zFar - zNear)) / (zFar - zNear);
    return z_e;
}

float read_depth(vec2 uv) {
    return lin_depth(texture(depth_source, uv).x);
}

void main() {
    float z = read_depth(tex_coords);
    out_color = vec4(0);
    float radius = sqrt(sqrt(sqrt(z)));
    float dist_sum = 0;
    float z_limit = near_z_cut;
    if (z > z_limit) {
        {000;}
        out_color.xyz /= dist_sum;
    }
    else
        out_color.xyz += texture(tex_img, tex_coords).xyz;
    //out_color.xyz = pow(out_color.xyz, vec3(1));
    //out_color = abs(out_color);
}'''
dof_injectable_code = '' \
    'if (read_depth(tex_coords + vec2({coord_offset}) * vec2({window_size}) * radius) > z_limit || vec2({coord_offset}) == vec2(0)) {{' \
        'out_color.xyz += texture(tex_img, tex_coords + vec2({coord_offset}) * vec2({window_size}) * radius).xyz * {distr_value}; ' \
        'dist_sum += {distr_value}; ' \
    '}}\n'


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
        #print('shader', frag_shader.replace('{000;}', inj_code))
        self.shader_prog = ShaderProgram(vert_shader, frag_shader.replace('{000;}', inj_code))

    def draw(self, out_fbo, data):
        self.first.draw(self.second.fbo, data)
        self.second.draw(out_fbo, self.second.meshes)

    def set_radius(self, value):
        self.radius = value
        self.first.direction = vec2(1, 0) / self.first.fbo.width * value
        self.second.direction = vec2(0, 1) / self.second.fbo.height * value


# todo make a basic class BasicConvolutionRenderer, that will be able to convolve image by another 2D image
class DepthOfFieldRenderer(SecondPassRenderer):
    def __init__(self, distribution, width, height, depth_buffer, color_buffer_type=1):
        if isinstance(distribution, str):
            distribution = self._read_bitmap(distribution)
        distribution /= distribution.sum()

        self.fbo = FrameBuffer(width, height, color_buffer_type, FB_NONE)
        self.meshes = (RenderCompound(gen_screen_mesh(), Material(self.fbo.color_buffers + [(depth_buffer, 1)])), )
        self._make_shader(distribution)

        self.near_cut = 0.002
        self.near_cut_setter = self.shader_prog.get_uniform_setter('near_z_cut', '1f')
        self.set_near_cut(self.near_cut)

    def set_near_cut(self, near_cut):
        self.near_cut = near_cut
        self.shader_prog.use()
        self.near_cut_setter(near_cut)

    def _make_shader(self, distribution):
        half_x_len = len(distribution) // 2
        half_y_len = len(distribution[0]) // 2
        inj_code = ''.join(dof_injectable_code.format(
            distr_value=val,
            coord_offset='%d, %d' % (row_offset, col_offset),
            window_size='%f, %f' % (1/self.fbo.width, 1/self.fbo.height))
                           for row, row_offset in zip(distribution, range(-half_x_len, half_x_len + 1))
                           for val, col_offset in zip(row, range(-half_y_len, half_y_len + 1))
                           )
        #print('shader', dof_frag_shader.replace('{000;}', inj_code))
        self.shader_prog = ShaderProgram(vert_shader, dof_frag_shader.replace('{000;}', inj_code))

    def _read_bitmap(self, filename):
        return np.array(Image.open(filename))[:, :, 0].astype('float32') / 255


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
