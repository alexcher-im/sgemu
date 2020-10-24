from ctypes import c_int

from openal.alc import *

ALC_HRTF = 6546


class AudioContext:
    def __init__(self, device=None, args=(ALC_HRTF, 1), use=True):
        if args is not None:
            args = (c_int * (len(args) + 1))(*(c_int(arg) for arg in args), c_int(0))
        self.device = alcOpenDevice(device, )
        self.context = alcCreateContext(self.device, args)
        self.active_listener = None
        if use:
            self.use()

    def use(self):
        alcMakeContextCurrent(self.context)

    def __del__(self):
        alcDestroyContext(self.context)
        alcCloseDevice(self.device)
