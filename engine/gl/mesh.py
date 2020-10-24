from typing import Union

from OpenGL.GL import *

from .base import BufferBase


class VBO(BufferBase):
    GL_BUF_TYPE = GL_ARRAY_BUFFER


class EBO(BufferBase):
    GL_BUF_TYPE = GL_ELEMENT_ARRAY_BUFFER
    ARRAY_TYPE = 'uint32'


class VAO:
    def __init__(self, attrib_sizes: Union[tuple, list]):
        # attrib_sizes: (int, int, ...) or ((GL_TYPE, type_size, vector size), ...)
        # example: (3, 3, 2) equals ((GL_FLOAT, 4, 3), (GL_FLOAT, 4, 3), (GL_FLOAT, 4, 2))
        if len(attrib_sizes) == 0:
            raise ValueError("Cannot create VertexArray without attribute information")
        if isinstance(attrib_sizes[0], int):
            attrib_sizes = tuple(map(lambda size: (GL_FLOAT, 4, size), attrib_sizes))

        self.buffer_id = glGenVertexArrays(1)
        self.use()
        self.attrib_sizes = attrib_sizes
        self.vertex_elem_size = sum((f[2] for f in attrib_sizes))
        self.vertex_byte_size = sum((f[1] * f[2] for f in attrib_sizes))  # in bytes
        self.vbo = VBO([], use=True)
        self._set_attrib_data()

    def _set_attrib_data(self):
        curr_offset = 0
        for i, (gl_type, type_size, size) in enumerate(self.attrib_sizes):
            glVertexAttribPointer(i, size, gl_type, GL_FALSE, self.vertex_byte_size, GLvoidp(curr_offset))
            glEnableVertexAttribArray(i)
            curr_offset += size * type_size

    def use(self):
        glBindVertexArray(self.buffer_id)

    def __del__(self):
        glDeleteVertexArrays(1, [self.buffer_id])


class VAOMesh:
    def __init__(self, vertices=None, indices=None, attr_data=(), mode=GL_TRIANGLES):
        self.render_mode = mode
        self.vao = VAO(attr_data)
        self.vbo = self.vao.vbo
        self.ebo = EBO([], use=True)
        self.set_vertex_data(vertices if vertices is not None else [], indices)

    def use(self):
        self.vao.use()

    @staticmethod
    def unbind():
        glBindVertexArray(0)

    def set_vertex_data(self, vertices, indices=None):
        if indices is None:
            indices = tuple(range(len(vertices) // self.vao.vertex_elem_size))
        self.vbo.set_buf_data(vertices, True)
        self.ebo.set_buf_data(indices,  True)

    def draw(self):
        glDrawElements(self.render_mode, self.ebo.size, GL_UNSIGNED_INT, None)


class VAOMeshInstanced(VAOMesh):
    def __init__(self, vertices=None, indices=None, attr_data=(), mode=GL_TRIANGLES, instances=1):
        super(VAOMeshInstanced, self).__init__(vertices, indices, attr_data, mode)
        self.instances = instances

    def draw(self):
        glDrawElementsInstanced(self.render_mode, self.ebo.size, GL_UNSIGNED_INT, None, self.instances)
