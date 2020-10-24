import numpy as np

from engine.gl import VAOMesh, GL_TRIANGLE_STRIP
from engine.gui.adaptive import ResizeModes, AlignModes
from engine.gui.base import BaseElement
from engine.gui.typedefs import vec_type, nullable_vec_type, cvec


class RoundedRect(BaseElement):
    def __init__(self, parent: 'BaseElement', pos: vec_type = cvec(), size: nullable_vec_type = None,
                 resize_act=ResizeModes.stretch, align_act=AlignModes.stretch,
                 border_radius=111, toughness=1):
        super().__init__(parent, pos, size, resize_act, align_act)
        self.border_radius = border_radius
        self.toughness = toughness
        self.render_data.mesh = VAOMesh([0, 0, 0, 1,
                                          0, 1, 0, 0,
                                          1, 1, 1, 0,
                                          1, 0, 1, 1],
                                         [0, 1, 2, 2, 3, 0], (2, 2), mode=GL_TRIANGLE_STRIP)
        self._rebuild_vertices()

    def _rebuild_vertices(self):
        internal, external = self._get_circle()
        vert_data = np.dtype([('pos', '2f4'), ('uv', '2f4')])
        arr = np.zeros((len(internal) * 2), dtype=vert_data)  # dims: (((pos) * 2) * `type (ext/int)`) * `vert (pos/uv)`
        arr[::2]['pos'] = external
        arr[1::2]['pos'] = internal
        arr['uv'] = 1
        print(arr)
        self.render_data.mesh.set_vertex_data(arr.view('float32'))

    def _get_circle(self):
        arange = np.arange(int(np.pi * self.border_radius / 4 + 1) * 4, dtype='float32')
        arange *= 1 / (len(arange) / (np.pi * 2))
        print(len(arange), arange)
        external_circle = np.zeros((arange.shape[0], 2), 'float32')
        # optimize with out= arg
        external_circle[:, 0] = np.cos(arange)
        external_circle[:, 1] = np.sin(arange)
        internal_circle = external_circle * (self.border_radius - self.toughness)
        external_circle *= self.border_radius
        print(internal_circle)
        return internal_circle, external_circle
