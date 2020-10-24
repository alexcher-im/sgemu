import numpy as np
from OpenGL.GL import GL_DYNAMIC_DRAW
from glm import lookAt, perspective

from .base import BaseRendererDependence
from ...scene.components.camera import CameraDataUpdateEvent
from ...scene.scene import SetCameraEvent
from ...model.model import NodeDrawEvent


class CurrentDependence(BaseRendererDependence):
    _event_subscriptions_ = (CameraDataUpdateEvent, NodeDrawEvent, SetCameraEvent)
    DEPENDENCY_NAME = 'MVPMatrices'
    BUFFER_SIZE = 5 * 4 * 4 * 4  # mat_cnt * rows * cols * sizeof(float32)
    BUFFER_SHAPE = (5, 4, 4)  # mat_cnt, rows, cols

    def __init__(self, scene, *args, **kwargs):
        super(CurrentDependence, self).__init__(scene, *args, **kwargs, buffer_usage=GL_DYNAMIC_DRAW)
        self.buffer.set_buf_data(np.zeros(self.BUFFER_SHAPE, 'float32'))
        self.near_pane = 0.1

        self.view_matrix = np.identity(4, 'float32')
        self.projection_matrix = np.identity(4, 'float32')
        self.view_projection_matrix = np.identity(4, 'float32')
        self.model_matrix = np.identity(4, 'float32')
        self.model_view_projection_matrix = np.identity(4, 'float32')
        self._old_model_matrix = np.identity(4, 'float32')
        # todo filter events if current renderer does not require this dependence

    def on_event(self, event):
        # using a single uniform buffer and same offset for all models is a worst thing you can find here, btw
        # you can see this if you profile `main.py` and look where most of the time spent :D

        # note: numpy matrix multiplication differs from glm. multiplication order is reversed
        if isinstance(event, NodeDrawEvent):
            self.model_matrix[:] = event.node.result_matrix
            if np.array_equal(self.model_matrix, self._old_model_matrix):
                return
            self._old_model_matrix[:] = self.model_matrix
            # np.matmul(self.model_matrix, self.view_projection_matrix, out=self.model_view_projection_matrix)
            self.model_view_projection_matrix[:] = self.model_matrix @ self.view_projection_matrix
        elif isinstance(event, CameraDataUpdateEvent) or isinstance(event, SetCameraEvent):
            self._rebuild_view_matrix(event.component.game_object)
            self._rebuild_projection_matrix(event.component)
            self.view_projection_matrix[:] = self.view_matrix @ self.projection_matrix
        else:
            return
        self.buffer.force_upload()

    def add_setter(self, name, offset, size):
        name += '_matrix'
        offset //= 4 * 4
        if not hasattr(self, name):
            raise AttributeError('Invalid attribute name:' + name)
        setattr(self, name, self.buffer.get_buffer_data()[offset])

    def _rebuild_view_matrix(self, game_object):
        self.view_matrix[:] = lookAt(game_object.abs_pos, game_object.abs_pos + game_object.direction,
                                     game_object._get_upward_vector())

    def _rebuild_projection_matrix(self, camera):
        # it's a perspective matrix only todo add other matrices
        self.projection_matrix[:] = perspective(camera.fov, camera.render_target.width / camera.render_target.height,
                                                self.near_pane, camera.render_distance)
