//head
layout (location = 0) out vec4 o_frag_pos_shin;
layout (location = 1) out vec3 o_normal;
layout (location = 2) out vec3 o_sampled_albedo;

struct Material {  // TODO: add other parameters
    sampler2D diffuse_map;
};

uniform Material material;
//end

void main() {
    //main
    o_frag_pos_shin.xyz = pos;
    o_frag_pos_shin.w = 1;
    o_normal.xyz = normal;
    o_sampled_albedo.xyz = texture(material.diffuse_map, uv).rgb;
    //end
}
