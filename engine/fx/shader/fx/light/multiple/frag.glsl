//head
#define USING_LIGHT_LOOP

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

#ifdef MULT_LIGHT_UBO_BUFFER
layout(std140, binding = 0) uniform SpotLightStorage
{
    int count;
    Light some_light[];
} ssbo_data;
#else
layout(std140, binding = 0) buffer SpotLightStorage
{
    int count;
    Light some_light[];
} ssbo_data;
#endif
//section 0
//end

void main() {
    //main
    for (int i = 0; i < ssbo_data.count; ++i) {
        Light light = ssbo_data.some_light[i];

        vec3 curr_color;
        //section 0
        result += curr_color;
    }
    //end
}
