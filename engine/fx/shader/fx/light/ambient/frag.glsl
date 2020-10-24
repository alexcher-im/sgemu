//head
uniform vec3 ambient_color;
//end

void main() {
    //main
    vec3 ambient = texel.xyz * ambient_color;
    result += ambient;
    //end
}
