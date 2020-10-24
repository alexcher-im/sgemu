from time import sleep as time_sleep
from timeit import default_timer as timer

from glfw.GLFW import glfwPollEvents

from .base import TimingManager
from ..event.tick import TickEvent


class GameTimingManager(TimingManager):
    def __init__(self, window):
        super(GameTimingManager, self).__init__()
        self.window = window

    def run(self, scene):
        self.should_execute = True
        sleep = time_sleep

        start = timer()
        while self.should_execute:
            # todo fully rewrite this timing system
            # todo add a new timing system, that holds delta time better
            delta_time = timer() - start
            start = timer()

            # polling events and drawing everything
            self.window.poll_key_array()
            glfwPollEvents()
            # todo this must be done by scene. make timing.draw() accept function it will call here, after polling events
            scene.event_manager.add_event(TickEvent(delta_time))
            scene.event_manager.poll_events()
            scene.draw()

            if __debug__:
                print('time: %.5fms' % ((timer() - start) * 1000), flush=True)
            self.tick_count += 1
            if self.delay:
                sleep(max(self.delay - timer() + start, 0))

    def run_with_strict_delta(self, scene):
        self.should_execute = True
        sleep = time_sleep

        start = timer()
        old_time = start
        # todo if window stays running for too long it will cause dt precision loss. fix
        while self.should_execute:
            dt = timer() - old_time
            old_time = timer()

            # polling events and drawing everything
            self.window.poll_key_array()
            glfwPollEvents()
            scene.event_manager.add_event(TickEvent(dt))
            scene.event_manager.poll_events()
            scene.draw()

            if __debug__:
                print('time: %.5fms' % ((timer() - old_time) * 1000), flush=True)
            # print(dt, 'sleeping for', self.delay - ((timer() - start) % self.delay))
            if self.delay:
                sleep((self.delay - ((timer() - start) % self.delay)))
