import glm
from .base import BasePositioned3D

vec3 = glm.vec3
radians = glm.radians
cross = glm.cross
normalize = glm.normalize
sin = glm.sin
cos = glm.cos
asin = glm.asin
acos = glm.acos
clamp = glm.clamp
pi = glm.pi()


class DrawDirected(BasePositioned3D):
    def __init__(self, pos=(0, 0, 0)):
        super(DrawDirected, self).__init__(pos)
        # yaw, pitch, roll: expressed in radians
        self._angles = (0.0, 0.0, 0.0)
        self._direction = vec3(0.0, 0.0, 1.0)
        self.view_matrix = glm.mat4()
        self.angles = (0.0, 0.0, 0.0)  # just to hook all rebuilding

    @property
    def angles(self):
        return self._angles

    @angles.setter
    def angles(self, value):
        if self._angles != value:
            self._angles = vec3(value)
            self._rebuild_direction_vector()

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        if self._direction != value:
            self._direction = normalize(value)
            self._rebuild_view_matrix()

    def set_angles(self, yaw=None, pitch=None, roll=None):
        old_angles = self.angles
        modulo_value = pi * 2
        clamp_value = pi
        self.angles = (old_angles[0] % modulo_value if yaw is None else yaw,
                       clamp(old_angles[1], -clamp_value, clamp_value) if pitch is None else pitch,
                       old_angles[2] % modulo_value if roll is None else roll
                       )

    def add_angles(self, yaw=0, pitch=0, roll=0):
        old_angles = self.angles
        modulo_value = pi * 2
        clamp_value = pi
        self.angles = ((old_angles[0] + yaw) % modulo_value,
                       clamp(old_angles[1] + pitch, -clamp_value, clamp_value),
                       (old_angles[2] + roll) % modulo_value
                       )

    def look_global(self, point: vec3):
        vector = normalize(vec3(point.x - self.pos.x,
                                point.y - self.pos.y,
                                point.z - self.pos.z))
        self.set_angles(acos(vector.x), asin(vector.y))
        self.direction = vector

    def set_position(self, pos):
        self.pos = vec3(pos)
        self._rebuild_view_matrix()

    def move_sideways(self, direction, speed=1.0):
        # move right if bool(direction) is True, else left
        vector = normalize(cross(self._get_upward_vector(), self.direction)) * speed
        if direction:
            vector *= -1
        self.move_by_vector(vector)

    def _rebuild_direction_vector(self):
        curr_angles = self.angles
        self.direction = vec3(cos(curr_angles[0]), curr_angles[1] * pi / 2, sin(curr_angles[0]))

    def _get_right_vector(self):
        # used as an auxiliary vector for creating upward vector
        curr_vec = normalize(cross(self.direction, vec3(0.0, 1.0, 0.0)))
        roll_matrix = glm.rotate(glm.identity(glm.mat4), self.angles[2], self.direction)
        return (glm.vec4(curr_vec, 1) * roll_matrix).xyz

    def _get_upward_vector(self):
        # upward vector in camera coordinate space
        return cross(self._get_right_vector(), self.direction)

    def _rebuild_view_matrix(self):
        self.view_matrix = glm.lookAt(self.pos, self.pos + self.direction, self._get_upward_vector())


class PerspectiveManager(DrawDirected):
    def __init__(self, pos=(0, 0, 0), fov=45.0, aspect=1.0, near_pane=0.1, render_distance=100.0):
        super(PerspectiveManager, self).__init__(pos=pos)
        self.near_pane = near_pane
        self.render_distance = render_distance
        self.screen_aspect = aspect
        self.fov = 0.0
        self.set_fov(fov)
        self._rebuild_projection_matrix()

    def set_fov(self, value):
        # value must be in degrees
        self.fov = radians(value)
        self._rebuild_projection_matrix()

    def set_screen_aspect(self, aspect):
        self.screen_aspect = aspect
        self._rebuild_projection_matrix()

    def _rebuild_projection_matrix(self):
        self.perspective_matrix = glm.perspective(self.fov, self.screen_aspect, self.near_pane, self.render_distance)
