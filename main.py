import time
from timeit import default_timer as timer

import OpenGL

OpenGL.ERROR_CHECKING = False
from glm import vec3

from engine.lib import assimp
from engine.renderer.batch import RenderBatch
from engine.renderer.chain import RenderChain
from engine.renderer.presets.deferred import GBuffer4Float16
from engine.renderer.presets.fancy.bloom import Bloom
from engine.renderer.presets.fancy.coloring import GammaCorrectionEffect, ReinhardToneMappingEffect
from engine.renderer.presets.fancy.first import GeometryPassDefault
from engine.renderer.presets.fancy.light import LightPass
from engine.renderer.presets.fancy.normal import NormalMapping
from engine.renderer.scene import SceneRenderer
from engine.renderer.uniformed import UniformedRenderer
from engine.scene.scene import Scene
from engine.scene.game_object import GameObject, DirectedGameObject
from engine.scene.components.camera import CameraComponent
from engine.scene.components.light import SpotLightComponent
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
    geom = SceneRenderer(scene, UniformedRenderer(GeometryPassDefault()))
    normal = SceneRenderer(scene, UniformedRenderer(NormalMapping()))
    light = SceneRenderer(scene, UniformedRenderer(LightPass(*size)))
    bloom = Bloom(800, 600, (GBuffer4Float16,), (GammaCorrectionEffect, ReinhardToneMappingEffect),
                  num_passes=3, )
    RenderChain(geom, light, bloom)
    RenderBatch([(normal, light, True), (geom, light, True), (light, bloom, False), ])
    return RenderChain(geom, light, bloom), RenderChain(normal, light, bloom)


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

    light_go.pos = vec3(glm.sin(time.time()) * 100, 10, glm.cos(time.time()) * 100)
    light_comp.direction = vec3(0, 0, 0) - light_go.pos


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
models_to_load = ('Lantern', 'Suzanne')

cam = DirectedGameObject(scene.root_obj, components=[
    CameraComponent(render_target=window.framebuffer, activate=True, fov=90),
    SoundListenerComponent()])

GameObject(scene.root_obj, components=[
    RenderComponent(model=load_model(r'glTF-Sample-Models\2.0\%s\glTF\%s.gltf' % (f, f)),
                    renderer=renderer).transform.move((10 * i, 0, 0)) for i, f in enumerate(models_to_load)])

GameObject(scene.root_obj, components=[
    RenderComponent(model=load_model(r'glTF-Sample-Models\2.0\Sponza\glTF\Sponza.gltf'), renderer=renderer).transform.scale(50),
    ])

light_comp = SpotLightComponent(diffuse_color=(10, 4, 4), direction=(0, 0, -1), cut_off=60)
light_go = GameObject(scene.root_obj, components=[light_comp], pos=(3, 10, 8))
GameObject(scene.root_obj, components=[
    SpotLightComponent(diffuse_color=(-10, -10, -10), direction=(0, 0, 1), cut_off=50),
    SoundSourceComponent()],
           pos=(3, 10, 8)).components[-1].play(sound)


scene.static_data['comm_light.ambient_color'] = vec3(0.1, 0.1, 0.1)  # todo rename to ambient_color when shader building done
scene.static_data['fog.color'] = vec3(1, 1, 1)  # todo move fog to external RendererDependency
scene.static_data['fog.start'] = 500
scene.static_data['fog.z_far'] = 5000
print('initialising done')

timing = GameTimingManager(window)
# timing.set_fps(0)
timing.delay = 0
timing.run_with_strict_delta(scene)
