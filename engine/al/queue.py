from openal.al import *
from .buffer import SoundBuffer


# it's only a looped queue
class Queue:
    def __init__(self, buffer_count=2, generator=None, sample_rate=44100, channels=2):
        self.source = None
        self.generator = generator
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffers = [SoundBuffer() for _ in range(buffer_count)]
        self.buffers_index = {buf.al_id: buf for buf in self.buffers}

    def set_generator(self, generator):
        self.generator = generator

    def on_bind_to_source(self, source):
        self.source = source
        source.queue_buffers(self.buffers)

    def fill_buffers(self):
        for buf in self.buffers:
            buf.fill(next(self.generator), self.sample_rate, self.channels)

    def update(self):
        count = self.source.get_i(AL_BUFFERS_PROCESSED)
        if count:
            buffer_list = []
            # updating buffers
            for buffer_id in self.source.unqueue_buffers(count):
                buffer = self.buffers_index[buffer_id]
                try:
                    data = next(self.generator)
                except StopIteration:
                    break
                buffer.fill(data, self.sample_rate, self.channels)
                buffer_list.append(buffer)
            # queueing buffers
            self.source.queue_buffers(buffer_list)

        if not self.source.is_playing():
            # resuming track if suddenly stopped
            if not self.source.get_queued_buffers_count():
                self.source.play()
            # clearing queue from source
            else:
                self.source.destination = None
                self.source = None
