from ctypes import POINTER, c_int, c_uint

import glm
from openal.al import *


def setter_digit(function, parameter, cast=None):
    if cast:
        return lambda self, value: function(self.al_id, parameter, cast(value))
    return lambda self, value: function(self.al_id, parameter, value)


class SoundSource:
    # shit goes here
    set_pitch = setter_digit(alSourcef, AL_PITCH)
    set_gain = setter_digit(alSourcef, AL_GAIN)
    set_max_distance = setter_digit(alSourcef, AL_MAX_DISTANCE)
    set_rolloff_factor = setter_digit(alSourcef, AL_ROLLOFF_FACTOR)
    set_reference_distance = setter_digit(alSourcef, AL_REFERENCE_DISTANCE)
    set_min_gain = setter_digit(alSourcef, AL_MIN_GAIN)
    set_max_gain = setter_digit(alSourcef, AL_MAX_GAIN)
    set_cone_outer_gain = setter_digit(alSourcef, AL_CONE_OUTER_GAIN)
    set_cone_inner_angle = setter_digit(alSourcef, AL_CONE_INNER_ANGLE)
    set_cone_outer_angle = setter_digit(alSourcef, AL_CONE_OUTER_ANGLE)
    set_position = setter_digit(alSourcefv, AL_POSITION, lambda x: glm.value_ptr(glm.vec3(x)))
    set_velocity = setter_digit(alSourcefv, AL_VELOCITY, lambda x: glm.value_ptr(glm.vec3(x)))
    set_direction = setter_digit(alSourcefv, AL_DIRECTION, lambda x: glm.value_ptr(glm.normalize(glm.vec3(x))))
    set_source_relative = setter_digit(alSourcei, AL_SOURCE_RELATIVE)
    set_source_type = setter_digit(alSourcei, AL_SOURCE_TYPE)
    set_looping = setter_digit(alSourcei, AL_LOOPING)
    set_buffer = setter_digit(alSourcei, AL_BUFFER)
    set_source_state = setter_digit(alSourcei, AL_SOURCE_STATE)
    set_buffers_processed = setter_digit(alSourcei, AL_BUFFERS_PROCESSED)
    set_sec_offset = setter_digit(alSourcef, AL_SEC_OFFSET)
    set_sample_offset = setter_digit(alSourcef, AL_SAMPLE_OFFSET)
    set_byte_offset = setter_digit(alSourcef, AL_BYTE_OFFSET)

    def __init__(self):
        int_ptr = POINTER(c_uint)(c_uint(0))
        alGenSources(1, int_ptr)
        self.al_id = int_ptr[0]
        self.destination = None
        self.position = glm.vec3(0)

    # function wrappers
    def queue_buffers(self, buffers):
        memory = (c_uint * len(buffers))(*(c_uint(buf.al_id) for buf in buffers))
        alSourceQueueBuffers(self.al_id, len(buffers), memory)

    def unqueue_buffers(self, count: int):
        memory = (c_uint * count)(*(c_uint(0), ) * count)
        alSourceUnqueueBuffers(self.al_id, count, memory)
        return tuple(memory)

    def get_queued_buffers_count(self):
        return self.get_i(AL_BUFFERS_QUEUED)

    def is_playing(self):
        state = self.get_i(AL_SOURCE_STATE)
        return state == AL_PLAYING

    def get_i(self, parameter):
        memory = (c_int * 1)(c_int(0))
        alGetSourcei(self.al_id, parameter, memory)
        return memory[0]
    # end wrappers

    def set_destination(self, destination):
        self.destination = destination
        destination.on_bind_to_source(self)

    def update(self):
        if self.destination is not None:
            self.destination.update()

    def play(self):
        alSourcePlay(self.al_id)
