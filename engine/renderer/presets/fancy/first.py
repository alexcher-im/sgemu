from OpenGL.GL import GL_DEPTH_TEST, GL_CULL_FACE, glEnable, glDisable

from ....gl import ShaderProgram
from ...base import BaseRenderer


class GeometryPassBase(BaseRenderer):
    _vert_shader = 'example that causes compilation error'
    _frag_shader = 'example that causes compilation error'
    _effects_to_enable = (GL_DEPTH_TEST, GL_CULL_FACE)

    def __init__(self):
        self._make_shader()

    def _make_shader(self):
        self.shader_prog = ShaderProgram(self._vert_shader, self._frag_shader, use=True)

    def draw(self, out_fbo, data) -> int:
        for effect in self._effects_to_enable:
            glEnable(effect)
        result = super(GeometryPassBase, self).draw(out_fbo, data)
        for effect in self._effects_to_enable:
            glDisable(effect)
        return result


class GeometryPassDefault(GeometryPassBase):
    # language=GLSL
    _vert_shader = '''\
#version 430 core

layout (location = 0) in vec3 pos_a;
layout (location = 1) in vec3 normal_a;
layout (location = 2) in vec2 uv_coord_a;

out vec3 pos;
out vec3 normal;
out vec2 uv;

layout (std140, binding = 0) uniform MVPMatrices {
    mat4 model;
    mat4 view;
    mat4 projection;
    mat4 view_projection;
    mat4 model_view_projection;
};

void main() {
    gl_Position = model_view_projection * vec4(pos_a.xyz, 1.0);

    pos = (model * vec4(pos_a, 1)).xyz;
    normal = normal_a * transpose(inverse(mat3(model)));
    uv = uv_coord_a;
}
'''
    # language=GLSL
    _frag_shader = '''\
#version 430 core

in vec3 pos;
in vec3 normal;
in vec2 uv;

layout (location = 0) out vec4 o_frag_pos_shin;
layout (location = 1) out vec3 o_normal;
layout (location = 2) out vec3 o_sampled_albedo;

struct Material {  // size: 16 bytes
    float shininess;
    float specular_correlation;
    sampler2D diffuse_map;
    sampler2D specular_map;
};

layout (location = 2) uniform Material material;

void main() {
    o_frag_pos_shin.xyz = pos;
    o_frag_pos_shin.w = 1;
    o_normal.xyz = normal;
    o_sampled_albedo.xyz = texture(material.diffuse_map, uv).rgb;
}
'''
    load_params = {'diffuse': {'anisotropic_levels': 16, 'gamma_corr': True, 'mipmap': True, 'interpolation': 'mipmap'}}
    signature = {'in': ('pos vec3', 'normal vec3', 'uv vec2'), 'out': ('pos_shin vec4', 'normal vec3', 'albedo vec3')}
