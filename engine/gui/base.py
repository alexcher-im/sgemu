from collections import namedtuple

from .drawable import RenderData
from .event import EventHandler
from .adaptive import ResizeModes, AlignModes
from .typedefs import *


class ElemMetrics:
    # metrics vectors (sorted from "set by user" to "ready to draw'):

    # set by user on init or in runtime
    user_pos: cvec
    user_size: cvec
    # copied from parent elem when user sets pos or size
    parent_old_pos: cvec
    parent_old_size: cvec

    # maximum available size for elem (after wrapping)
    fit_size: cvec
    # which current element decided to use (also an *update* function is called here to make elem set this value)
    draw_size: cvec
    # aligned elem position
    draw_pos: cvec
    # absolute position
    abs_pos: cvec

    def __init__(self, elem: 'BaseTreeNode', pos, size):
        size = cvec(size)
        pos = cvec(pos)
        self.user_pos = pos
        self.user_size = size

        self.abs_pos = elem.parent.metrics.abs_pos + pos
        self.draw_pos = pos
        self.draw_size = size
        self.fit_size = cvec(0)
        self.parent_old_size = elem.parent.size
        self.parent_old_pos = elem.parent.pos


class BaseTreeNode:
    def __init__(self, parent: 'BaseTreeNode', pos, size):
        self.parent = parent
        self.children = []
        self.metrics = ElemMetrics(self, pos, size)

    @property
    def pos(self) -> cvec:
        return self.metrics.draw_pos

    @pos.setter
    def pos(self, value: vec_type):
        self.metrics.draw_pos = cvec(value)

    @property
    def size(self) -> cvec:
        return self.metrics.draw_size

    @size.setter
    def size(self, value: vec_type):
        self.metrics.draw_size = cvec(value)

    def add_child(self, child: 'BaseTreeNode'):
        self.children.append(child)
        # maybe we should call .internal_resize()

    # external function
    def set_size(self, size: vec_type):
        size = cvec(size)
        if min(size) < 1:
            return
        self.metrics.user_size = size
        self.metrics.parent_old_size = self.parent.size
        self._user_update_hook()

    # external function
    def move(self, pos: vec_type):
        self.metrics.user_pos = cvec(pos)
        self.metrics.parent_old_pos = self.parent.pos
        self._user_update_hook()

    def _user_update_hook(self):
        pass


class BaseElement(BaseTreeNode):
    EVENT_MANAGER_CLASS = EventHandler

    def __init__(self, parent: 'BaseElement', pos: vec_type = cvec(), size: nullable_vec_type = None,
                 resize_act=ResizeModes.stretch, align_act=AlignModes.stretch):
        if size is None:
            size = cvec(parent.size) - cvec(pos)
        super().__init__(parent, pos, size)
        self.parent.add_child(self)
        self._enabled = True  # todo may be we also should not resize element if disabled

        self.resize_act = resize_act
        self.align_act = align_act

        self.render_data = RenderData()
        self.event_manager = self.EVENT_MANAGER_CLASS(self)

        # rebuilding everything
        self.internal_resize()

    def internal_resize(self, force=False):
        # `force` argument indicates that parent's position changed and we should move all child elements
        old_fit_size = self.metrics.fit_size
        self.resize_act.func(self)
        self.clamp_values()

        if not force and self.metrics.fit_size == old_fit_size:  # does not resized [optimization]
            old_pos = self.pos
            self.align_act.func(self)
            if old_pos == self.pos:
                return
            force = True

        self._internal_update_on_resize()
        self.align_act.func(self)
        self.metrics.abs_pos = self.parent.metrics.abs_pos + self.pos

        for child in self.children:
            child.internal_resize(force)

    def clamp_values(self):
        # self.metrics.fit_size = clamp(self.metrics.fit_size, cvec(1), self.parent.size)
        pass

    def _internal_update_on_resize(self):
        # override this if you want to set preferred size
        self.metrics.draw_size = self.metrics.fit_size

    def _user_update_hook(self):
        self.internal_resize()

    def __bool__(self):
        return self._enabled

    def get_active_nodes(self):
        if not self:
            return
        yield self
        for child in self.children:
            yield from child.get_active_nodes()


class RootElement(BaseElement):
    MetricsInitRootObj = namedtuple('MetricsInitRootObj', 'abs_pos draw_pos draw_size')

    def __init__(self, size: vec_type):
        self.metrics = self.MetricsInitRootObj(cvec(0), cvec(0), size)
        super().__init__(self, cvec(0), size, resize_act=ResizeModes.keep)
        self.children.pop(-1)

    def clamp_values(self):
        pass
