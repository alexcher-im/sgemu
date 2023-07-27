from OpenGL.GL import GL_RGBA32F, GL_RGB32F, GL_RGB, GL_RGBA, GL_FLOAT, GL_RGB16F, GL_RGBA16F, glEnable, glDisable, \
    GL_DEPTH_TEST, GL_INT, GL_RGB8_SNORM, GL_CULL_FACE

from ...fx.shader.loader import Effect, Builder
from ...gl.framebuffer import FrameBuffer, ColorTextureBuffer, FB_NONE
from ...gl.shader import ShaderProgram
from ...lib.pathlib import get_rel_path
from ...model.model import RenderCompound, Material
from ..base import BaseRenderer, SecondPassRenderer
from ..scene import SceneRenderer
from ..chain import RenderChain
from ..uniformed import UniformedRenderer
from ..util import gen_screen_mesh


class GBuffer(ColorTextureBuffer):
    pass


class GBuffer4Float(GBuffer):
    TEX_INTERNAL_TYPE = GL_RGBA32F
    TEX_TYPE = GL_RGBA
    TEX_DATA_TYPE = GL_FLOAT


class GBuffer3Float(GBuffer):
    TEX_INTERNAL_TYPE = GL_RGB32F
    TEX_TYPE = GL_RGB
    TEX_DATA_TYPE = GL_FLOAT


class GBuffer4UInt(GBuffer):
    TEX_INTERNAL_TYPE = GL_RGBA
    TEX_TYPE = GL_RGBA


class GBuffer3Float16(GBuffer):
    TEX_INTERNAL_TYPE = GL_RGB16F
    TEX_TYPE = GL_RGB
    TEX_DATA_TYPE = GL_FLOAT


class GBuffer4Float16(GBuffer):
    TEX_INTERNAL_TYPE = GL_RGBA16F
    TEX_TYPE = GL_RGBA
    TEX_DATA_TYPE = GL_FLOAT


class GBuffer4Float32(GBuffer):
    TEX_INTERNAL_TYPE = GL_RGBA32F
    TEX_TYPE = GL_RGBA
    TEX_DATA_TYPE = GL_FLOAT


class GBuffer3UInt(GBuffer):
    pass


class GBuffer3Int(GBuffer):
    TEX_DATA_TYPE = GL_INT
    TEX_INTERNAL_TYPE = GL_RGB8_SNORM


class GeometryPassRenderer(BaseRenderer):
    def __init__(self):
        shader = Effect.from_file(get_rel_path(__file__, '../../fx/shader/fx/template/base'))
        shader.insert(Effect.from_file(get_rel_path(__file__, '../../fx/shader/fx/transformation/mvp')))
        shader.insert(Effect.from_file(get_rel_path(__file__, '../../fx/shader/fx/template/deferred/geom')))
        builder = Builder(shader)
        self.shader_prog = ShaderProgram(builder.vert_str, builder.frag_str)
    
    def draw(self, data, out_fbo):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        super(GeometryPassRenderer, self).draw(out_fbo, data)
        glDisable(GL_CULL_FACE)
        glDisable(GL_DEPTH_TEST)


class LightPassRenderer(SecondPassRenderer):
    def __init__(self):
        vert_path = get_rel_path(__file__, '..', '..', 'shaders', 'gbuffers', 'light_main.vsh.glsl')
        frag_path = get_rel_path(__file__, '..', '..', 'shaders', 'gbuffers', 'light_main.fsh.glsl')
        self.shader_prog = ShaderProgram.from_files(vert_path, frag_path)

        self.fbo = FrameBuffer(800, 600, [GBuffer4Float,  # positions + shininess
                                          GBuffer3Int,    # normals
                                          GBuffer3UInt    # diffuse + specular
                                          ], FB_NONE, FB_NONE)
        # todo do not hardcode resolution
        self.meshes = ()

    def on_created_uniformed(self, uniformed):
        arr_data = [(buf, uniformed.sampler_data[name].bind_index)
                    for buf, name in zip(self.fbo.color_buffers, ('pos_shin', 'normal', 'albedo'))]
        self.meshes = (RenderCompound(gen_screen_mesh(), Material(arr_data)), )

    def draw(self, out_fbo, data):
        super(LightPassRenderer, self).draw(out_fbo, data)
        self.fbo.clear()


class DeferredRendererPreset(RenderChain):
    def __init__(self, scene):
        geom = SceneRenderer(scene, UniformedRenderer(GeometryPassRenderer()))
        light = SceneRenderer(scene, UniformedRenderer(LightPassRenderer()))
        super(DeferredRendererPreset, self).__init__(geom, light)
