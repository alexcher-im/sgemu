from glfw.GLFW import *
# import glfw
from OpenGL.GL import *

from .framebuffer import FrameBuffer

import numpy as np
from timeit import default_timer
import time


class WindowFrameBuffer(FrameBuffer):
    def __init__(self, window, width, height):
        super(WindowFrameBuffer, self).__new__(WindowFrameBuffer)
        self.width, self.height = width, height
        self.depth_buffer = None
        self.stencil_depth_buffer = None
        self.color_buffers = []
        self.buffer_id = 0
        self.window = window
        self.set_viewport(width, height)
        self.clear_mask = GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT

    def add_depth_buffer(self, depth_buffer=None):
        pass

    def finish(self):
        glfwSwapBuffers(self.window.window)
        self.clear()

    def __del__(self):
        pass


class Window:
    def __init__(self, res=(800, 600), resize=True, title='LearnOpenGL', version=(4, 3), alpha=False,
                 cursor_lock=True, depth_testing=True):
        glfwInit()
        # setting up glfw base
        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, version[0])
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, version[1])
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE)
        # glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_COMPAT_PROFILE)
        if not resize:
            glfwWindowHint(GLFW_RESIZABLE, GL_FALSE)

        # creating glfw window object
        self.window = glfwCreateWindow(*res, title, None, None)
        self.setup_opengl_context()
        self.framebuffer = WindowFrameBuffer(self, *glfwGetFramebufferSize(self.window))

        # setting callbacks
        self._user_resize_callback = lambda window, width, height: True
        self._user_key_callback = lambda window, key, scancode, action, mode: True
        self._user_key_array_callback = lambda keys, dt: True
        glfwSetWindowSizeCallback(self.window, self._on_resize)
        glfwSetKeyCallback(self.window, self._on_keyboard_key)
        self.pressed_keys = np.array([False] * 1024, 'bool')

        self.framebuffer.set_clear_color((0.2, 0.3, 0.3, 1.0))

        if depth_testing:
            glEnable(GL_DEPTH_TEST)
        if alpha:
            self.enable_blending()  # move this from this class
        if cursor_lock:
            self.set_cursor_lock()

    def setup_opengl_context(self):
        glfwMakeContextCurrent(self.window)

    def set_key_callback(self, func):
        """
        Func params:

        GLFWwindow window
               int key
               int scancode
               int action
               int mode
        """
        self._user_key_callback = func

    def set_mouse_move_callback(self, func):
        """
        Func params:

        GLFWwindow window
             float xpos
             float ypos
        """
        glfwSetCursorPosCallback(self.window, func)

    def set_mouse_click_callback(self, func):
        """
        Func params:

        GLFWindow window
              int button
              int action
              int mods
        """
        glfwSetMouseButtonCallback(self.window, func)

    def set_resize_callback(self, func):
        """
        Func params:

        GLFWwindow window
               int width
               int height
        """
        self._user_resize_callback = func

    def set_key_array_handler(self, func):
        """
        Func params:

        ndarray keys
          float delta_time
        """
        self._user_key_array_callback = func

    def set_scroll_callback(self, func):
        """
        Func params:

        GLFWwindow window
             float xoffset
             flaot yoffset
        """
        glfwSetScrollCallback(self.window, func)

    def _on_resize(self, window, width, height):
        self.framebuffer.width, self.framebuffer.height = width, height
        self.framebuffer.set_viewport(self.framebuffer.width, self.framebuffer.height)
        self._user_resize_callback(window, width, height)

    def _on_keyboard_key(self, window, key, scancode, action, mode):
        if action == GLFW_PRESS:
            self.pressed_keys[key] = True
        elif action == GLFW_RELEASE:
            self.pressed_keys[key] = False
        self._user_key_callback(window, key, scancode, action, mode)

    @staticmethod
    def enable_blending():
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def set_cursor_lock(self, mode=True):
        glfwSetInputMode(self.window, GLFW_CURSOR, GLFW_CURSOR_DISABLED if mode else GLFW_CURSOR_NORMAL)

    def poll_key_array(self):
        self._user_key_array_callback(self.pressed_keys, 1/60)  # todo remove delta time

    def run_loop(self, draw_func, fps=60):
        # setting timing values
        delay = 1 / fps if fps > 0 else 1.0

        # adding global vars to local scope
        sleep = time.sleep if fps > 0 else lambda t: None
        timer = default_timer
        max_func = max
        window = self.window
        should_close = glfwWindowShouldClose
        poll_events = glfwPollEvents
        poll_key_array_func = self._user_key_array_callback
        keys_array = self.pressed_keys
        swap_buffers = glfwSwapBuffers

        # main drawing loop
        start = timer()
        while not should_close(window):
            delta_time = timer() - start
            start = timer()

            # polling events and drawing everything
            poll_events()
            poll_key_array_func(keys_array, delta_time)
            self.framebuffer.clear()
            draw_func(delta_time)
            swap_buffers(window)

            print('time: %.5fms' % ((timer() - start) * 1000), flush=True)
            sleep(max_func(delay - timer() + start, 0))
