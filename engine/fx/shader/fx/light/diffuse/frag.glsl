void main() {
    //main
    vec3 light_dir = normalize(light.pos - frag_pos);
    float diffuse_power = max(dot(light_dir, normal), 0);
    vec3 diffuse = diffuse_power * texel.xyz * light.diffuse_color;
    curr_color += diffuse;
    //end
}
