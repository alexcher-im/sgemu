# do a bloom, god rays, lens flares effects here
from .coloring import EffectSupporter
from .convolution import GaussianBlur
from ...base import SecondPassRenderer, BaseRenderer
from ...uniformed import UniformedRenderer
from ...util import sample_vertex_shader, gen_screen_mesh
from ....gl.shader import ShaderProgram
from ....gl.framebuffer import FrameBuffer, FB_NONE
from ....model.model import RenderCompound, Material


class LightExtractorRenderer(SecondPassRenderer):
    _vert_shader = sample_vertex_shader
    # language=GLSL
    _frag_shader = '''\
#version 430 core
in vec2 tex_coords;

out vec4 out_color;

uniform sampler2D tex_img;
uniform float limit;

void main() {
    vec4 curr_texel = texture(tex_img, tex_coords);
    if (dot(curr_texel.xyz, vec3(1)) > limit) out_color = max(curr_texel - limit, vec4(0));
    else out_color = vec4(vec3(0), 1); 
}
'''

    def __init__(self, width, height, color_buffer_type=1):
        self.fbo = FrameBuffer(width, height, color_buffer_type, FB_NONE)
        self.shader_prog = ShaderProgram(self._vert_shader, self._frag_shader, use=True)
        self.meshes = (RenderCompound(gen_screen_mesh(), Material(self.fbo.color_buffers)), )
        self.brightness_limit_setter = self.shader_prog.get_uniform_setter('limit', '1f')
        self.brightness_limit_setter(1)

    draw = BaseRenderer.draw


class LightMergerRenderer(EffectSupporter):
    _vert_shader = sample_vertex_shader
    # language=GLSL
    _frag_shader = '''\
#version 430 core
in vec2 tex_coords;

out vec4 out_color;

uniform sampler2D raw_img;
uniform sampler2D blurred_img;
uniform float bloom_brightness;
/* uniforms */

void main() {
    out_color = texture(raw_img, tex_coords) + texture(blurred_img, tex_coords) * bloom_brightness;
    /* main */ 
}
'''
    _frag_out_color_name = 'out_color'

    def __init__(self, width, height, src_col_buffer, color_buffer_type=1, custom_effects=()):
        super(LightMergerRenderer, self).__init__(custom_effects)
        self.fbo = FrameBuffer(width, height, color_buffer_type, FB_NONE)

        uniformed = UniformedRenderer(self)
        self.meshes = (RenderCompound(gen_screen_mesh(),
                                      Material(((src_col_buffer, uniformed.sampler_data['raw_img'].bind_index),
                                                (self.fbo.color_buffers[0],
                                                 uniformed.sampler_data['blurred_img'].bind_index)))
                                      ), )
        del uniformed

        brightness = self.shader_prog.get_uniform_setter('bloom_brightness', '1f')
        brightness(0.2)
        self.effect_value_setters['brightness'] = brightness

    draw = BaseRenderer.draw


class Bloom(SecondPassRenderer):
    def __init__(self, width, height, color_buffer_type=1, additional_post_effects=(), blur_points=51, num_passes=1,
                 mix_cf=0.1, light_limit=1):
        super(Bloom, self).__init__()

        self.extract_pass = LightExtractorRenderer(width, height, color_buffer_type)
        self.blur_pass = GaussianBlur(width, height, blur_points, color_buffer_type)
        self.merge_pass = LightMergerRenderer(width, height, self.extract_pass.fbo.color_buffers[0], color_buffer_type,
                                              additional_post_effects)

        self.merge_pass.shader_prog.use()
        self.merge_pass.set_effect_value('brightness', mix_cf)
        self.extract_pass.shader_prog.use()
        self.extract_pass.brightness_limit_setter(light_limit)

        self.meshes = self.extract_pass.meshes
        self.fbo = self.extract_pass.fbo

        self.num_additional_passes = num_passes - 1

    def draw(self, out_fbo, data):
        self.extract_pass.draw(self.blur_pass.fbo, data)
        for _ in range(self.num_additional_passes):
            self.blur_pass.draw(self.blur_pass.fbo, self.blur_pass.meshes)
        self.blur_pass.draw(self.merge_pass.fbo, self.blur_pass.meshes)
        self.merge_pass.draw(out_fbo, self.merge_pass.meshes)
