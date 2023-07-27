from abc import abstractmethod

import numpy as np
from OpenGL.GL import *
from PIL import Image

from .base import BaseBindable


class BaseTexture(BaseBindable):
    BIND_POINT = 0

    def __init__(self, use=True, block_id=0, anisotropic_levels=0, interpolation='mipmap', border='repeat'):
        super(BaseTexture, self).__init__(block_id)
        self.sampler_id = glGenTextures(1)

        if use:
            self.use()
        if anisotropic_levels:
            self.set_anisotropic_levels(anisotropic_levels)
        self.set_interpolation(interpolation)
        self.set_border(border)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

    def use(self):
        glBindTexture(self.BIND_POINT, self.sampler_id)

    def bind_to_block(self, block_id=None):
        glActiveTexture(GL_TEXTURE0 + super(BaseTexture, self).bind_to_block(block_id))
        self.use()

    @classmethod
    def unbind_block(cls, block_id, tex_type=None):
        glActiveTexture(GL_TEXTURE0 + block_id)
        glBindTexture(tex_type or cls.BIND_POINT, 0)

    def set_interpolation(self, value):
        if isinstance(value, str):
            value = {'linear': GL_LINEAR, 'mipmap': GL_LINEAR_MIPMAP_LINEAR, 'nearest': GL_NEAREST}[value]
        mag_value = value if value is not GL_LINEAR_MIPMAP_LINEAR else GL_LINEAR
        glTexParameteri(self.BIND_POINT, GL_TEXTURE_MIN_FILTER, value)
        glTexParameteri(self.BIND_POINT, GL_TEXTURE_MAG_FILTER, mag_value)

    @abstractmethod
    def set_border(self, value):
        pass

    @staticmethod
    def get_max_anisotropic_levels():
        return glGetIntegerv(0x84FF)

    def set_anisotropic_levels(self, levels):
        glTexParameteri(self.BIND_POINT, 0x84FE, levels)

    def set_rgba_swizzling(self, data):
        values = {0: GL_ZERO, 1: GL_ONE,
                  '0': GL_ZERO, '1': GL_ONE,
                  'red': GL_RED, 'r': GL_RED,
                  'blue': GL_BLUE, 'b': GL_BLUE,
                  'green': GL_GREEN, 'g': GL_GREEN,
                  'alpha': GL_ALPHA, 'a': GL_ALPHA}
        arr = np.zeros((4, ), 'int32')
        for i, item in enumerate(data):
            arr[i] = values[item]
        glTexParameteriv(self.BIND_POINT, GL_TEXTURE_SWIZZLE_RGBA, arr)

    def __del__(self):
        glDeleteTextures(1, [self.sampler_id])


class Texture2D(BaseTexture):
    BIND_POINT = GL_TEXTURE_2D

    @classmethod
    def tex_from_file(cls, filename, use=True, block_id=0, anisotropic_levels=0, interpolation='mipmap',
                      *args, **kwargs):
        obj = cls(use=use, block_id=block_id, anisotropic_levels=anisotropic_levels, interpolation=interpolation)
        obj.load_from_file(filename, *args, **kwargs)
        return obj

    @classmethod
    def tex_from_binary_file(cls, filename, width, height, pixel_format, use=True, block_id=0,
                             anisotropic_levels=0, interpolation='mipmap', border='repeat', *args, **kwargs):
        obj = cls(use=use, block_id=block_id, anisotropic_levels=anisotropic_levels,
                  interpolation=interpolation, border=border)
        obj.load_from_binary_file(filename, width, height, pixel_format, *args, **kwargs)
        return obj

    def __init__(self, use=True, block_id=0, anisotropic_levels=0, interpolation='mipmap', border='repeat'):
        super(Texture2D, self).__init__(use, block_id, anisotropic_levels, interpolation, border)
        self.width = 0
        self.height = 0

    def set_border(self, value):
        if isinstance(value, str):
            value = {'clamp': GL_CLAMP_TO_BORDER, 'repeat': GL_REPEAT,
                     'mirror': GL_MIRRORED_REPEAT, 'edge': GL_CLAMP_TO_EDGE}[value]
        glTexParameteri(self.BIND_POINT, GL_TEXTURE_WRAP_S, value)
        glTexParameteri(self.BIND_POINT, GL_TEXTURE_WRAP_T, value)

    def load_from_file(self, filename: str, mipmap=True, alpha=False, gamma_corr=True):
        pil_type = 'RGBA' if alpha else 'RGB'
        src_gl_type = GL_RGBA if alpha else GL_RGB
        if alpha:
            dst_gl_type = GL_SRGB_ALPHA if gamma_corr else GL_RGBA
        else:
            dst_gl_type = GL_SRGB if gamma_corr else GL_RGB

        img = Image.open(filename).convert(pil_type)
        width, height = img.size
        self.use()
        self.load_from_bytes(img.tobytes('raw', pil_type, 0, -1),
                             dst_gl_type, src_gl_type, width, height, mipmap)
        return width, height

    def load_from_binary_file(self, filename, width, height, pixel_format, tex_data_type=None,
                              data_type=GL_UNSIGNED_BYTE, mipmap=False):
        tex_data_type = tex_data_type or pixel_format
        im_bytes = open(filename, 'rb').read()
        self.use()
        self.load_from_bytes(im_bytes, tex_data_type, pixel_format, width, height, mipmap, data_type)

    def load_from_bytes(self, byte_data, internal_type, data_format, width, height, mipmap=False,
                        data_type=GL_UNSIGNED_BYTE):
        self.bind_to_block()
        self.width = width
        self.height = height
        glTexImage2D(self.BIND_POINT, 0, internal_type, width, height, 0, data_format, data_type, byte_data)
        if mipmap:
            glGenerateMipmap(self.BIND_POINT)

    def load_zeros(self, i_type=GL_RGB, d_format=GL_RGB, width=0, height=0, mipmap=False, d_type=GL_UNSIGNED_BYTE):
        self.load_from_bytes(0, i_type, d_format, width, height, mipmap, d_type)


# todo ConstantTextureManager which can generate textures, filled with specific values
#  (may be used in model loading when some texture not found)
