from glm import ivec4

from engine.gui.adaptive import AlignModes, ResizeModes
from engine.gui.base import BaseElement, cvec
from engine.gui.elements.image import ImageElement
from engine.gui.elements.text import TextElement
from engine.gui.typedefs import vec_type, nullable_vec_type
from engine.lib.text_renderer import LineAlignmentMode


class SgCheckboxOld(BaseElement):
    def __init__(self, parent: 'BaseElement', pos: vec_type = cvec(), size: nullable_vec_type = None,
                 resize_act=ResizeModes.keep, align_act=AlignModes.stretch,
                 mark_color_unchecked=ivec4(0xFF, 0x43, 0x3E, 255), mark_color_checked=ivec4(0x4F, 0xD9, 0x4F, 255),
                 text='Checkbox text'):
        size = cvec(size)
        size.x = 9999
        super().__init__(parent, pos, size, resize_act, align_act)
        self._colors = [mark_color_unchecked, mark_color_checked]

        self.border = ImageElement(self, size=self.size.y, resize_act=ResizeModes.keep_ratio_fit, picture=255)
        self.check_mark = ImageElement(self.border, picture=mark_color_unchecked, pos=(1, 1), size=self.size.y - 2)
        self.text = TextElement(self, pos=(self.size.y + 4, 2), text=text)

        self.is_checked = False
        self.check_mark.event_manager.mouse_click_callback = self.on_mouse_press

        self.internal_resize()

    def swap_state(self):
        self.is_checked = not self.is_checked
        self.check_mark.set_picture(self._colors[self.is_checked])

    def _internal_update_on_resize(self):
        if self.children:
            self.metrics.draw_size = cvec(self.text.size.x + self.size.y, self.size.y)
        else:
            super(SgCheckboxOld, self)._internal_update_on_resize()

    def on_mouse_press(self, *_):
        self.swap_state()
        return True


class SgCheckbox(TextElement):
    def __init__(self, parent: 'BaseElement', pos: vec_type = cvec(), size: nullable_vec_type = None,
                 resize_act=ResizeModes.stretch, align_act=AlignModes.stretch, fonts=None, text='nothing',
                 font_info=None, color=None, line_align=LineAlignmentMode.left,

                 inactive_color=ivec4(0x24, 0x28, 0x33, 255), active_color=ivec4(255),
                 inactive_font_color=ivec4(235, 235, 235, 255), active_font_color=ivec4(15, 15, 15, 255)):

        super().__init__(parent, pos, size, resize_act, align_act, fonts, text, font_info, color, line_align)
        self._colors = (inactive_color, active_color)
        self._font_colors = (inactive_font_color, active_font_color)

        self.background = ImageElement(self)
        self.is_checked = True
        self.swap_states()
        self.event_manager.mouse_click_callback = self.mouse_click_event

    def swap_states(self):
        self.is_checked = not self.is_checked
        self.background.set_picture(self._colors[self.is_checked])
        self.set_color(self._font_colors[self.is_checked])

    def get_active_nodes(self):
        yield from self.background.get_active_nodes()
        yield self

    def mouse_click_event(self, *_):
        self.swap_states()
        return True
