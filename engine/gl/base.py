from OpenGL.GL import *
from glm import vec3
from ctypes import cast
import numpy as np

from engine.lib.np_helper import int2array


class BasePositioned3D:
    def __init__(self, pos=None):
        if pos is None:
            pos = (0, 0, 0)
        self.pos = vec3(pos)

    def set_position(self, pos):
        # calls set_position to rebuild other position params
        pass

    def move_by_vector(self, vector: vec3):
        self.set_position(self.pos + vector)


class BaseBindable:
    def __init__(self, bind_block_id=0):
        self._bind_block_id = bind_block_id
    
    def bind_to_block(self, block_id=None):
        return self._bind_block_id if block_id is None else block_id

    def set_bind_index(self, index):
        self._bind_block_id = index


class BufferBase(BaseBindable):
    GL_BUF_TYPE = 0
    ARRAY_TYPE = 'float32'

    def __init__(self, data=None, buf_index=0, use=True, array_type=None, buffer_usage=GL_STATIC_DRAW):
        super(BufferBase, self).__init__(buf_index)
        self.buffer_usage = buffer_usage
        self.buff_type = array_type if array_type is not None else self.ARRAY_TYPE
        self.buffer_id = glGenBuffers(1)
        self._buffer_data = np.array([] if data is None else data, dtype=self.buff_type, copy=False)
        self.is_changed = True
        if use:
            self.use()

    def use(self):
        glBindBuffer(self.GL_BUF_TYPE, self.buffer_id)

    def upload(self):
        if self.is_changed:
            self.use()
            glBufferData(self.GL_BUF_TYPE, self._buffer_data.nbytes, self._buffer_data, self.buffer_usage)
            self.is_changed = False

    def force_upload(self):
        self.use()
        glBufferData(self.GL_BUF_TYPE, self._buffer_data.nbytes, self._buffer_data, self.buffer_usage)
        self.is_changed = False

    def download(self):
        self.use()
        glGetBufferSubData(self.GL_BUF_TYPE, 0, self._buffer_data.nbytes, self._buffer_data.view(np.uint8))
        self.is_changed = False

    def sub_src_upload(self, offset, data):
        self.use()
        glBufferSubData(self.GL_BUF_TYPE, offset, data.nbytes, data)

    def chunk_upload(self, offset, size):
        # offset and size described in buffer.dtype
        self.sub_src_upload(offset * self._buffer_data.itemsize, self._buffer_data[offset:offset + size])

    def bind_to_block(self, index=None):
        glBindBufferBase(self.GL_BUF_TYPE, super(BufferBase, self).bind_to_block(index), self.buffer_id)

    def set_buf_data(self, data, upload=False):
        self.is_changed = True
        if isinstance(data, np.ndarray) and data.dtype == self.buff_type:
            self._buffer_data = data.reshape(data.shape)
        else:
            self._buffer_data = np.array(data, dtype=self.buff_type, copy=False)
        if upload:
            self.upload()

    def add_buf_data(self, data, upload=False):
        self.set_buf_data(np.concatenate((self._buffer_data, data)), upload)

    def get_array_chunk_setter(self, offset, count):
        def func(values):
            self.is_changed = True
            self._buffer_data[offset:offset + count] = values
        return func

    def get_array_chunk_getter(self, offset, count):
        return lambda: self._buffer_data[offset:offset + count]

    def get_chunk(self, start, stop):
        return self._buffer_data[start:stop]

    def set_chunk(self, start, stop, value):
        self.is_changed = True
        self._buffer_data[start:stop] = value

    def get_buffer_data(self):
        return self._buffer_data

    @property
    def size(self):
        return len(self._buffer_data)

    def get_raw_memory_data_setter(self, pointer, byte_offset=0):
        return cast(self._buffer_data.__array_interface__['data'][0] + byte_offset, pointer)

    def resize(self, size, zero_items=False):
        old_len = len(self._buffer_data)
        self._buffer_data = np.resize(self._buffer_data, size)
        if zero_items:
            self._buffer_data[old_len:] = 0

    def map_itself(self, size=None):
        shape = (size, )
        if size is None:
            size = self._buffer_data.nbytes
            shape = self._buffer_data.shape

        self.use()
        glBufferStorage(self.GL_BUF_TYPE, size, None,
                        GL_MAP_READ_BIT | GL_MAP_COHERENT_BIT | GL_MAP_PERSISTENT_BIT | GL_MAP_WRITE_BIT)
        _raw_mapped_addr = glMapBufferRange(self.GL_BUF_TYPE, 0, size,
                                            GL_MAP_READ_BIT | GL_MAP_WRITE_BIT)
        c_type = np.ctypeslib.as_ctypes_type(self._buffer_data.dtype)
        self._buffer_data = int2array(_raw_mapped_addr, c_type, shape)

    def __del__(self):
        glDeleteBuffers(1, [self.buffer_id])
