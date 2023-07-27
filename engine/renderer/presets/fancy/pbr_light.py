from OpenGL.GL import GL_RGBA, GL_FLOAT, GL_RGBA32F

from engine.gl import FrameBuffer, ShaderProgram, Texture2D
from engine.gl.framebuffer import FB_NONE
from engine.lib.pathlib import get_rel_path
from engine.model.model import RenderCompound, Material
from engine.renderer.base import SecondPassRenderer
from engine.renderer.presets.deferred import GBuffer4Float, GBuffer3Int, GBuffer3UInt, GBuffer3Float16
from engine.renderer.util import gen_screen_mesh


class PbrLightPass(SecondPassRenderer):
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

out vec4 FragColor;


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


struct AreaLight { // size: 80 bytes
    vec3 color;
    float intensity;
    vec3 points[4];
    //int twoSided;
};

struct CommonLight {  // size: 16 bytes
    vec3 ambient_color;
};


uniform sampler2D pos_shin_map;
uniform sampler2D normal_map;
uniform sampler2D albedo_map;

uniform float metallic;
uniform float roughness;
uniform float ao;

uniform CommonLight comm_light;
uniform vec3 camera_pos;

layout(std140, binding = 0) buffer SpotLightStorage {
    int count;
    Light lights[];
} light_data;

layout (std140, binding = 1) buffer AreaLightStorage {
    int count;
    AreaLight lights[];
} area_lights;


const float PI = 3.14159265359;

const float LUT_SIZE  = 64.0; // ltc_texture size
const float LUT_SCALE = (LUT_SIZE - 1.0)/LUT_SIZE;
const float LUT_BIAS  = 0.5/LUT_SIZE;

uniform sampler2D LTC1; // for inverse M
uniform sampler2D LTC2; // GGX norm, fresnel, 0(unused), sphere


vec3 fresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(max(1.0 - cosTheta, 0.0), 5.0);
}

float DistributionGGX(vec3 N, vec3 H, float roughness) {
    float a      = roughness*roughness;
    float a2     = a*a;
    float NdotH  = max(dot(N, H), 0.0);
    float NdotH2 = NdotH*NdotH;

    float num   = a2;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;

    return num / denom;
}

float GeometrySchlickGGX(float NdotV, float roughness) {
    float r = (roughness + 1.0);
    float k = (r*r) / 8.0;

    float num   = NdotV;
    float denom = NdotV * (1.0 - k) + k;

    return num / denom;
}

float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx2  = GeometrySchlickGGX(NdotV, roughness);
    float ggx1  = GeometrySchlickGGX(NdotL, roughness);

    return ggx1 * ggx2;
}

float spotlight_interp(float x) {
    float lin_part = (x * 1.52753) - 0.527525;
    float quad_part = 1 - sqrt(1. - pow(x / sqrt(2.), 2.0));
    if (x <= 1)
        return quad_part / 0.2928932188134524755991556378951509607151640623115259634116601310;
    else 
        return lin_part;
}

// Vector form without project to the plane (dot with the normal)
// Use for proxy sphere clipping
vec3 IntegrateEdgeVec(vec3 v1, vec3 v2) {
    // Using built-in acos() function will result flaws
    // Using fitting result for calculating acos()
    float x = dot(v1, v2);
    float y = abs(x);

    float a = 0.8543985 + (0.4965155 + 0.0145206*y)*y;
    float b = 3.4175940 + (4.1616724 + y)*y;
    float v = a / b;

    float theta_sintheta = (x > 0.0) ? v : 0.5*inversesqrt(max(1.0 - x*x, 1e-7)) - v;

    return cross(v1, v2)*theta_sintheta;
}

// P is fragPos in world space (LTC distribution)
vec3 LTC_Evaluate(vec3 N, vec3 V, vec3 P, mat3 Minv, vec3 points[4], bool twoSided) {
    // construct orthonormal basis around N
    vec3 T1, T2;
    T1 = normalize(V - N * dot(V, N));
    T2 = cross(N, T1);

    // rotate area light in (T1, T2, N) basis
    Minv = Minv * transpose(mat3(T1, T2, N));
	//Minv = Minv * transpose(mat3(N, T2, T1));

    // polygon (allocate 4 vertices for clipping)
    vec3 L[4];
    // transform polygon from LTC back to origin Do (cosine weighted)
    L[0] = Minv * (points[0] - P);
    L[1] = Minv * (points[1] - P);
    L[2] = Minv * (points[2] - P);
    L[3] = Minv * (points[3] - P);

    // use tabulated horizon-clipped sphere
    // check if the shading point is behind the light
    vec3 dir = points[0] - P; // LTC space
    vec3 lightNormal = cross(points[1] - points[0], points[3] - points[0]);
    bool behind = (dot(dir, lightNormal) < 0.0);

    // cos weighted space
    L[0] = normalize(L[0]);
    L[1] = normalize(L[1]);
    L[2] = normalize(L[2]);
    L[3] = normalize(L[3]);

	// integrate
    vec3 vsum = vec3(0.0);
    vsum += IntegrateEdgeVec(L[0], L[1]);
    vsum += IntegrateEdgeVec(L[1], L[2]);
    vsum += IntegrateEdgeVec(L[2], L[3]);
    vsum += IntegrateEdgeVec(L[3], L[0]);

    // form factor of the polygon in direction vsum
    float len = max(0.00, length(vsum));

    float z = vsum.z/len;
    if (behind)
        z = -z;

    vec2 uv = vec2(z*0.5f + 0.5f, len); // range [0, 1]
    uv = uv*LUT_SCALE + LUT_BIAS;

    // Fetch the form factor for horizon clipping
    float scale = texture(LTC2, uv).w;

    float sum = len*scale;
    if (!behind && !twoSided)
        sum = 0.0;

    // Outgoing radiance (solid angle) for the entire polygon
    vec3 Lo_i = vec3(sum, sum, sum);
    return Lo_i;
}

void main() {
    //vec2 TexCoords;
    vec3 WorldPos;
    vec3 Normal;

    WorldPos = texture(pos_shin_map, uv).xyz;
    Normal = texture(normal_map, uv).xyz;
    vec3 albedo = texture(albedo_map, uv).xyz;

    vec3 N = normalize(Normal); 
    vec3 V = normalize(camera_pos - WorldPos);

    vec3 F0 = vec3(0.04); 
    F0 = mix(F0, albedo, metallic);

    // reflectance equation
    vec3 Lo = vec3(0.0);
    for(int i = 0; i < light_data.count; ++i) {
        Light light = light_data.lights[i];
        
        // calculate per-light radiance
        vec3 L = normalize(light.pos - WorldPos);
        vec3 H = normalize(V + L);
        float distance    = length(light.pos - WorldPos);
        float attenuation = 1.0 / (distance * distance);
        vec3 radiance     = light.diffuse_color * attenuation * 100000;
        
        // spot-light attenuation
        float theta = dot(L, -light.direction);
        float eps = (light.cut_off - light.outer_cut_off) / 0.7310585786300048792511592418218362743651446401650565192763659079;
        float spotlight_int = spotlight_interp(1 / (1 + exp(-(theta - light.outer_cut_off) / eps + 1)));
        spotlight_int = clamp(spotlight_int, 0., 1.);

        // Cook-Torrance BRDF
        float NDF = DistributionGGX(N, H, roughness);
        float G   = GeometrySmith(N, V, L, roughness);
        vec3 F    = fresnelSchlick(max(dot(H, V), 0.0), F0);

        vec3 kS = F;
        vec3 kD = vec3(1.0) - kS;
        kD *= 1.0 - metallic;

        vec3 numerator    = NDF * G * F;
        float denominator = 4.0 * max(dot(N, V), 0.0) * max(dot(N, L), 0.0);
        vec3 specular     = numerator / max(denominator, 0.001);

        // add to outgoing radiance Lo
        float NdotL = max(dot(N, L), 0.0);
        Lo += (kD * albedo / PI + specular) * spotlight_int * radiance * NdotL;
    }
    
    // area lights
    
	float dotNV = clamp(dot(N, V), 0.0f, 1.0f);
    
    // use roughness and sqrt(1-cos_theta) to sample M_texture
    vec2 area_uv = vec2(roughness, sqrt(1.0f - dotNV));
    area_uv = area_uv*LUT_SCALE + LUT_BIAS;
    
    // get 4 parameters for inverse_M
    vec4 t1 = texture(LTC1, area_uv);

    // Get 2 parameters for Fresnel calculation
    vec4 t2 = texture(LTC2, area_uv);
    
    mat3 Minv = mat3(
        vec3(t1.x, 0, t1.y),
        vec3(  0,  1,    0),
        vec3(t1.z, 0, t1.w)
    );
    
    vec3 mSpecular = pow(vec3(0.23f, 0.23f, 0.23f), vec3(2.2)); // mDiffuse
    
    for (int i = 0; i < area_lights.count; ++i) {
        AreaLight light = area_lights.lights[i];
    
        // Evaluate LTC shading
        bool twoSided = true; // light.twoSided
		vec3 diffuse = LTC_Evaluate(N, V, WorldPos, mat3(1), light.points, twoSided);
		vec3 specular = LTC_Evaluate(N, V, WorldPos, Minv, light.points, twoSided);

		// GGX BRDF shadowing and Fresnel
		// t2.x: shadowedF90 (F90 normally it should be 1.0)
		// t2.y: Smith function for Geometric Attenuation Term, it is dot(V or L, H).
		specular *= mSpecular*t2.x + (1.0f - mSpecular) * t2.y;

		// Add contribution
		Lo += light.color * light.intensity * (specular + albedo * diffuse);
    }

    // finish

    vec3 ambient = comm_light.ambient_color * albedo * ao;
    vec3 color = ambient + Lo;

    FragColor = vec4(color, 1.0);
}
'''

    _buffers_ldr = (GBuffer4Float,  # positions + shininess
                    GBuffer3Int,    # normals
                    GBuffer3UInt)   # diffuse + specular
    _buffers_hdr = (GBuffer4Float,    # positions + shininess
                    GBuffer3Float16,  # normals
                    GBuffer3Float16)  # diffuse + specular
    signature = {'in': ('pos_shin vec4', 'normal vec3', 'albedo vec3'), 'out': ('color vec3')}

    def __init__(self, width, height, hdr_gbuffer=True):
        super(PbrLightPass, self).__init__()

        self.fbo = FrameBuffer(width, height, (self._buffers_ldr, self._buffers_hdr)[hdr_gbuffer], FB_NONE)

        self._make_shader()
        self.meshes = ()  # will be set in on_created_uniformed()

    def on_created_uniformed(self, uniformed):
        arr_data = [(buf, uniformed.sampler_data[name].bind_index)
                    for buf, name in zip(self.fbo.color_buffers, ('pos_shin', 'normal', 'albedo'))]

        ltc1_tex = Texture2D.tex_from_binary_file(get_rel_path(__file__, 'area_light_ltc1.bin'), 64, 64, GL_RGBA,
                                                  data_type=GL_FLOAT, border='edge', interpolation='mipmap',
                                                  mipmap=True, tex_data_type=GL_RGBA32F)
        ltc2_tex = Texture2D.tex_from_binary_file(get_rel_path(__file__, 'area_light_ltc2.bin'), 64, 64, GL_RGBA,
                                                  data_type=GL_FLOAT, border='edge', interpolation='mipmap',
                                                  mipmap=True, tex_data_type=GL_RGBA32F)
        arr_data.append((ltc1_tex, uniformed.sampler_data['LTC1'].bind_index))
        arr_data.append((ltc2_tex, uniformed.sampler_data['LTC2'].bind_index))

        self.meshes = (RenderCompound(gen_screen_mesh(), Material(arr_data)), )

    def _make_shader(self):
        self.shader_prog = ShaderProgram(self._vert_shader, self._frag_shader, use=True)

    def draw(self, out_fbo, data):
        super(PbrLightPass, self).draw(out_fbo, data)
