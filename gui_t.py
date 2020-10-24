from timeit import default_timer as timer

from glm import vec4

from engine.gl import Window, glfwSwapBuffers, GLFW_MOUSE_BUTTON_LEFT, GLFW_PRESS, GLFW_RELEASE, glGetIntegerv, \
    GL_MAX_UNIFORM_BLOCK_SIZE, GL_MAX_VERTEX_UNIFORM_VECTORS
from engine.gui.adaptive import AlignModes, ResizeModes
from engine.gui.base import BaseElement, cvec
from engine.gui.elements.image import ImageElement
from engine.gui.elements.text import TextElement
from engine.gui.renderer import UIRenderer
from engine.lib.text_renderer import LineAlignmentMode

python_man = open('python_man.txt').read()


window = Window((954, 540), cursor_lock=False, depth_testing=False, alpha=True)
print(glGetIntegerv(GL_MAX_UNIFORM_BLOCK_SIZE))
print(glGetIntegerv(GL_MAX_VERTEX_UNIFORM_VECTORS))
renderer = UIRenderer(window.framebuffer)
root = renderer.root


ImageElement(root, picture='res/yd.jpg', resize_act=ResizeModes.keep_ratio_oversize, align_act=AlignModes.center)
form = BaseElement(root, size=(300, 200), resize_act=ResizeModes.keep, align_act=AlignModes.center)
apple = ImageElement(form, align_act=AlignModes.center, resize_act=ResizeModes.keep_ratio_fit, picture='res/yn.jpg', set_orig_size=True)
img = ImageElement(root, picture='res/sv.jpg', set_orig_size=True, resize_act=ResizeModes.keep_ratio_fit)
text = TextElement(img, fonts=None, color=(0, 0, 255, 255), text=python_man, align_act=AlignModes.center, line_align=LineAlignmentMode.center)
# checkbox = SgCheckbox(text, size=(300, 20), align_act=AlignModes.center)
# RoundedRect(root, border_radius=2, toughness=1)
# exit()


def resize_func(glfw_window, width, height):
    start = timer()
    root.set_size((width, height))
    print('resizing took', timer() - start)
    renderer.draw()
    glfwSwapBuffers(glfw_window)


def apple_on_aim(elem, *_):
    elem.render_data.color = vec4(255, 10, 10, 255) / 255


def apple_on_leave(elem, *_):
    elem.render_data.color = vec4(255) / 255


def window_mouse_move_event(_, x, y):
    root.event_manager.on_mouse_move_event(cvec(x, y))


def window_mouse_button_event(_, button, action, mods):
    if action == GLFW_PRESS:
        root.event_manager.on_mouse_press_event(0 if button == GLFW_MOUSE_BUTTON_LEFT else 1)
    elif action == GLFW_RELEASE:
        root.event_manager.on_mouse_release_event(0 if button == GLFW_MOUSE_BUTTON_LEFT else 1)


apple.event_manager.mouse_click_callback = apple_on_aim
apple.event_manager.mouse_release_callback = apple_on_leave
window.set_resize_callback(resize_func)
window.set_mouse_move_callback(window_mouse_move_event)
window.set_mouse_click_callback(window_mouse_button_event)
window.run_loop(lambda _: renderer.draw())
