import ctypes
import os
import platform
from collections import namedtuple

import freetype
import freetype.ft_enums
import numpy as np
from glm import ivec2

from engine.lib.np_helper import map_ct_pointer

_font_names_cache = ()


class FTFace:
    def __init__(self, name, size=(16, 16), dpi=(96, 96), lcd=False, color=False):
        self.lcd = lcd
        self.color = color
        self.face = freetype.Face(name)
        self.set_size(size, dpi)

    def set_size(self, size, dpi=(96, 96)):
        self.face.set_char_size(int(size[0] * 64), int(size[1] * 64), *dpi)

    @property
    def bitmap(self):
        glyph_bitmap = self.face.glyph.bitmap

        # determining array size (based on coloring)
        if not self.color:
            arr_size = (glyph_bitmap.rows, glyph_bitmap.pitch)
        elif glyph_bitmap.pixel_mode == 7:  # FT_PIXEL_MODE_BGRA
            arr_size = (glyph_bitmap.rows, glyph_bitmap.pitch // 4, 4)
        else:
            arr_size = (glyph_bitmap.rows, glyph_bitmap.pitch, 1)

        # mapping freetype bitmap buffer
        if glyph_bitmap.rows:
            bitmap = map_ct_pointer(glyph_bitmap._FT_Bitmap.buffer, ctypes.c_uint8, arr_size)
        else:
            return np.empty((0, 0), 'uint8')

        # changing color palette from BGRA to RGBA
        if glyph_bitmap.pixel_mode == 7:  # FT_PIXEL_MODE_BGRA
            bitmap_new = np.empty(arr_size, 'uint8')
            bitmap_new[:, :, 0] = 255 - bitmap[:, :, 2]
            bitmap_new[:, :, 1] = 255 - bitmap[:, :, 1]
            bitmap_new[:, :, 2] = 255 - bitmap[:, :, 0]
            bitmap_new[:, :, 3] = 255 - bitmap[:, :, 3]
            bitmap = bitmap_new
        else:
            bitmap = bitmap.copy()

        return bitmap

    @property
    def bearing(self):  # vertical (up), horizontal (left), advance (increment-by-symbol value)
        advance = self.face.glyph.advance
        mult = 3 if self.lcd else 1
        return (self.face.glyph.bitmap_top, self.face.glyph.bitmap_left * mult,
                (ivec2(advance.x, advance.y) * mult) / 64)

    def get_symbol(self, char):
        mode = freetype.ft_enums.FT_LOAD_FLAGS['FT_LOAD_RENDER']
        if self.color:
            mode |= freetype.ft_enums.FT_LOAD_FLAGS['FT_LOAD_COLOR']
        # print('load char', repr(char))
        if self.lcd:
            mode |= freetype.ft_enums.FT_LOAD_TARGETS['FT_LOAD_TARGET_LCD']
        self.face.load_char(char, mode)
        bitmap = self.bitmap
        bearing = self.bearing
        return RasterSymbol(char, bitmap, RasterSymbol.Bearing(*bearing), self.face.size.height >> 6,
                            self.face.size.ascender >> 6, self.face.get_kerning)


class RasterSymbol:
    Bearing = namedtuple('Bearing', 'vertical horizontal advance')  # int, int, ivec2

    def __init__(self, char: str, bitmap: np.ndarray, bearing: Bearing, font_height: int, font_ascender: int,
                 kerning_func=lambda x, y: ivec2()):
        self.char = char
        self.bitmap = bitmap
        self.bearing = bearing
        self.kerning_func = kerning_func
        self.font_height = font_height
        self.font_ascender = font_ascender

        self.size = ivec2(bitmap.shape)
        self.height, self.width = bitmap.shape[:2]
        self.full_width = self.bearing.advance.x

    def get_kerning(self, symbol: 'RasterSymbol'):
        return self.kerning_func(self.char, symbol.char).x >> 6

    def __str__(self):
        return f'<RasterSymbol class: char "{self.char}", advance {self.full_width}'

    def __len__(self):
        return self.full_width


class FontList:
    def __init__(self, os_default):
        self.fonts = {}
        self.os_default = os_default

    def add_font(self, path, family, style):
        try:
            self.fonts[family][style] = path
        except KeyError:
            self.fonts[family] = {style: path}

    def get_font(self, name, style='Regular'):
        # todo add 2 warning logs: if style not found or font name not found
        if name in self.fonts:
            if style in self.fonts[name]:
                return self.fonts[name][style]
            return self.fonts[name]['Regular']
        return self.fonts[self.os_default]['Regular']


def enumerate_fonts():
    curr_os = platform.system().lower()
    if 'linux' in curr_os:
        fonts = FontList('NonExistingFont')
        raw_lines = os.popen('fc-list').read().split('\n')
        for line in raw_lines:
            filepath, name, style = map(str.strip, line.split(':'))
            fonts.add_font(filepath, name, style['style='.__len__():])
    elif 'windows' in curr_os:
        fonts = FontList('Arial')
        search_dirs = ['C:\\Windows\\Fonts\\', ]
        for directory in search_dirs:
            for root, _, files in os.walk(directory):
                for file in files:
                    filename = os.path.join(root, file)
                    if os.path.splitext(filename)[1] not in ('.ttf', '.ttc'):
                        continue
                    face = freetype.Face(filename)
                    name = face.family_name.decode()
                    style = face.style_name.decode()
                    fonts.add_font(filename, name, style)
    elif 'darwin' in curr_os:
        raise ModuleNotFoundError("Fuck you dude just sell your mac and buy a real pc")
    else:
        raise Exception("Hey! What the fuck? How did you run python on this?")
    return fonts


if __name__ == '__main__':
    print(*enumerate_fonts().fonts.items(), sep='\n')
