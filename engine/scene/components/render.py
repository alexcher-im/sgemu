from typing import Union, List

import glm

from ...renderer.chain import RenderChain
from ...model.model import UnfinishedModel, Model
from ..component import Component


class RenderComponent(Component):
    def __init__(self, game_object=None, model: Union[UnfinishedModel, Model] = None, renderer: RenderChain = None):
        super(RenderComponent, self).__init__(game_object)
        if isinstance(model, UnfinishedModel):
            model = model.format(renderer.attribute_data, renderer.sampler_data)
        self.model = model
        self.transform = TransformationProcessor(self)
        self.renderer = renderer

    def update(self):
        self.model.set_offset(self.game_object.abs_pos)

    def set_model(self, model):
        self.model = model

    def set_renderer(self, renderer):
        self.renderer = renderer

    def draw(self):
        self.renderer.first_pass(self.model)


class TransformationProcessor:
    """
    This class applies transformation to already transformed data
    If you want to undo transformation - drop the matrix or apply reverse transform
    """

    def __init__(self, component):
        self.component = component

    def _add_transformation(self, func):
        self.component.model.set_model_matrix(func(self.component.model.raw_matrix))
        return self.component

    def scale(self, scale):
        self._add_transformation(lambda mat: glm.scale(mat, glm.vec3(scale)))
        return self.component

    def move(self, pos):
        self._add_transformation(lambda mat: glm.translate(mat, glm.vec3(pos)))
        return self.component

    def rotate(self, axis, value):
        self._add_transformation(lambda mat: glm.rotate(mat, value, glm.vec3(axis)))
        return self.component


class CachedComponentsGroup(list):
    def draw(self):
        self: List[RenderComponent]
        if self:
            renderer = self[0].renderer
            renderer.first_pass((component.model for component in self))
