//head
layout (location = 0) in vec2 a_pos;
layout (location = 1) in vec2 a_uv;

out vec2 uv;
//section 0
//end

void main() {
    //main
    gl_Position = vec4(a_pos, 0, 1);
    uv = a_uv;

    //section 0
    //end
}
