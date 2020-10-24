from collections import namedtuple

from glm import vec2, min as glm_min

from .typedefs import cvec

ResizeWrapper = namedtuple('ResizeWrapper', 'func soft_redraw')
AlignWrapper = namedtuple('AlignWrapper', 'func soft_redraw')


# resize functions
def resize_stretch(elem):
    new_size = vec2(elem.metrics.user_size) * (vec2(elem.parent.size) / elem.metrics.parent_old_size)
    new_size = glm_min(new_size, vec2(elem.parent.size))
    elem.metrics.fit_size = cvec(new_size)


def resize_keep(elem):
    elem.metrics.fit_size = elem.metrics.user_size


def resize_keep_width(elem):
    new_size = elem.metrics.user_size.y * (elem.parent.size.y / elem.metrics.parent_old_size.y)
    elem.metrics.fit_size = cvec(elem.metrics.user_size.x, new_size)


def resize_keep_height(elem):
    new_size = elem.metrics.user_size.x * (elem.parent.size.x / elem.metrics.parent_old_size.x)
    elem.metrics.fit_size = cvec(new_size, elem.metrics.user_size.y)


def resize_stretch_new(elem):
    new_size = vec2(elem.metrics.user_size) * (vec2(elem.parent.size - elem.pos) /
                                               vec2(elem.metrics.parent_old_size - elem.pos))
    elem.metrics.fit_size = new_size


def resize_keep_ratio_fit(elem):
    div_c = min(vec2(elem.parent.size) / elem.metrics.user_size)
    elem.metrics.fit_size = cvec(vec2(elem.metrics.user_size) * div_c)


def resize_keep_ratio_oversize(elem):
    div_c = max(vec2(elem.parent.size) / elem.metrics.user_size)
    elem.metrics.fit_size = cvec(vec2(elem.metrics.user_size) * div_c)


# align functions
def align_stretch(elem):
    # current version may not work properly
    elem.pos = vec2(elem.metrics.user_pos) * (vec2(elem.parent.size) / elem.metrics.parent_old_size)


def align_keep(elem):
    elem.pos = elem.metrics.user_pos


def align_center(elem):
    elem.pos = (vec2(elem.parent.size) - elem.size) / 2


# side
def align_side_left(elem):
    elem.pos = 0, (vec2(elem.parent.size).y - elem.size.y) / 2


def align_side_up(elem):
    elem.pos = (vec2(elem.parent.size).x - elem.size.x) / 2, 0


def align_side_right(elem):
    elem.pos = elem.parent.size.x - elem.size.x, (vec2(elem.parent.size).y - elem.size.y) / 2


def align_side_down(elem):
    elem.pos = (vec2(elem.parent.size).x - elem.size.x) / 2, elem.parent.size.y - elem.size.y


# corner
def align_border_ul(elem):
    elem.pos = 0, 0


def align_border_ur(elem):
    elem.pos = elem.parent.size.x - elem.size.x, 0


def align_border_bl(elem):
    elem.pos = 0, elem.parent.size.y - elem.size.y


def align_border_br(elem):
    elem.pos = elem.parent.size.x - elem.size.x, elem.parent.size.y - elem.size.y


# should only change fit_size if possible
class ResizeModes:
    stretch = ResizeWrapper(resize_stretch, True)
    keep = ResizeWrapper(resize_keep, False)
    keep_width = ResizeWrapper(resize_keep_width, True)
    keep_height = ResizeWrapper(resize_keep_height, True)
    keep_ratio_fit = ResizeWrapper(resize_keep_ratio_fit, True)
    keep_ratio_oversize = ResizeWrapper(resize_keep_ratio_oversize, True)

    stretch_new = ResizeWrapper(resize_stretch_new, True)


class AlignModes:
    stretch = AlignWrapper(align_stretch, True)
    keep = AlignWrapper(align_keep, False)
    center = AlignWrapper(align_center, True)

    class Side:
        left = AlignWrapper(align_side_left, True)
        up = AlignWrapper(align_side_up, True)
        right = AlignWrapper(align_side_right, True)
        down = AlignWrapper(align_side_down, True)
        top = up
        bottom = down

    class Corner:
        ul = AlignWrapper(align_border_ul, True)
        ur = AlignWrapper(align_border_ur, True)
        bl = AlignWrapper(align_border_bl, True)
        br = AlignWrapper(align_border_br, True)
        topleft = ul
        topright = ur
        bottomright = br
        botomleft = bl
