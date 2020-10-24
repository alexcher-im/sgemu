import numpy as np

from engine.lib.freetype_wrap import FTFace


class CachedFont:
    def __init__(self, ft: FTFace, cached_symbols=tuple(map(chr, range(0x20, 127)))):
        self.cached = {}
        self.cached_set = set()
        self.face = ft
        for char in cached_symbols:
            self._add_cached(char)

        self.line_gap = ft.face.size.height >> 6
        self.ascender = ft.face.size.ascender >> 6

    def _add_cached(self, char):
        glyph = self.face.get_symbol(char)
        self.cached[glyph.char] = glyph
        self.cached_set.add(glyph.char)

    def get_symbols(self, charset):
        # todo here can be some optimizations
        new_symbols = charset - self.cached_set
        return dict(self.cached, **self._get_glyphs(new_symbols))

    def _get_glyphs(self, chars):
        return {char: self.face.get_symbol(char) for char in chars}


class LineAlignmentMode:
    @staticmethod
    def left(_, __):
        return 0

    @staticmethod
    def right(curr_line_len: int, max_line_len: int):
        return max_line_len - curr_line_len

    @staticmethod
    def center(curr_line_len: int, max_line_len):
        return (max_line_len - curr_line_len) // 2


class BitmapFactory:
    class Word:
        def __init__(self, symbols):
            self.symbols = symbols
            self.f_height = max((f.font_height for f in symbols))
            self.f_ascender = max((f.font_ascender for f in symbols))
            # calculating length
            self.length = 0
            length = 0
            for _, __, length in self:
                pass
            self.length = length

        def pop_last(self):
            symbol = self.symbols.pop(-1)
            length = symbol.full_width
            if self.symbols:
                length += self.symbols[-1].get_kerning(symbol)
            self.length -= length
            return length

        # @wrap({'range': range, 'max': max, 'len': len})
        def __iter__(self):
            curr_offset = 0
            symbols = self.symbols
            for i in range(len(symbols) - 1):
                symbol = symbols[i]
                yield symbol, max(curr_offset + symbol.bearing.horizontal, 0), 0  # here endpoint isn't important
                # warning: kerning uses about 40% of all time. add option to disable it
                curr_offset += symbol.full_width + symbol.get_kerning(symbols[i + 1])

            if symbols:
                symbol = symbols[-1]
                curr_offset += symbol.bearing.horizontal
                yield symbol, max(curr_offset, 0), max(curr_offset, 0) + symbol.full_width

    class Line:
        def __init__(self, max_length):
            self.max_width = max_length
            self.words = []

            self.length = 0
            self.height = 0
            self.ascender = 0

        def add_word(self, word):
            if self.length + word.length >= self.max_width:
                return False
            self.words.append(word)
            self.length += word.length
            if word.f_height > self.height:
                self.height = word.f_height
            if word.f_ascender > self.ascender:
                self.ascender = word.f_ascender
            return True

        def decrease(self, value):
            self.length -= value

    def __init__(self, ft, cached_symbols=tuple(map(chr, range(0x20, 127))), align_mode=LineAlignmentMode.left):
        self.fonts = [CachedFont(face, cached_symbols) for face in ft]
        self.lcd = self.fonts[0].face.lcd
        self.color = self.fonts[0].face.color

        self.align_mode = align_mode

    @staticmethod
    def _get_indices(text, indices):
        if indices is None:  # like None
            indices = ((0, len(text) + 1), )
        elif not indices:  # like []
            raise ValueError("Indices field cannot be empty")
        elif isinstance(indices, int):
            indices = ((indices, len(text)), )
        elif len(indices[0]) == 1:  # like [(0, )]
            indices = ((indices[0], len(text)), )
        yield indices

        # ((0, 13), (1, 5), (0, 82))
        for index, count in indices:
            for _ in range(count):
                yield index

    def get_map(self, text: str, max_width: int, indices=None):
        indices = self._get_indices(text, indices)
        total_symbols = self._cache_pass(text, next(indices))

        if self.lcd:
            max_width *= 3

        full_lines = self._split_pass(total_symbols, text, max_width, indices)
        arr = self._blit_pass(full_lines)

        if self.lcd:
            arr = arr.reshape((arr.shape[0], arr.shape[1] // 3, 3))
        return arr

    def _cache_pass(self, text, indices):
        fonts = [{} for _ in range(len(self.fonts))]
        curr_text_index = 0
        for font_index, size in indices:
            curr_text_part = text[curr_text_index:curr_text_index + size]
            fonts[font_index].update(self.fonts[font_index].get_symbols(set(curr_text_part)))
            curr_text_index += size
        return fonts

    def _split_pass(self, total_symbols, text, max_width, indices=None):
        # split pass
        full_lines = []
        for line in text.split('\n'):
            # special case for empty line
            if not line:
                line = self.Line(max_width)
                line.height = next(iter(total_symbols[next(indices)].values())).font_height
                full_lines.append(line)
                continue

            full_lines.append(self.Line(max_width))

            # making word objects
            words_line = []
            for word_str in line.split(' '):
                curr_word = [total_symbols[index][char] for char, index in zip(word_str, indices)]
                curr_word.append(total_symbols[next(indices)][' '])
                words_line.append(curr_word)
            words = tuple(map(self.Word, words_line))

            # wrapping words
            for word in words:
                if not full_lines[-1].add_word(word):  # can't fit into existing size
                    '''if full_lines[-1].words:
                        full_lines[-1].decrease(full_lines[-1].words[-1].pop_last())'''
                    new_line = self.Line(max_width)
                    new_line.add_word(word)
                    full_lines.append(new_line)
        if full_lines[-1].words:
            full_lines[-1].decrease(full_lines[-1].words[-1].pop_last())
        return full_lines

    def _allocate_array(self, full_lines):
        _max_width = max(full_lines, key=lambda x: x.length).length + 1
        total_height = sum((f.height for f in full_lines)) + 1
        # rounding to 3 by adding extra lines
        arr_width = (_max_width + (3 - (_max_width % 3))) if self.lcd else _max_width
        arr = np.zeros((total_height, arr_width, ) + ((4, ) if self.color else ()), dtype='uint8')
        return arr, arr_width

    # @wrap({'max': max, 'min': min, 'sum': np.sum, 'enumerate': enumerate, 'np': np})
    def _blit_pass(self, full_lines):
        arr, arr_width = self._allocate_array(full_lines)

        accumulated_vert_line_offset = 0
        for lineno, line in enumerate(full_lines):
            word_offset = self.align_mode(line.length, arr_width)
            line_ascender = line.ascender

            for word in line.words:
                endpoint = 0
                for symbol, symbol_offset, endpoint in word:
                    if not symbol.bitmap.size:
                        continue
                    hor_offset = word_offset + symbol_offset
                    vert_start = accumulated_vert_line_offset - symbol.bearing.vertical + line_ascender

                    arr[max(vert_start, 0): vert_start + symbol.height,
                        hor_offset: hor_offset + symbol.width] \
                        += symbol.bitmap[-min(vert_start, 0):]

                word_offset += endpoint
            accumulated_vert_line_offset += line.height

        # arr = ((arr.astype('float32') / 256) ** 1.3 * 256).astype('uint8')

        return arr
