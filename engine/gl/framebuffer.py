from typing import Union, Iterable

from OpenGL.GL import *
import numpy as np

from .texture import Texture2D

FB_NONE = 0
FB_TEXTURE_BUFFER = 1
FB_RENDER_BUFFER = 2


class RenderBuffer:
    def __init__(self, use=True):
        self.buffer_id = glGenRenderbuffers(1)
        if use:
            self.use()

    def use(self):
        glBindRenderbuffer(GL_RENDERBUFFER, self.buffer_id)

    @staticmethod
    def set_data(width, height, internalformat):
        glRenderbufferStorage(GL_RENDERBUFFER, internalformat, width, height)


class FrameBufferTextureAttachment(Texture2D):
    ATTACH_TARGET = 0
    TEX_TYPE = 0
    TEX_INTERNAL_TYPE = 0
    TEX_DATA_TYPE = GL_UNSIGNED_BYTE

    def __init__(self, width, height, **kwargs):
        super(FrameBufferTextureAttachment, self).__init__(use=True, interpolation='nearest', border='clamp', **kwargs)
        self.resize(width, height)

    def resize(self, width, height):
        self.load_from_bytes(GLvoidp(0), self.TEX_INTERNAL_TYPE, self.TEX_TYPE, width, height,
                             False, self.TEX_DATA_TYPE)

    def bind_to_framebuffer(self, target=GL_FRAMEBUFFER):
        glFramebufferTexture(target, self.ATTACH_TARGET, self.sampler_id, 0)


class FrameBufferRenderAttachment(RenderBuffer):
    ATTACH_TARGET = 0
    TEX_INTERNAL_TYPE = 0

    def __init__(self, width, height):
        super(FrameBufferRenderAttachment, self).__init__()
        self.resize(width, height)

    def resize(self, width, height):
        self.set_data(width, height, self.TEX_INTERNAL_TYPE)

    def bind_to_framebuffer(self, target=GL_FRAMEBUFFER):
        glFramebufferRenderbuffer(target, self.ATTACH_TARGET, GL_RENDERBUFFER, self.buffer_id)


class ColorTextureBuffer(FrameBufferTextureAttachment):
    ATTACH_TARGET = GL_COLOR_ATTACHMENT0
    TEX_TYPE = GL_RGB
    TEX_INTERNAL_TYPE = GL_RGB

    @classmethod
    def move(cls, value):
        return type(cls.__name__, (cls, ), {'ATTACH_TARGET': cls.ATTACH_TARGET + value})

    @classmethod
    def custom_buf_type(cls, buf_type):
        return type(cls.__name__, (cls,), {'TEX_TYPE': buf_type, 'TEX_INTERNAL_TYPE': buf_type})


class ColorFloatTextureBuffer(ColorTextureBuffer):
    TEX_INTERNAL_TYPE = GL_RGB32F
    TEX_DATA_TYPE = GL_FLOAT


class DepthTextureBuffer(FrameBufferTextureAttachment):
    ATTACH_TARGET = GL_DEPTH_ATTACHMENT
    TEX_TYPE = GL_DEPTH_COMPONENT
    TEX_INTERNAL_TYPE = GL_DEPTH_COMPONENT
    TEX_DATA_TYPE = GL_FLOAT


class DepthRenderBuffer(FrameBufferRenderAttachment):
    ATTACH_TARGET = GL_DEPTH_ATTACHMENT
    TEX_INTERNAL_TYPE = GL_DEPTH_COMPONENT


class StencilDepthTextureBuffer(FrameBufferTextureAttachment):
    ATTACH_TARGET = GL_DEPTH_STENCIL_ATTACHMENT
    TEX_TYPE = GL_DEPTH_STENCIL
    TEX_INTERNAL_TYPE = GL_DEPTH24_STENCIL8
    TEX_DATA_TYPE = GL_UNSIGNED_INT_24_8


class StencilDepthRenderBuffer(FrameBufferRenderAttachment):
    ATTACH_TARGET = GL_DEPTH_STENCIL_ATTACHMENT
    TEX_INTERNAL_TYPE = GL_DEPTH24_STENCIL8


# deprecated, todo remove this class
class StaticFrameBuffer:
    window_width = 0
    window_height = 0
    clear_mask = GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT

    @staticmethod
    def set_read_buffer(value=GL_NONE):
        glReadBuffer(value)

    @staticmethod
    def set_draw_buffer(value=GL_NONE):
        glDrawBuffer(value)

    @staticmethod
    def bind_default_framebuffer():
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
    use = bind_default_framebuffer

    @classmethod
    def clear(cls):
        glClear(cls.clear_mask)

    @staticmethod
    def set_viewport(width, height):
        glViewport(0, 0, width, height)

    @classmethod
    def add_depth_buffer(cls):
        pass


class FrameBuffer(StaticFrameBuffer):
    def __init__(self, width, height, color_buffers=1, depth_buffer=FB_RENDER_BUFFER,
                 stencil_depth_buffer=FB_NONE):
        # todo make ability to pass existing depth and stencil-depth buffers (objects, not classes or consts)
        self.width, self.height = width, height
        self.buffer_id = glGenFramebuffers(1)
        self.use()
        self.stencil_depth_buffer = None
        self.depth_buffer = None
        self.color_buffers = []
        self.clear_mask = 0

        self._gen_color_buffers(color_buffers)
        if stencil_depth_buffer:
            selected_buffer = [StencilDepthTextureBuffer, StencilDepthRenderBuffer][stencil_depth_buffer - 1]
            self.stencil_depth_buffer = selected_buffer(width, height)
            self.stencil_depth_buffer.bind_to_framebuffer()
            self.clear_mask |= GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT
        if depth_buffer:
            self.add_depth_buffer(depth_buffer)

    def _gen_color_buffers(self, buffers: Union[int, list, tuple, Iterable[ColorTextureBuffer]]):
        if isinstance(buffers, int):
            buffers = [ColorTextureBuffer] * buffers
        for i, buf in enumerate(buffers):

            if isinstance(buf, ColorTextureBuffer):
                self.color_buffers.append(buf)
            else:
                self.color_buffers.append(buf.move(i)(self.width, self.height))

            self.color_buffers[i].bind_to_framebuffer()
            self.clear_mask |= GL_COLOR_BUFFER_BIT
        self.set_draw_buffers(len(buffers))

    @staticmethod
    def set_draw_buffers(buffer_count):
        glDrawBuffers(buffer_count,
                      np.array(tuple(map(GL_COLOR_ATTACHMENT0.__add__, range(buffer_count))), 'uint32'))

    def add_depth_buffer(self, depth_buffer=FB_RENDER_BUFFER):
        if self.depth_buffer is None and self.stencil_depth_buffer is None:
            self.use()

            if isinstance(depth_buffer, int):
                selected_buffer = [DepthTextureBuffer, DepthRenderBuffer][depth_buffer - 1]
                self.depth_buffer = selected_buffer(self.width, self.height)
            else:
                self.depth_buffer = depth_buffer

            self.depth_buffer.bind_to_framebuffer()
            self.clear_mask |= GL_DEPTH_BUFFER_BIT
        else:
            print('WARNING: attempted to add depth buffer, but it was already added')  # todo add this to logging

    def clear(self):
        self.use()
        glClear(self.clear_mask)

    def recreate(self):
        self.bind_default_framebuffer()
        self.__del__()
        self.buffer_id = glGenFramebuffers(1)
        self.use()
        # todo recreate buffer and it's attachments
        self._gen_color_buffers(self.color_buffers)

    def resize(self, width, height):
        if self.width == width and self.height == height:
            return
        if self.color_buffers:
            for buf in self.color_buffers:
                buf.resize(width, height)
        if self.depth_buffer is not None:
            self.depth_buffer.resize(width, height)
        if self.stencil_depth_buffer is not None:
            self.stencil_depth_buffer.resize(width, height)
        self.width, self.height = width, height

    def use(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer_id)
        self.set_viewport(self.width, self.height)

    @staticmethod
    def set_clear_color(col: tuple or list):
        glClearColor(*col)

    def finish(self):  # called when finished rendering to this buffer
        pass

    def __del__(self):
        glDeleteFramebuffers(1, [self.buffer_id])
