from numpy import dtype
from OpenGL.GL import *

items = {}
default_post = lambda func: func
np_int = dtype('int32')
np_float = dtype('float32')
np_uint = dtype('uint32')
np_double = dtype('float64')


def register_type(name, gl_type, setter_postfix, size, numpy_type, setter_wrapper=default_post):
    items[gl_type] = (name, setter_postfix, size, numpy_type, setter_wrapper)


def get_type(gl_type):
    return items.get(gl_type, ('SomeSampler', '1iv', 4, np_int, default_post))


_mat_setter_wrapper = lambda func: (lambda count, value: func(count, GL_FALSE, value))

register_type('int', GL_INT, '1iv', 4, np_int)
register_type('float', GL_FLOAT, '1fv', 4, np_float)
register_type('uint', GL_UNSIGNED_INT, '1uiv', 4, np_uint)
register_type('double', GL_BOOL, '1dv', 8, np_double)

register_type('vec2', GL_FLOAT_VEC2, '2fv', 4 * 2, np_float)
register_type('vec3', GL_FLOAT_VEC3, '3fv', 4 * 3, np_float)
register_type('vec4', GL_FLOAT_VEC4, '4fv', 4 * 4, np_float)

register_type('dvec2', GL_DOUBLE_VEC2, '2dv', 8 * 2, np_double)
register_type('dvec3', GL_DOUBLE_VEC3, '3dv', 8 * 3, np_double)
register_type('dvec4', GL_DOUBLE_VEC4, '4dv', 8 * 4, np_double)

register_type('ivec2', GL_INT_VEC2, '2iv', 4 * 2, np_int)
register_type('ivec3', GL_INT_VEC3, '3iv', 4 * 3, np_int)
register_type('ivec4', GL_INT_VEC4, '4iv', 4 * 4, np_int)

register_type('uvec2', GL_UNSIGNED_INT_VEC2, '2uiv', 4 * 2, np_uint)
register_type('uvec3', GL_UNSIGNED_INT_VEC3, '3uiv', 4 * 3, np_uint)
register_type('uvec4', GL_UNSIGNED_INT_VEC4, '4uiv', 4 * 4, np_uint)

register_type('mat2', GL_FLOAT_MAT2, 'Matrix2fv', 4 * 2 * 2, np_float, _mat_setter_wrapper)
register_type('mat3', GL_FLOAT_MAT3, 'Matrix3fv', 4 * 3 * 3, np_float, _mat_setter_wrapper)
register_type('mat4', GL_FLOAT_MAT4, 'Matrix4fv', 4 * 4 * 4, np_float, _mat_setter_wrapper)
register_type('mat2x3', GL_FLOAT_MAT2x3, 'Matrix2x3fv', 4 * 2 * 3, np_float, _mat_setter_wrapper)
register_type('mat2x4', GL_FLOAT_MAT2x4, 'Matrix2x4fv', 4 * 2 * 4, np_float, _mat_setter_wrapper)
register_type('mat3x2', GL_FLOAT_MAT3x2, 'Matrix3x2fv', 4 * 3 * 2, np_float, _mat_setter_wrapper)
register_type('mat3x4', GL_FLOAT_MAT3x4, 'Matrix3x4fv', 4 * 3 * 4, np_float, _mat_setter_wrapper)
register_type('mat4x2', GL_FLOAT_MAT4x2, 'Matrix4x2fv', 4 * 4 * 2, np_float, _mat_setter_wrapper)
register_type('mat4x3', GL_FLOAT_MAT4x3, 'Matrix4x3fv', 4 * 4 * 3, np_float, _mat_setter_wrapper)

register_type('dmat2', GL_DOUBLE_MAT2, 'Matrix2dv', 8 * 2 * 2, np_double, _mat_setter_wrapper)
register_type('dmat3', GL_DOUBLE_MAT3, 'Matrix3dv', 8 * 3 * 3, np_double, _mat_setter_wrapper)
register_type('dmat4', GL_DOUBLE_MAT4, 'Matrix4dv', 8 * 4 * 4, np_double, _mat_setter_wrapper)
register_type('dmat2x3', GL_DOUBLE_MAT2x3, 'Matrix2x3dv', 8 * 2 * 3, np_double, _mat_setter_wrapper)
register_type('dmat2x4', GL_DOUBLE_MAT2x4, 'Matrix2x4dv', 8 * 2 * 4, np_double, _mat_setter_wrapper)
register_type('dmat3x2', GL_DOUBLE_MAT3x2, 'Matrix3x2dv', 8 * 3 * 2, np_double, _mat_setter_wrapper)
register_type('dmat3x4', GL_DOUBLE_MAT3x4, 'Matrix3x4dv', 8 * 3 * 4, np_double, _mat_setter_wrapper)
register_type('dmat4x2', GL_DOUBLE_MAT4x2, 'Matrix4x2dv', 8 * 4 * 2, np_double, _mat_setter_wrapper)
register_type('dmat4x3', GL_DOUBLE_MAT4x3, 'Matrix4x3dv', 8 * 4 * 3, np_double, _mat_setter_wrapper)
