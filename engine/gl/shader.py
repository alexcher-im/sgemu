from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader

from ..lib.pathlib import read_file


class ShaderStorageBuffersList:
    instances = {}

    @classmethod
    def add_buffer(cls, name, buffer):
        cls.instances[name] = buffer

    @classmethod
    def get_buffer(cls, name):
        return cls.instances[name]


class ShaderProgram:
    @classmethod
    def from_files(cls, v_filename, f_filename, use=False):
        return cls(read_file(v_filename), read_file(f_filename), use)

    def __init__(self, vs, fs, use=False, *args, **kwargs):
        self.gl_program = self.make_program_from_shader_source(vs, fs, use, *args, **kwargs)

    def use(self):
        glUseProgram(self.gl_program)

    def get_uniform_setter(self, addr, v_type, *additional_args):
        func = globals()['glUniform' + v_type]
        location = glGetUniformLocation(self.gl_program, addr) if isinstance(addr, str) else addr

        return (lambda *args: func(location, *args)) if not additional_args else \
               (lambda *args: func(location, *additional_args, *args))

    # introspection start
    def _get_internal_data(self, gl_req_func, gl_type):
        data = [gl_req_func(self.gl_program, i)
                for i in range(glGetProgramiv(self.gl_program, gl_type))]
        return data

    def get_attributes(self):
        data = self._get_internal_data(glGetActiveAttrib, GL_ACTIVE_ATTRIBUTES)
        sorted_data = [0] * len(data)
        for item in data:
            sorted_data[glGetAttribLocation(self.gl_program, item[0])] = item
        return sorted_data

    def get_uniforms(self):
        # returns list with all uniforms (name, size, type)
        return self._get_internal_data(glGetActiveUniform, GL_ACTIVE_UNIFORMS)

    def get_uniform_block_names(self):
        # returns list with all uniform block names (str)
        return [bytes(glGetActiveUniformBlockName(self.gl_program, i, 1024)[1]).replace(b'\x00', b'').decode().strip()
                for i in range(glGetProgramiv(self.gl_program, GL_ACTIVE_UNIFORM_BLOCKS))]

    def get_uniform_block_indices(self):
        # returns dict with UBO block indices
        return {name: glGetUniformBlockIndex(self.gl_program, name) for name in self.get_uniform_block_names()}

    def get_uniform_block_bindings(self):
        # returns dict with UBO block binding points
        return {name: glUniformBlockBinding(self.gl_program, name) for name in self.get_uniform_block_names()}

    def get_ssbo_names(self):
        return [bytes(glGetProgramResourceName(self.gl_program, GL_SHADER_STORAGE_BLOCK, i, 1024)[1])
                    .replace(b'\0', b'').decode()
                for i in range(glGetProgramInterfaceiv(self.gl_program, GL_SHADER_STORAGE_BLOCK, GL_ACTIVE_RESOURCES))]

    def get_ssbo_block_indices(self):
        return {name: glGetProgramResourceIndex(self.gl_program, GL_SHADER_STORAGE_BLOCK, name)
                for name in self.get_ssbo_names()}
    # introspection end

    @staticmethod
    def make_program_from_shader_source(vertex_shader, fragment_shader, use=True, geometry_shader=None):
        program = glCreateProgram()

        vertex_compiled = compileShader(vertex_shader, GL_VERTEX_SHADER) \
            if isinstance(vertex_shader, str) or isinstance(vertex_shader, bytes) else vertex_shader
        glAttachShader(program, vertex_compiled)
        fragment_compiled = compileShader(fragment_shader, GL_FRAGMENT_SHADER) \
            if isinstance(fragment_shader, str) or isinstance(fragment_shader, bytes) else fragment_shader
        glAttachShader(program, fragment_compiled)

        if geometry_shader is not None:
            geometry_compiled = compileShader(geometry_shader, GL_GEOMETRY_SHADER) \
                if isinstance(geometry_shader, str) or isinstance(geometry_shader, bytes) else geometry_shader
            glAttachShader(program, geometry_compiled)

        glLinkProgram(program)
        if glGetProgramiv(program, GL_LINK_STATUS) == GL_FALSE:
            raise RuntimeError(glGetProgramInfoLog(program).decode())
        if use:
            glUseProgram(program)
        return program

    @staticmethod
    def compile_shader(shader, s_type):
        s_type = {'v': GL_VERTEX_SHADER, 'vert': GL_VERTEX_SHADER, 'vertex': GL_VERTEX_SHADER,
                  'f': GL_FRAGMENT_SHADER, 'frag': GL_FRAGMENT_SHADER, 'fragment': GL_FRAGMENT_SHADER,
                  'g': GL_GEOMETRY_SHADER, 'geom': GL_GEOMETRY_SHADER, 'geometry': GL_GEOMETRY_SHADER}[s_type]
        return compileShader(shader, s_type)

    def __del__(self):
        glDeleteProgram(self.gl_program)
