//head
in vec2 uv;

uniform sampler2D pos_shin_map;
uniform sampler2D normal_map;
uniform sampler2D albedo;

out vec3 out_color;

uniform vec3 camera_pos;
//section 0
//end

void main() {
    // TODO: there must be an easy way to implement a TBDL
    //main
    // gathering info from textures
    vec4 _sampled_pos_shin = texture(pos_shin_map, uv);
    vec4 _sampled_normal = texture(normal_map, uv);
    vec4 _sampled_albedo = texture(albedo, uv);

    vec3 frag_pos = _sampled_pos_shin.xyz;
    float shininess = _sampled_pos_shin.w;
    vec3 normal = _sampled_normal.xyz;
    vec4 texel = _sampled_albedo;
    float specular_cf = texel.w;

    vec3 result;

    //section 0
    out_color = result;
    //end
}
