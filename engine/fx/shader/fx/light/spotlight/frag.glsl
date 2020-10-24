void main() {

for (int i = 0; i < 0; ++i){
//main
vec3 light_dir = normalize(light.pos - frag_pos);

float theta = dot(light_dir, -light.direction);
float eps = light.cut_off - light.outer_cut_off;
float intensity = clamp((theta - light.outer_cut_off) / eps, 0, 1);
#ifdef USING_LIGHT_LOOP
if (intensity <= 0.0) continue;
#endif
//end
curr_color *= intensity;
}

}
