from ....gl import FrameBuffer, ShaderProgram
from ....gl.framebuffer import FB_NONE
from ....model.model import Material, RenderCompound
from ...base import SecondPassRenderer
from ...util import gen_screen_mesh, sample_vertex_shader


class LightVolumeRenderer(SecondPassRenderer):
    # language=GLSL
    _fragment_shader = '''\
#version 430 core

in vec2 tex_coords;

out vec4 out_color;

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

layout(std140, binding = 0) buffer SpotLightStorage
{
    int count;
    Light some_light[];
} ssbo_data;

layout (binding = 0) uniform sampler2D tex_img;
layout (binding = 1) uniform sampler2D pos_buffer;

uniform vec3 camera_pos;

struct Ray {
    vec3 o;		// origin
    vec3 d;		// direction
};

struct Cone {
    float cosa;	// half cone angle
    vec3 c;		// tip position
    vec3 v;		// axis
};

const float noHit = 1e10;

float intersectCone(Cone s, Ray r) {
    vec3 co = r.o - s.c;

    float a = dot(r.d,s.v)*dot(r.d,s.v) - s.cosa*s.cosa;
    float b = 2. * (dot(r.d,s.v)*dot(co,s.v) - dot(r.d,co)*s.cosa*s.cosa);
    float c = dot(co,s.v)*dot(co,s.v) - dot(co,co)*s.cosa*s.cosa;

    float det = b*b - 4.*a*c;
    if (det < 0.) return noHit;

    det = sqrt(det);
    float t1 = (-b - det) / (2. * a);
    float t2 = (-b + det) / (2. * a);

    // This is a bit messy; there ought to be a more elegant solution.
    float t = t1;
    if (t < 0. || t2 > 0. && t2 < t) t = t2;
    if (t < 0.) return noHit;

    vec3 cp = r.o + t*r.d - s.c;
    float h = dot(cp, s.v);
    if (h < 0.) return noHit;

    vec3 n = normalize(cp * dot(s.v, cp) / dot(cp, cp) - s.v);

    return t;
}

float check_cone_ray_intersect(vec3 ray_pos, vec3 ray_dir, vec3 cone_pos, vec3 cone_dir, float cone_angle) {
    float res = intersectCone(Cone(cone_angle, cone_pos, cone_dir), Ray(ray_pos, ray_dir));
    return res;
}

void main() {
    vec3 pixel_lin_depth = texture(pos_buffer, tex_coords).xyz - camera_pos;
    vec3 look_dir = normalize(pixel_lin_depth);
    vec4 source = texture(tex_img, tex_coords);
    
    for (int light_i = 0; light_i < ssbo_data.count; ++light_i) {
        // do rot render volume if inside it
        if (dot(normalize(camera_pos - ssbo_data.some_light[light_i].pos), 
                ssbo_data.some_light[light_i].direction
            ) > ssbo_data.some_light[light_i].outer_cut_off)
            continue;
    
        float intersection = check_cone_ray_intersect(camera_pos, 
                                                      look_dir, 
                                                      ssbo_data.some_light[light_i].pos, 
                                                      ssbo_data.some_light[light_i].direction, 
                                                      ssbo_data.some_light[light_i].cut_off);
        // float intersection_outer = check_cone_ray_intersect(camera_pos, 
        //                                                     look_dir, 
        //                                                     ssbo_data.some_light[light_i].pos, 
        //                                                     ssbo_data.some_light[light_i].direction, 
        //                                                     ssbo_data.some_light[light_i].outer_cut_off);
        
        if (intersection < length(pixel_lin_depth)) {
            vec3 curr_color = ssbo_data.some_light[light_i].diffuse_color * 0.01;

            source += vec4(curr_color, 0);
        }
        // else if (intersection_outer < length(pixel_lin_depth)) {
        //     vec3 curr_color = ssbo_data.some_light[light_i].diffuse_color * 0.01 / 2;

        //     source += vec4(curr_color, 0);
        // }
    }

    out_color = source;
}
'''

    def __init__(self, width, height, pos_buffer, color_buffer_type=1):
        self.fbo = FrameBuffer(width, height, color_buffer_type, FB_NONE)
        self.meshes = (RenderCompound(gen_screen_mesh(), Material([(self.fbo.color_buffers[0], 0)] +
                                                                  [(pos_buffer, 1)]
                                                                  )), )
        self.shader_prog = ShaderProgram(sample_vertex_shader, self._fragment_shader)
        self.shader_prog.use()
        self.shader_prog.get_uniform_setter('tex_img', '1i')(0)
        self.shader_prog.get_uniform_setter('pos_buffer', '1i')(1)

    def draw(self, out_fbo, data):
        self.shader_prog.use()
        self.shader_prog.get_uniform_setter('tex_img', '1i')(0)
        self.shader_prog.get_uniform_setter('pos_buffer', '1i')(1)
        ret = super().draw(out_fbo, data)
        return ret
