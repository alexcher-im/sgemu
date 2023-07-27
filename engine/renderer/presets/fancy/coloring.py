from collections import namedtuple

from ...base import SecondPassRenderer
from ....gl.shader import ShaderProgram


class BaseEffect:
    elements = ()


Uniform = namedtuple('Uniform', 'name type default handler')
UniformHandler = namedtuple('UniformHandler', 'name type function')
Code = namedtuple('Code', 'code resulting_pixel_name')
# Uniform - info about uniform in shader
# UniformHandler - info about setting values outside the shader

EffectSetterInfo = namedtuple('EffectSetterTuple', 'name function type default')


def merge_code(src, effects, color_out_name):
    uniforms = []
    uniform_setters = {}
    main = []

    for effect in effects:
        for item in effect.elements:

            if isinstance(item, Uniform):
                uniforms.append('uniform %s %s;' % (item.type, item.name))
                handler = item.handler
                uniform_setters[handler.name] = EffectSetterInfo(item.name, handler.function, handler.type,
                                                                 item.default)

            elif isinstance(item, Code):
                main.append(item.code.replace(item.resulting_pixel_name, color_out_name))

            else:
                raise ValueError('Cannot handle effect part:', item)

    uniforms = '\n'.join(uniforms)
    main = '\n'.join(main)
    return src.replace('/* uniforms */', uniforms).replace('/* main */', main), uniform_setters


class EffectSupporter(SecondPassRenderer):
    _vert_shader = ''
    _frag_shader = ''
    _frag_out_color_name = ''

    def __init__(self, effects):
        new_frag, setters = merge_code(self._frag_shader, effects, self._frag_out_color_name)
        self.shader_prog = ShaderProgram(self._vert_shader, new_frag, use=True)

        self.effect_value_setters = {}
        for name, setter in setters.items():
            curr_setter = self.shader_prog.get_uniform_setter(setter.name, setter.type)
            self.effect_value_setters[name] = lambda values: curr_setter(setter.function(values))
            curr_setter(setter.function(setter.default))

    def set_effect_value(self, name, value):
        self.shader_prog.use()
        self.effect_value_setters[name](value)


class GammaCorrectionEffect(BaseEffect):
    elements = (
        Uniform('rev_gamma', 'float', 2.2, UniformHandler('gamma', '1f', lambda gamma: 1 / gamma)),
        Code('vec3 lin_part = out_color.xyz * 12.92;'
             'vec3 quad_part = pow(out_color.xyz * 1.055, vec3(1/2.4)) - 0.055;'
             'out_color.xyz = mix(lin_part, quad_part, greaterThan(out_color.xyz, vec3(0.0031308)));'
             #'out_color = pow(out_color, vec4(vec3(rev_gamma), 1));'
             '', 'out_color')
    )


class ReinhardToneMappingEffect(BaseEffect):
    elements = (
        Code('out_color.xyz = abs(out_color.xyz) / (out_color.xyz + 1);', 'out_color'),
    )


class LuminanceBasedReinhardToneMappingEffect(BaseEffect):
    elements = (
        Code(#'float curr_luminance = max(max(out_color.x, max(out_color.y, out_color.z)), 0);'
             'float curr_luminance = dot(abs(out_color.xyz), vec3(0.2126, 0.7152, 0.0722));'
             'float scale_factor = 1 / (curr_luminance + 1);'
             'out_color.xyz *= scale_factor;', 'out_color'),
    )


class FilmicToneMappingEffect(BaseEffect):
    elements = (
        Code(#'float curr_luminance = max(max(out_color.x, max(out_color.y, out_color.z)), 0);'
             'vec3 X = max(vec3(0.0), out_color.xyz - 0.004);'
             'vec3 result = (X * (6.2 * X + 0.5)) / (X * (6.2 * X + 1.7) + 0.06);'
             'out_color.xyz = pow(result, vec3(2.2));', 'out_color'),
    )


class ExposureEffect(BaseEffect):
    elements = (
        Uniform('exposure', 'float', 1, UniformHandler('exposure', '1f', lambda exposure: exposure)),
        Code('out_color.xyz = vec3(1) - exp(-out_color.xyz * exposure);', 'out_color')
    )


class PosterizationEffect(BaseEffect):
    elements = (
        Uniform('power', 'float', 16, UniformHandler('posterization_power', '1f', lambda power: power)),
        Code('out_color.xyz = round(out_color.xyz * 255 / power) * power / 255;', 'out_color')
    )
