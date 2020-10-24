from ctypes import POINTER, c_uint
from openal.al import *


class SoundBuffer:
    def __init__(self):
        int_ptr = POINTER(c_uint)(c_uint(0))
        alGenBuffers(1, int_ptr)
        self.al_id = int_ptr[0]

    def on_bind_to_source(self, source):
        source.set_buffer(self.al_id)

    def fill(self, data, sample_rate=44100, channels=2):
        al_format = [AL_FORMAT_MONO16, AL_FORMAT_STEREO16][channels - 1]
        data = bytes(data)
        alBufferData(self.al_id, al_format, data, len(data), sample_rate)

    def update(self):
        pass
