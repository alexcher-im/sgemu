from audioread import audio_open

from ..al.buffer import SoundBuffer


class BaseSound:
    def bind(self, source):
        pass


class CachedSound(BaseSound):
    @classmethod
    def from_file(cls, filename):
        stream = audio_open(filename)
        data = b''.join(stream.read_data())
        return cls(data, stream.samplerate, stream.channels)

    def __init__(self, data, sample_rate=44100, channels=2):
        self.buffer = SoundBuffer()
        self.buffer.fill(data, sample_rate, channels)

    def bind(self, source):
        source.set_destination(self.buffer)
