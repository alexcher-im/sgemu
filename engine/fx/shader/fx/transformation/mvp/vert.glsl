//head
layout (location = 0) in vec3 pos_a;
layout (location = 1) in vec3 normal_a;
layout (location = 2) in vec2 uv_coord_a;

out vec3 pos;
out vec3 normal;
out vec2 uv;

layout (std140, binding = 0) uniform MVPMatrices {
    mat4 model;
    mat4 view;
    mat4 projection;
    mat4 view_projection;
    mat4 model_view_projection;
};
//end


void main() {
    //main
    gl_Position = model_view_projection * vec4(pos_a.xyz, 1.0);

    pos = (model * vec4(pos_a, 1)).xyz;
    normal = normal_a;// * transpose(inverse(mat3(model)));
    uv = uv_coord_a;
    //end
}
