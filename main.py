from timeit import default_timer as timer

import OpenGL
import numpy as np

from engine.gl.framebuffer import FB_TEXTURE_BUFFER
from engine.renderer.presets.fancy.convolution import DepthOfFieldRenderer
from engine.renderer.presets.fancy.light_volume import LightVolumeRenderer
from engine.renderer.presets.fancy.pbr_light import PbrLightPass

OpenGL.ERROR_CHECKING = False
from glm import vec3

from engine.lib import assimp
from engine.renderer.chain import RenderChain
from engine.renderer.presets.deferred import GBuffer4Float16
from engine.renderer.presets.fancy.bloom import Bloom
from engine.renderer.presets.fancy.coloring import GammaCorrectionEffect, LuminanceBasedReinhardToneMappingEffect
from engine.renderer.presets.fancy.normal import NormalMapping
from engine.renderer.scene import SceneRenderer
from engine.renderer.uniformed import UniformedRenderer
from engine.scene.scene import Scene
from engine.scene.game_object import GameObject, DirectedGameObject
from engine.scene.components.camera import CameraComponent
from engine.scene.components.light import SpotLightComponent, AreaLightComponent
from engine.scene.components.render import RenderComponent
from engine.scene.components.sound import SoundListenerComponent, SoundSourceComponent
from engine.sound.sound import CachedSound
from engine.sound.stream import StreamingSound
from engine.model.assimp_loader import load_model
from engine.gl.window import Window
from engine.timing.game import GameTimingManager
from glfw.GLFW import *
import glm

cursor_pos = glm.vec2(0, 0)


def make_renderer(scene, size):
    global lens_blur

    normal = SceneRenderer(scene, UniformedRenderer(NormalMapping()))
    light = SceneRenderer(scene, UniformedRenderer(PbrLightPass(*size)))
    light.uniformed.src_renderer.fbo.add_depth_buffer(FB_TEXTURE_BUFFER)

    volumetric = SceneRenderer(scene, UniformedRenderer(LightVolumeRenderer(
        *size,
        light.uniformed.src_renderer.fbo.color_buffers[0],
        (GBuffer4Float16, )))
    )
    bloom = Bloom(*size, (GBuffer4Float16,), (), blur_points=301,
                  num_passes=1, mix_cf=0.02, light_limit=1)#, mix_cf=15, light_limit=9)

    lens_blur = DepthOfFieldRenderer('res/kernel/lens_blur_phonecam1.png', *size, light.uniformed.src_renderer.fbo.depth_buffer, (GBuffer4Float16,))
    bloom_gamma = Bloom(*size, (GBuffer4Float16,), (LuminanceBasedReinhardToneMappingEffect, GammaCorrectionEffect),
                        num_passes=0)#, mix_cf=15, light_limit=9)

    return None, RenderChain(normal, light, bloom, volumetric, lens_blur, bloom_gamma)


def key_array_callback(keys, dt):
    speed = 0.9 * dt
    rotation_speed = 2.1
    if keys[GLFW_KEY_ESCAPE]:
        timing.should_execute = False
    if keys[GLFW_KEY_LEFT_SHIFT]:
        speed *= 10
    if keys[GLFW_KEY_LEFT_CONTROL]:
        speed *= 100
    if keys[GLFW_KEY_W]:
        cam_dir = cam.direction
        cam.move_by_vector(glm.normalize(glm.vec3(cam_dir.x, 0, cam_dir.z)) * speed)
    if keys[GLFW_KEY_A]:
        cam.move_sideways(0, speed)
    if keys[GLFW_KEY_S]:
        cam_dir = cam.direction
        cam.move_by_vector(glm.normalize(glm.vec3(cam_dir.x, 0, cam_dir.z)) * -speed)
    if keys[GLFW_KEY_D]:
        cam.move_sideways(1, speed)
    if keys[GLFW_KEY_UP]:
        cam.move_by_vector(glm.vec3(0, speed, 0))
    if keys[GLFW_KEY_DOWN]:
        cam.move_by_vector(glm.vec3(0, -speed, 0))

    if keys[GLFW_KEY_G]:
        cam.add_angles(dt * rotation_speed)
    if keys[GLFW_KEY_F]:
        cam.add_angles(-dt * rotation_speed)
    if keys[GLFW_KEY_B]:
        cam.add_angles(pitch=-dt * rotation_speed)
    if keys[GLFW_KEY_N]:
        cam.add_angles(pitch=dt * rotation_speed)
    if keys[GLFW_KEY_E]:
        cam.add_angles(roll=-dt)
    if keys[GLFW_KEY_Q]:
        cam.add_angles(roll=dt)
    if keys[GLFW_KEY_T]:
        lens_blur.set_near_cut(lens_blur.near_cut - 0.001 * speed)
    if keys[GLFW_KEY_Y]:
        lens_blur.set_near_cut(lens_blur.near_cut + 0.001 * speed)

    if __debug__:
        print('camera at', tuple(cam.pos), 'facing', tuple(cam.direction), 'with fov', cam.components[0].fov)


def mouse_callback(_, xpos, ypos):
    global cursor_pos
    sensitivity = 0.004
    curr_pos = glm.vec2(xpos, ypos)
    offset = (curr_pos - cursor_pos) * sensitivity
    cursor_pos = curr_pos
    cam.add_angles(offset.x, -offset.y)


window = Window(depth_testing=False, alpha=False)
window.set_key_array_handler(key_array_callback)
window.set_mouse_move_callback(mouse_callback)

import OpenGL.GL
print('Vendor: %s' % OpenGL.GL.glGetString(OpenGL.GL.GL_VENDOR).decode())
print('Opengl version: %s' % OpenGL.GL.glGetString(OpenGL.GL.GL_VERSION).decode())
print('GLSL Version: %s' % OpenGL.GL.glGetString(OpenGL.GL.GL_SHADING_LANGUAGE_VERSION).decode())
print('Renderer: %s' % OpenGL.GL.glGetString(OpenGL.GL.GL_RENDERER).decode())

assimp.USE_C_LOADER = False

scene = Scene()
# renderer = DeferredRendererPreset(scene)
start = timer()
_, renderer = make_renderer(scene, (window.framebuffer.width, window.framebuffer.height))
print('renderers took:', timer() - start)
sound = StreamingSound.from_file('nyancat.mp3', looped=True)
# todo `looped` arg for CachedSound
# models_to_load = ('Lantern', 'Suzanne')

cam = DirectedGameObject(scene.root_obj, components=[
    CameraComponent(render_target=window.framebuffer, activate=True, fov=90),
    SoundListenerComponent()])

# GameObject(scene.root_obj, components=[
#     RenderComponent(model=load_model(r'glTF-Sample-Models\2.0\%s\glTF\%s.gltf' % (f, f)),
#                     renderer=renderer).transform.move((10 * i, 0, 0)) for i, f in enumerate(models_to_load)])

GameObject(scene.root_obj, components=[
    RenderComponent(model=load_model(r'glTF-Sample-Models\2.0\Sponza\glTF\Sponza.gltf'), renderer=renderer).transform.scale(50),
    ])

GameObject(scene.root_obj, components=[
    # negative-luminance light
    # SpotLightComponent(diffuse_color=(-10, -10, -10), direction=(0, 0, 1), cut_off=50),
    SoundSourceComponent()],
           pos=(3, 10, 8)).components[-1].play(sound)

GameObject(scene.root_obj, components=[
    SpotLightComponent(diffuse_color=(vec3(201, 52, 124) / 255) ** 2.2 * 20, direction=(-0.3, 0, -1), cut_off=30),
    SpotLightComponent(diffuse_color=(vec3(33, 86, 184) / 255) ** 2.2 * 20, direction=(-1, 0, -1), cut_off=25)
], pos=(3, 10, 8))

GameObject(scene.root_obj, components=[
    SpotLightComponent(diffuse_color=(vec3(255, 250, 219) / 255) ** 2.2 * 10, direction=(-0.445, -0.3, -0.843), cut_off=15),

    # orange-purple area lights:
    AreaLightComponent(color=(vec3(262, 182, 30) / 255) ** 2.2 * 4 * 10, intensity=1,
                       points=(vec3(0, 100, 0), vec3(400, 100, 0), vec3(400, 200, 0), vec3(0, 200, 0))),
    AreaLightComponent(color=(vec3(166, 71, 255) / 255) ** 2.2 * 6,
                       points=(vec3(0, 100, 0), vec3(-400, 100, 0), vec3(-400, 200, 0), vec3(0, 200, 0))),

    # blue-pink area lights:
    #AreaLightComponent(color=(vec3(33, 86, 184) / 255) ** 2.2 * 50,
    #                  points=(vec3(0, 100, 0), vec3(0, 100, 100), vec3(0, 200, 100), vec3(0, 200, 0))),
    #AreaLightComponent(color=(vec3(201, 52, 124) / 255) ** 2.2 * 50,
    #                  points=(vec3(0, 100, 0), vec3(100, 100, 0), vec3(100, 200, 0), vec3(0, 200, 0))),

    # red area light:
    # AreaLightComponent(color=(vec3(255, 51, 51) / 255) ** 2.2 * 20,
    #                    points=(vec3(0, 100, 0), vec3(0, 100, 400), vec3(0, 200, 400), vec3(0, 200, 0))),

    # white-green area lights:
    #AreaLightComponent(color=(vec3(71, 255, 142) / 255) ** 2.2 * 2,
    #                   points=(vec3(0, 100, 0), vec3(0, 100, 400), vec3(0, 200, 400), vec3(0, 200, 0))),
    #AreaLightComponent(color=(vec3(255, 250, 219) / 255) ** 2.2 * 3,
    #                   points=(vec3(0, 0, 0), vec3(100, 0, 0), vec3(100, 100, 0), vec3(0, 100, 0))),
], pos=(95, 48, 0.41))


scene.static_data['comm_light.ambient_color'] = vec3(0.01, 0.01, 0.01) * 1  # todo rename to ambient_color when shader building done
scene.static_data['fog.color'] = vec3(1, 1, 1)  # todo move fog to external RendererDependency
scene.static_data['fog.start'] = 500
scene.static_data['fog.z_far'] = 5000
scene.static_data['metallic'] = 0
scene.static_data['roughness'] = 0.8
scene.static_data['ao'] = 1
print('initialising done')

timing = GameTimingManager(window)
# timing.set_fps(0)
timing.delay = 0
timing.run_with_strict_delta(scene)
