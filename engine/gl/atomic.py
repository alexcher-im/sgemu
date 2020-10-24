import numpy as np
from OpenGL.GL import GL_ATOMIC_COUNTER_BUFFER

from .base import BufferBase


class AtomicBuffer(BufferBase):
    GL_BUF_TYPE = GL_ATOMIC_COUNTER_BUFFER
    ARRAY_TYPE = 'uint32'

    def __init__(self, counters_num=1, *args, **kwargs):
        super(AtomicBuffer, self).__init__(data=np.zeros(counters_num, self.ARRAY_TYPE), *args, **kwargs)
        self.upload()
