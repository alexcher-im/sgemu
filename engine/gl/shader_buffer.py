from OpenGL.GL import GL_SHADER_STORAGE_BUFFER
import numpy as np

from .base import BufferBase


class SSBO(BufferBase):
    GL_BUF_TYPE = GL_SHADER_STORAGE_BUFFER


class ObjStructHelper:
    @classmethod
    def from_source(cls, data):
        obj = cls(())
        for item in data:
            obj.add_elem(*item)

    def __init__(self, struct_data, offset=0):
        self.offset = offset

        self.struct_len = 0
        self.data = {}  # name: (offset, len)
        for item in struct_data:
            self.data[item[0]] = (self.struct_len, item[1])
            self.struct_len += item[1]
        self.data.pop(None, None)

    def add_elem(self, name, offset, length):
        self.data[name] = (offset, length)

    def get_frame_pointer(self, index):
        return self.struct_len * index + self.offset, self.struct_len

    def get_value_pointers(self, name, index=0):
        curr_frame = self.data[name]
        return self.struct_len * index + curr_frame[0] + self.offset, \
               self.struct_len * index + curr_frame[0] + self.offset + curr_frame[1]

    def get_struct_value_setter(self, buffer: BufferBase, name, index=0):
        curr_frame = self.data[name]
        return buffer.get_array_chunk_setter(self.struct_len * index + curr_frame[0] + self.offset,
                                             curr_frame[1])

    def get_struct_value_getter(self, buffer, name, index=0):
        curr_frame = self.data[name]
        return buffer.get_array_chunk_getter(self.struct_len * index + curr_frame[0] + self.offset,
                                             curr_frame[1])

    def _gen_struct(self, **kwargs):
        """
        Generates 1 element of current structure
        :param kwargs:
          params name:value for required elements
        :return:
          numpy array with generated structure
        """
        arr = np.array([0] * self.struct_len, dtype='float32')
        for name, value in kwargs.items():
            start, count = self.data[name]
            arr[start:start + count] = value
        return arr

    def add_struct_to_buffer(self, buffer: BufferBase, **kwargs):
        buffer.add_buf_data(self._gen_struct(**kwargs))


class StructElem:
    def __init__(self, buffer, index):
        object.__setattr__(self, 'index', index)
        object.__setattr__(self, 'buffer', buffer)

    def __getattr__(self, item):
        try:
            return self.__dict__[item]
        except KeyError:
            addr = self.buffer.struct.get_value_pointers(item, self.index)
            return self.buffer.get_chunk(*addr)

    def __setattr__(self, key, value):
        try:
            addr = self.buffer.struct.get_value_pointers(key, self.index)
            return self.buffer.set_chunk(*addr, value)
        except KeyError:
            self.__dict__[key] = value


class StructuredShaderBuffer(SSBO):
    def __init__(self, name, structure, *args, **kwargs):
        object.__setattr__(self, 'struct', ObjStructHelper(structure))
        object.__setattr__(self, '_setters', {name: self.struct.get_value_pointers(name) for name in self.struct.data})
        super(StructuredShaderBuffer, self).__init__(data=[0] * self.struct.struct_len, *args, **kwargs)
        self.name = name

    def get_struct_value_setter(self, name, index=0):
        return self.struct.get_struct_value_setter(self, name, index)

    def hasattr(self, attr: str):
        return attr in self._setters

    def add_elem(self, name: str, offset: int, length: int):
        self.struct.add_elem(name, offset, length)
        self._setters[name] = self.struct.get_value_pointers(name)

    def __getattr__(self, item):
        try:
            indices = self._setters[item]
            return self._buffer_data[indices[0]:indices[1]]
        except KeyError:
            return self.__dict__[item]

    def __setattr__(self, key, value):
        try:
            indices = self._setters[key]
            self.set_chunk(indices[0], indices[1], value)
        except KeyError:
            self.__dict__[key] = value


class StructuredShaderArrayBuffer(SSBO):
    def __init__(self, name, structure, struct_offset=0, *args, **kwargs):
        self.name = name
        # WARNING: do not use force buffer data setting
        super(StructuredShaderArrayBuffer, self).__init__(data=[0] * struct_offset, *args, **kwargs)
        self.struct = ObjStructHelper(structure, struct_offset)
        self.upload_callback = lambda count: True

    def set_upload_callback(self, func):
        self.upload_callback = func

    def upload(self):
        struct_obj = self.struct
        self.upload_callback((len(self._buffer_data) - struct_obj.offset) // struct_obj.struct_len)
        super(StructuredShaderArrayBuffer, self).upload()

    def add_frame(self, **keyword_params):
        self.struct.add_struct_to_buffer(self, **keyword_params)

    def get_struct_value_setter(self, name, index=0):
        return self.struct.get_struct_value_setter(self, name, index)

    def __getitem__(self, item):
        return StructElem(self, item)
