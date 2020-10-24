from OpenGL.GL import GL_UNIFORM_BUFFER, glGetActiveUniformsiv, GL_UNIFORM_OFFSET, GL_UNIFORM_BLOCK_INDEX, \
    glGetInteger, GL_MAX_UNIFORM_BUFFER_BINDINGS
import numpy as np

from .base import BufferBase
from .shader_buffer import ObjStructHelper, StructElem
from .shader import ShaderProgram


class UBO(BufferBase):
    GL_BUF_TYPE = GL_UNIFORM_BUFFER

    # introspection start
    @classmethod
    def get_offsets(cls, prog, items_count: int):
        return cls.get_active_uniforms_iv(prog, range(items_count), GL_UNIFORM_OFFSET)

    @classmethod
    def get_block_indices(cls, prog, items_count: int):
        return cls.get_active_uniforms_iv(prog, range(items_count), GL_UNIFORM_BLOCK_INDEX)

    @staticmethod
    def get_active_uniforms_iv(prog: ShaderProgram, items, pname):
        a = np.array(items, 'uint32')
        out = np.zeros(len(a), 'int32')
        glGetActiveUniformsiv(prog.gl_program, len(a), a, pname, out)
        return out
    # introspection end

    @staticmethod
    def get_max_binding_points():
        return glGetInteger(GL_MAX_UNIFORM_BUFFER_BINDINGS)


# todo fix duplicate code with shader buffer (common buffer and array buffer)
class StructuredUniformArrayBuffer(UBO):
    def __init__(self, name, structure, struct_offset=0, *args, **kwargs):
        self.name = name
        # WARNING: do not use force buffer data setting
        super(StructuredUniformArrayBuffer, self).__init__(data=[0] * struct_offset, *args, **kwargs)
        self.struct = ObjStructHelper(structure, struct_offset)
        self.upload_callback = lambda count: True

    def set_upload_callback(self, func):
        self.upload_callback = func

    def upload(self):
        struct_obj = self.struct
        self.upload_callback((len(self._buffer_data) - struct_obj.offset) // struct_obj.struct_len)
        super(StructuredUniformArrayBuffer, self).upload()

    def add_frame(self, **keyword_params):
        self.struct.add_struct_to_buffer(self, **keyword_params)

    def get_struct_value_setter(self, name, index=0):
        return self.struct.get_struct_value_setter(self, name, index)

    def __getitem__(self, item):
        return StructElem(self, item)


class StructuredUniformBuffer(UBO):
    def __init__(self, name, structure, *args, **kwargs):
        object.__setattr__(self, 'struct', ObjStructHelper(structure))
        object.__setattr__(self, '_setters', {name: self.struct.get_value_pointers(name) for name in self.struct.data})
        super(StructuredUniformBuffer, self).__init__(data=[0] * self.struct.struct_len, *args, **kwargs)
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
