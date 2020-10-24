from ..al.context import AudioContext as ALContext
from ..al.source import SoundSource


class AudioContext(ALContext):
    def __init__(self, cached_sources=30, *args, **kwargs):
        super(AudioContext, self).__init__(*args, **kwargs)
        self.source_cache_len = cached_sources
        self._sources = [SoundSource() for _ in range(cached_sources)]

    def get_free_source(self):
        try:
            return self._sources.pop(-1)
        except IndexError:
            return SoundSource()

    def push_source(self, source):
        if len(self._sources) < self.source_cache_len:
            self._sources.append(source)
