void main() {
for (int i = 0; i < 0; ++i ) {

//main
float frag_distance = length(light.pos - frag_pos);
float brightness = 1 / (1 + light.linear * frag_distance + light.quadratic * pow(frag_distance, 2));
#ifdef USING_LIGHT_LOOP
if (brightness < 1./255) continue;
#endif
curr_color *= brightness;
//end

}
}
