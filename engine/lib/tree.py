from typing import Union, Iterable, Optional, List

from glm import vec2, vec3


class Tree:
    def __init__(self, parent: 'Tree' = None, children: Optional[Iterable['Tree']] = None):
        if children is None:
            children = []
        self.parent: 'Tree' = parent
        self.children: List['Tree'] = children

    def add_child(self, child: 'Tree'):
        self.children.append(child)

    def remove_by_index(self, index: int):
        self.children.pop(index)

    def remove_child(self, obj: 'Tree'):
        self.children.remove(obj)

    def filter_children(self, condition):
        return filter(condition, self.children)

    def update(self) -> None:
        # slow method
        """for child in self.children:
            child.update()"""
        # faster method
        any((child.update() for child in self.children))

    @property
    def copy(self):
        return self.__class__(self.parent, [child.copy for child in self.children])


class PosTree2D(Tree):
    parent: 'PosTree2D'
    children: List['PosTree2D']
    abs_pos: vec2

    def __init__(self, parent: 'PosTree2D' = None, children: Optional[Iterable['PosTree2D']] = None,
                 pos: Union[vec2, float, Iterable] = 0):
        super(PosTree2D, self).__init__(parent, children)
        self._pos = vec2(pos)
        self.abs_pos = vec2(pos)

    @property
    def pos(self) -> vec2:
        return vec2(self._pos)

    @pos.setter
    def pos(self, value: Union[vec2, float, Iterable]):
        self._pos = vec2(value)
        self.abs_pos = self.parent.abs_pos + self._pos
        self.update()


class PosTree3D(Tree):
    parent: 'PosTree3D'
    children: List['PosTree3D']
    abs_pos: vec3

    def __init__(self, parent: 'PosTree3D' = None, children: Optional[Iterable['PosTree3D']] = None,
                 pos: Union[vec3, float, Iterable] = 0):
        super(PosTree3D, self).__init__(parent, children)
        self._pos = vec3(pos)
        self.abs_pos = vec3(pos)

    @property
    def pos(self) -> vec3:
        return vec3(self._pos)

    @pos.setter
    def pos(self, value: Union[vec3, float, Iterable]):
        self._pos = vec3(value)
        self.abs_pos = self.parent.abs_pos + self._pos
        self.update()
