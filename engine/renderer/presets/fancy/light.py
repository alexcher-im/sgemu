from ....gl.shader import ShaderProgram
from ....gl.framebuffer import FrameBuffer, FB_NONE
from ....model.model import RenderCompound, Material
from ...base import SecondPassRenderer
from ...util import gen_screen_mesh
from ..deferred import GBuffer4Float, GBuffer3Int, GBuffer3Float16, GBuffer3UInt


class LightPass(SecondPassRenderer):
    # language=GLSL
    _vert_shader = '''\
#version 430 core

layout (location = 0) in vec2 a_pos;
layout (location = 1) in vec2 a_uv;

out vec2 uv;

void main() {
    gl_Position = vec4(a_pos, 0, 1);
    uv = a_uv;
}
'''

    # language=GLSL
    _frag_shader = '''\
#version 430 core

in vec2 uv;

uniform sampler2D pos_shin_map;
uniform sampler2D normal_map;
uniform sampler2D albedo;

out vec4 out_color;

#define pi 3.1415926

struct Light {  // size: 64 bytes
    vec3 diffuse_color;
    float linear;
    vec3 specular_color;
    float quadratic;

    vec3 pos;
    float cut_off;  // angle cosine

    vec3 direction;
    float outer_cut_off;  // angle cosine
};

struct CommonLight {  // size: 16 bytes
    vec3 ambient_color;
};

struct Fog {  // size: 32 bytes
    vec3 color;
    float start;
    float z_far;
};

vec3 frag_pos;
vec3 normal;

uniform CommonLight comm_light;
uniform Fog fog;
uniform vec3 camera_pos;

layout(std140, binding = 0) buffer SpotLightStorage
{
    int count;
    Light some_light[];
} ssbo_data;


float sigmoid(float x) {
    return (cos((x - 1) * pi) + 1) / 2;
}


float calcFogIntensity() {
    // linear intensity
    float x = 1 - clamp((length(frag_pos - camera_pos) - fog.z_far) / (fog.start - fog.z_far), 0, 1);
    // sigmoid intensity
    return sigmoid(x);
}

float spotlight_interp(float x) {
    float lin_part = (x * 1.52753) - 0.527525;
    float quad_part = 1 - sqrt(1 - pow(x / sqrt(2), 2.0));
    if (x <= 1)
        return quad_part / 0.2928932188134524755991556378951509607151640623115259634116601310;
    else 
        return lin_part;
    //return mix(lin_part, quad_part, (x >= 0.4));
}


void main() {
    // gathering info from textures
    vec4 _sampled_pos_shin = texture(pos_shin_map, uv);
    vec4 _sampled_normal = texture(normal_map, uv);
    vec4 _sampled_albedo = texture(albedo, uv);

    frag_pos = _sampled_pos_shin.xyz;
    float shininess = _sampled_pos_shin.w;
    normal = _sampled_normal.xyz;
    vec4 texel = _sampled_albedo;
    float specular_cf = texel.w;

    // common values
    vec3 view_dir = normalize(camera_pos - frag_pos);

    // rendering ambient lightning
    vec3 ambient = texel.xyz * comm_light.ambient_color;

    vec3 result = ambient;
    for (int i = 0; i < ssbo_data.count; ++i) {
        Light light = ssbo_data.some_light[i];

        vec3 curr_color;
        vec3 light_dir = normalize(light.pos - frag_pos);
        vec3 halfway_light = normalize(light_dir + view_dir);
        // calculating brightness
        float frag_distance = length(light.pos - frag_pos);
        float brightness = 1 / (1 + light.linear * frag_distance + light.quadratic * pow(frag_distance, 2));
        //if (brightness < 1./255) continue;

        // for spotlight
        float theta = dot(light_dir, -light.direction);
        float eps = (light.cut_off - light.outer_cut_off) / 0.7310585786300048792511592418218362743651446401650565192763659079;
        float intensity = spotlight_interp(1 / (1 + exp(-(theta - light.outer_cut_off) / eps + 1)));
        intensity = clamp(intensity, 0, 1);
        //if (intensity <= 0.0) continue;

        // diffuse
        float diffuse_power = max(dot(light_dir, normal), 0);
        vec3 diffuse = diffuse_power * texel.xyz * light.diffuse_color;

        // specular
        float spec_power = pow(max(dot(halfway_light, normal), 0.0), 32);
        vec3 specular = spec_power * light.specular_color * specular_cf;
        specular = mix(specular, specular * texel.xyz, 0.95);  // TODO: replace 0.95 with material.specular_corellation

        curr_color = diffuse + specular;
        curr_color *= brightness * intensity;
        result += curr_color;
    }

    // fog
    result = mix(result, fog.color, calcFogIntensity());

    out_color = vec4(result, 1);
}
'''

    _buffers_ldr = (GBuffer4Float,  # positions + shininess
                    GBuffer3Int,    # normals
                    GBuffer3UInt)   # diffuse + specular
    _buffers_hdr = (GBuffer4Float,    # positions + shininess
                    GBuffer3Float16,  # normals
                    GBuffer3Float16)  # diffuse + specular
    signature = {'in': ('pos_shin vec4', 'normal vec3', 'albedo vec3'), 'out': ('color vec3')}

    def __init__(self, width, height, hdr_gbuffer=False):
        super(LightPass, self).__init__()

        self.fbo = FrameBuffer(width, height, (self._buffers_ldr, self._buffers_hdr)[hdr_gbuffer], FB_NONE)

        self._make_shader()
        self.meshes = ()  # will be set in on_created_uniformed()

    def on_created_uniformed(self, uniformed):
        arr_data = [(buf, uniformed.sampler_data[name].bind_index)
                    for buf, name in zip(self.fbo.color_buffers, ('pos_shin', 'normal', 'albedo'))]
        self.meshes = (RenderCompound(gen_screen_mesh(), Material(arr_data)), )

    def _make_shader(self):
        self.shader_prog = ShaderProgram(self._vert_shader, self._frag_shader, use=True)

    def draw(self, out_fbo, data):
        super(LightPass, self).draw(out_fbo, data)
        #self.fbo.clear()
