from audioread import audio_open

from .sound import BaseSound
from ..al.queue import Queue

BUFFER_SIZE = 1024 ** 2


def get_looped_gen(filename, buf_size):
    while True:
        fp = audio_open(filename)
        yield from fp.read_data(buf_size)


class StreamingSound(BaseSound):
    @classmethod
    def from_file(cls, filename, buffer_size=None, buffer_count=2, looped=False):
        if buffer_size is None:
            buffer_size = BUFFER_SIZE
        getter = (lambda source: get_looped_gen(filename, buffer_size)) if looped else \
            (lambda source: audio_open(filename).read_data(buffer_size))
        audio = audio_open(filename)
        return cls(getter, audio.samplerate, audio.channels, buffer_count)

    def __init__(self, stream_getter, sample_rate, channels, buffer_count=2):
        self.audio_rate = sample_rate
        self.channels = channels
        self.buffer_count = buffer_count
        self.stream_getter = stream_getter

    def bind(self, source):
        queue = Queue(self.buffer_count, self.stream_getter(source), self.audio_rate, self.channels)
        queue.fill_buffers()
        source.set_destination(queue)
