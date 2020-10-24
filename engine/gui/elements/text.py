from typing import List

from OpenGL.GL import GL_RED
from glm import vec4

from ..adaptive import ResizeModes, AlignModes
from ..base import BaseElement
from ..typedefs import vec_type, nullable_vec_type, cvec
from ...lib.freetype_wrap import FTFace, enumerate_fonts
from ...lib.text_renderer import BitmapFactory, LineAlignmentMode

system_fonts = enumerate_fonts()

# todo cache fonts


class Font:
    def __init__(self, family=None, f_type='Regular', size=12, dpi=96):
        self.family = family
        self.f_type = f_type
        self.size = size
        self.dpi = dpi
        if family is None:
            family = system_fonts.os_default
        try:
            family = system_fonts.fonts[family]
            try:
                name = family[f_type]
            except KeyError:
                name = next(iter(family))
        except KeyError:
            name = system_fonts.fonts[system_fonts.os_default]['Regular']
        self.name = name


def parse_fonts(font) -> List[FTFace]:
    if font is None:
        font = system_fonts.os_default
    if isinstance(font, str) or isinstance(font, FTFace) or isinstance(font, Font):
        font = (font, )
    font = list(font)
    for i, item in enumerate(font):
        if item is None:
            item = system_fonts.os_default
        if isinstance(item, str):
            item = Font(item)
        if isinstance(item, Font):
            item = FTFace(item.name, (item.size, item.size), (item.dpi, item.dpi))
        font[i] = item
    return font


class TextElement(BaseElement):
    def __init__(self, parent: 'BaseElement', pos: vec_type = cvec(), size: nullable_vec_type = None,
                 resize_act=ResizeModes.stretch, align_act=AlignModes.stretch,
                 fonts=None, text='nothing', font_info=None, color=None, line_align=LineAlignmentMode.left):
        self.text_info = (text, font_info)
        self.fonts = parse_fonts(fonts)
        self.bitmap_factory = BitmapFactory(self.fonts, align_mode=line_align)
        super().__init__(parent, pos, size, resize_act, align_act)
        self.set_color(color)

    def _internal_set_text(self):
        text, font_info = self.text_info
        bitmap = self.bitmap_factory.get_map(text, self.metrics.fit_size.x, font_info)
        self.render_data.opengl_texture.load_from_bytes(bitmap[::-1], GL_RED, GL_RED, *bitmap.shape[::-1], True)
        self.render_data.opengl_texture.set_rgba_swizzling('111r')
        self.metrics.draw_size = cvec(bitmap.shape[::-1])

    def set_text(self, text, font_info=None):
        self.text_info = (text, font_info)
        self._internal_set_text()

    def set_color(self, color):
        if color is None:
            color = (0, 0, 0, 255)
        color = vec4(color) / 255
        self.render_data.color = color

    def _internal_update_on_resize(self):
        self._internal_set_text()
