from .first import GeometryPassBase, GeometryPassDefault


class NormalMapping(GeometryPassBase):
    # language=GLSL
    _vert_shader = '''\
#version 430 core

layout (location = 0) in vec3 pos_a;
layout (location = 1) in vec3 normal_a;
layout (location = 2) in vec2 uv_coord_a;
layout (location = 3) in vec3 tangent;
layout (location = 4) in vec3 bitangent;

out vec3 pos;
out vec3 normal;
out vec2 uv;
out mat3 TBN;

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
    TBN = mat3(normalize(tangent), -normalize(bitangent), normalize(normal));
}
'''
    # language=GLSL
    _frag_shader = '''\
#version 430 core

in vec3 pos;
in vec3 normal;
in vec2 uv;
in mat3 TBN;

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
uniform sampler2D normal_map;

void main() {
    o_frag_pos_shin.xyz = pos;
    o_frag_pos_shin.w = 1;
    o_normal.xyz = normalize(TBN * normalize(texture(normal_map, uv).xyz * 2 - 1));
    //o_normal.xyz = vec3(0, 0, 1) * TBN;
    o_sampled_albedo.xyz = texture(material.diffuse_map, uv).rgb;
}
'''
    load_params = dict(GeometryPassDefault.load_params, **{'normal': {'gamma_corr': False, 'anisotropic_levels': 0,
                                                                      'interpolation': 'mipmap', 'mipmap': True}})
