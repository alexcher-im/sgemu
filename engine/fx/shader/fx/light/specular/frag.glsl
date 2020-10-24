void main() {
    //main
    vec3 view_dir = normalize(camera_pos - frag_pos);
    vec3 light_dir = normalize(light.pos - frag_pos);
    vec3 halfway_light = normalize(light_dir + view_dir);

    float spec_power = pow(max(dot(halfway_light, normal), 0.0), 32);
    vec3 specular = spec_power * light.specular_color * specular_cf;
    specular = mix(specular, specular * texel.xyz, 0.95);  // TODO: replace 0.0 with material.specular_corellation
    curr_color += specular;
    //end
}
