from typing import Optional, Union

import numpy as np
from OpenGL.GL import GL_RGBA
from glm import ivec4, vec4

from ..gl.mesh import VAOMesh
from ..gl.texture import Texture2D

white_color = np.zeros((4, 1, 1), 'int8')
white_color.fill(255)
white_color.flags.writeable = False


class RenderData:
    __STATIC_MESH = None

    def __init__(self, data: Optional[Union[np.ndarray, int, ivec4]] = None):
        self.opengl_texture = Texture2D(interpolation='mipmap', anisotropic_levels=0)
        self.mesh = self.gen_mesh()
        self.set_data(data)
        self.color = vec4(0)

    def set_data(self, data: Optional[Union[np.ndarray, int, ivec4]]):
        if data is None:
            data = white_color
        elif isinstance(data, int):
            data = np.array(ivec4(data), 'int8').reshape((4, 1, 1))
        elif isinstance(data, ivec4):
            data = np.array(data, 'int8').reshape((4, 1, 1))
        self.opengl_texture.load_from_bytes(data, GL_RGBA, GL_RGBA, *data.shape[:0:-1], True)

        # returning (width, height)
        shape = data.shape
        if len(shape) == 1:
            return 1, 1
        elif len(shape) == 3:
            shape = shape[1:]
        if len(shape) == 2:
            return shape[::-1]
        return 1, 1

    def gen_mesh(self):
        if self.__STATIC_MESH is None:
            self.__STATIC_MESH = VAOMesh([0, 0, 0, 1,
                                          0, 1, 0, 0,
                                          1, 1, 1, 0,
                                          1, 0, 1, 1],
                                         [0, 1, 2, 2, 3, 0], (2, 2))
        return self.__STATIC_MESH
