from glm import ivec2


class EventHandler:
    def __init__(self, element):
        self.elem = element

        self.mouse_enter_callback = lambda elem, pos: False
        self.mouse_leave_callback = lambda elem, pos: False
        self.mouse_click_callback = lambda elem, button, pos: False
        self.mouse_release_callback = lambda elem, button, pos: False

        self._pressed_buttons = [False] * 2  # [left, right]
        self._is_aimed = False
        self._mouse_pos = ivec2(-1)

    def on_mouse_move_event(self, pos: ivec2):
        self._mouse_pos = pos

        if self._is_aimed:
            if pos not in self:
                self._is_aimed = False
                if self.mouse_leave_callback(self.elem, pos):  # event handled
                    return
        else:
            if pos not in self:  # [optimization] do not check children
                return
            self._is_aimed = True
            if self.mouse_enter_callback(self.elem, pos):  # event handled
                return

        for child in self.elem.children:
            child.event_manager.on_mouse_move_event(pos - child.pos)

    def on_mouse_press_event(self, button: int):
        if self._is_aimed:
            if self.mouse_click_callback(self.elem, self._mouse_pos, button):  # event handled
                return
            for child in self.elem.children:
                child.event_manager.on_mouse_press_event(button)

    def on_mouse_release_event(self, button: int):
        self._pressed_buttons[button] = False
        if self.mouse_release_callback(self.elem, self._mouse_pos, button):  # event handled
            return
        for child in self.elem.children:
            child.event_manager.on_mouse_release_event(button)

    def __contains__(self, item: ivec2):
        size = self.elem.size
        return 0 <= item.x < size.x and 0 <= item.y < size.y
