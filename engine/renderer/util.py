import glm
import numpy as np
from ..gl.mesh import VAOMesh

# vertex data: (2, 2)
#                               pos      uv
screen_vertices = np.array([((-1,  1), (0, 1)),
                            ((-1, -1), (0, 0)),
                            ((1, -1),  (1, 0)),
                            ((1,  1),  (1, 1))], 'float32')
screen_indices = np.array([0, 1, 2, 2, 3, 0], dtype='float32')

_saved_mesh = None


# language=GLSL
sample_vertex_shader = """\
#version 430 core

layout (location = 0) in vec2 a_pos;
layout (location = 1) in vec2 a_uv;

out vec2 tex_coords;

void main() {
    gl_Position = vec4(a_pos, 0, 1);
    tex_coords = a_uv;
}
"""


class ScreenMesh(VAOMesh):
    def __init__(self):
        super().__init__(screen_vertices, screen_indices, (2, 2))

    @staticmethod
    def src_move_vert(start_pos, end_pos, src: np.ndarray):
        diff_pos = glm.vec2(end_pos[0] - start_pos[0], 1 - (end_pos[1] - start_pos[1])) * 2 - 1

        buf_data = src.copy()
        buf_data[:, 0, 0] = glm.vec4(-1, -1, diff_pos[0], diff_pos[0]) + start_pos[0] * 2
        buf_data[:, 0, 1] = glm.vec4(1, diff_pos[1], diff_pos[1], 1) - start_pos[1] * 2

        return buf_data

    @staticmethod
    def src_move_uv(start_pos, end_pos, src: np.ndarray):
        diff_pos = glm.vec2(end_pos[0] - start_pos[0], 1 - (end_pos[1] - start_pos[1]))
        buf_data = src.copy()
        buf_data[:, 1, 0] = glm.vec4(0, 0, diff_pos[0], diff_pos[0]) + start_pos[0]
        buf_data[:, 1, 1] = glm.vec4(1, diff_pos[1], diff_pos[1], 1) - start_pos[1]

        return buf_data

    def move_vertices(self, start_pos=(0, 0), end_pos=(1, 1)):
        # here:
        # (0, 0) - upper left corner
        # (1, 1) - lower right corner

        self.vbo.set_buf_data(self.src_move_vert(start_pos, end_pos, screen_vertices), True)

    def move_uv(self, start_pos=(0, 0), end_pos=(1, 1)):
        # here:
        # (0, 0) - upper left corner
        # (1, 1) - lower right corner

        self.vbo.set_buf_data(self.src_move_uv(start_pos, end_pos, screen_vertices), True)

    def move_both(self, vert_start=(0, 0), vert_end=(1, 1), uv_start=(0, 0), uv_end=(1, 1)):
        buf_data = self.src_move_vert(vert_start, vert_end, screen_vertices)
        buf_data = self.src_move_uv(uv_start, uv_end, buf_data)
        self.vbo.set_buf_data(buf_data, True)


def gen_screen_mesh():
    global _saved_mesh
    if _saved_mesh is not None:
        return _saved_mesh
    _saved_mesh = ScreenMesh()
    return _saved_mesh
