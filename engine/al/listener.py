import glm
from openal.al import *


class SoundListener:
    def __init__(self, context, use=True):
        self.context = context
        self.direction = glm.mat2x3(glm.vec3(1, 0, 0), glm.vec3(0, 1, 0))
        self.velocity = glm.vec3(0)
        self.gain = 1.0
        self.position = glm.vec3(0)
        if use:
            self.use()

    def set_direction(self, direction, upward=glm.vec3(0, 1, 0)):
        self.direction = glm.mat2x3(glm.normalize(glm.vec3(direction)),
                                    glm.normalize(glm.vec3(upward)))
        if self.context.active_listener == self:
            alListenerfv(AL_ORIENTATION, glm.value_ptr(self.direction))

    def set_position(self, pos):
        self.position = glm.vec3(pos)
        if self.context.active_listener == self:
            alListenerfv(AL_POSITION, glm.value_ptr(self.position))

    def set_velocity(self, velocity):
        self.velocity = glm.vec3(velocity)
        if self.context.active_listener == self:
            alListenerfv(AL_VELOCITY, glm.value_ptr(self.velocity))

    def set_gain(self, gain):
        self.gain = gain
        if self.context.active_listener == self:
            alListenerf(AL_GAIN, self.gain)

    def use(self):
        if self.context.active_listener == self:
            return
        self.context.active_listener = self
        alListenerfv(AL_ORIENTATION, glm.value_ptr(self.direction))
        alListenerf(AL_GAIN, self.gain)
        alListenerfv(AL_VELOCITY, glm.value_ptr(self.velocity))
        alListenerfv(AL_POSITION, glm.value_ptr(self.position))
