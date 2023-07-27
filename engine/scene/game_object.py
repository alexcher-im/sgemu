from typing import Union, Iterable

from glm import pi as pi_func, vec3, normalize, clamp, acos, asin, cross, rotate, mat4, vec4, cos, sin

from ..event.scene import GameObjectEvent
from ..event.base import MainEventManager
from .component import Component, ComponentUpdateEvent

pi = pi_func()

GameObjectAddEvent = GameObjectEvent.create_meta('GameObjectAddEvent')
GameObjectUpdateEvent = GameObjectEvent.create_meta('GameObjectUpdateEvent')


class GameObject:
    def __init__(self, parent=None, scene=None, pos=(0., 0., 0.), children=(), components=()):
        # todo protect game_objects and components from being used more than once
        pos = vec3(pos)
        self.scene = scene
        self.parent = parent
        self._pos = pos
        self.abs_pos = pos
        self.children = []
        self.components = []
        if parent is not None:
            self.scene = parent.scene
            parent.add_child(self)
            self.pos = pos
        for child in children:
            self.add_child(child)
        for component in components:
            self.add_component(component)

    @property
    def pos(self):
        return vec3(self._pos)

    @pos.setter
    def pos(self, value):
        self._pos = vec3(value)
        self.update()

    def move_by_vector(self, vector: vec3):
        self.pos = self.pos + vector

    def update(self):
        self.abs_pos = self.parent.abs_pos + self.pos
        MainEventManager.add_event(GameObjectUpdateEvent(self))
        for child in self.children:
            child.update()
        for comp in self.components:
            comp.update()

    def add_child(self, obj: 'GameObject'):
        obj.parent = self
        self.children.append(obj)
        obj.recursive_add_object_event()

    def recursive_add_object_event(self):
        MainEventManager.add_event(GameObjectAddEvent(self))
        for obj in self.children:
            MainEventManager.add_event(GameObjectAddEvent(obj))
        for comp in self.components:
            MainEventManager.add_event(ComponentUpdateEvent(comp))

    @property
    def copy(self):
        copy_obj = GameObject(self.scene, None, self.pos)
        for child in self.children:
            copy_obj.add_child(child.copy)
        for component in self.components:
            copy_obj.add_component(component.copy)
        return copy_obj

    def add_component(self, component: Component):
        self.components.append(component)
        component.on_attach(self)

    def get_component(self, metaclass):
        for item in self.components:
            if isinstance(item, metaclass):
                return item

    def yield_components(self, condition):
        for component in self.components:
            if condition(component):
                yield component
        for child in self.children:
            yield from child.yield_components(condition)


class DirectedGameObject(GameObject):
    def __init__(self, *args, direction = None, **kwargs):
        self._angles = vec3(0)
        self._direction = vec3(0.0, 0.0, 1.0) if direction == None else direction
        super(DirectedGameObject, self).__init__(*args, **kwargs)
        self.angles = (pi, 0, 0)

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
            self.update()

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

    def look_global(self, point: Union[vec3, Iterable, float]):
        pos = self.abs_pos
        vector = normalize(point - pos)
        self.set_angles(acos(vector.x), asin(vector.y))
        self.direction = vector

    def _get_right_vector(self):
        # used as an auxiliary vector for creating upward vector
        curr_vec = normalize(cross(self.direction, vec3(0.0, 1.0, 0.0)))
        roll_matrix = rotate(mat4(1), self.angles[2], self.direction)
        return (vec4(curr_vec, 1) * roll_matrix).xyz

    def _get_upward_vector(self):
        # upward vector in camera coordinate space
        return cross(self._get_right_vector(), self.direction)

    def move_sideways(self, direction, speed=1.0):
        # move right if bool(direction) is True, else left
        vector = self._get_right_vector() * speed
        if not direction:
            vector *= -1
        self.move_by_vector(vector)

    def _rebuild_direction_vector(self):
        curr_angles = self.angles
        self.direction = vec3(cos(curr_angles[0]), curr_angles[1] * pi / 2, sin(curr_angles[0]))
