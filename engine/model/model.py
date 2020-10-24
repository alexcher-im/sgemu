from glm import mat4, translate, vec3

from ..event.base import MainEventManager, BaseEvent
from ..gl.mesh import VAOMesh
from ..gl import Texture2D

# todo big model update

"""
SceneRenderInfo - stores RenderComponent() instances
    must be able to dynamically load models
RendererList - stores a number of renderers to be used depending on current LOD level
RenderComponent - stores a LodModel() and RendererList() instances. interacts with scene as a component

LodModel - stores info about Model() instances to draw and some shader info
    must be able lo dynamicly load Model() instances in another thread
Model - stores info about nodes and their meshes+materials
Node - stores a number of RenderCompound() instances to be drawn and their matrices
RenderCompound - Stores a VAOMesh() and Material() instance"""


class Material:
    # todo animations (texture switches)
    def __init__(self, textures):
        self._textures = textures
        self._methods = [(Texture2D.unbind_block, val) if isinstance(val, int)  # if we should unbind it
                         else (val[0].bind_to_block, val[1]) if isinstance(val, tuple)   # if there is a texture sampler
                         else (val.bind_to_block, None) for val in textures]

    def get_textures(self):
        return self._textures

    def use(self):
        for method, arg in self._methods:
            method(arg)


RenderCompoundEvent = BaseEvent.create_meta('RenderCompoundEvent', ('compound', ))
RenderCompoundDrawEvent = RenderCompoundEvent.create_meta('RenderCompoundDrawEvent')


class RenderCompound:
    def __init__(self, mesh: VAOMesh, material: Material):
        self.mesh = mesh
        self.material = material

    def draw(self):
        MainEventManager.add_event(RenderCompoundDrawEvent(self, instant=True))
        self.material.use()
        self.mesh.use()
        self.mesh.draw()


class UnfinishedModel:
    def __init__(self, meshes: list, materials: list, node,
                 mesh_processor, material_processor, node_processor, on_delete):
        self.raw_meshes = meshes
        self.raw_materials = materials
        self.raw_node = node
        self.mesh_processor = mesh_processor
        self.material_processor = material_processor
        self.node_processor = node_processor
        self.on_delete = on_delete

    def format(self, attribute_data, texture_bind_data):
        model = Model()
        for material in self.raw_materials:
            model.materials.append(self.material_processor(self, model, material, texture_bind_data))
        for mesh in self.raw_meshes:
            model.meshes.append(self.mesh_processor(self, model, mesh, attribute_data))
        model.root_node = self.node_processor(self, model, self.raw_node)
        model.finished()
        return model

    def __del__(self):
        self.on_delete(self)


class Model:
    # todo Model.copy() and Node.copy() that copies the meshes and creates new matrices
    # soft-copy refers original resources, hard-copy copies it's byte data
    def __init__(self, materials=None, meshes=None, root_node=None):
        if meshes is None:
            meshes = []
        if materials is None:
            materials = []
        self.materials = materials
        self.meshes = meshes  # meshes are RenderCompound instances, not a Mesh
        self.root_node = root_node
        self.draw = None
        self.set_model_matrix = None
        self.set_offset = None

    @property
    def own_matrix(self):
        return self.root_node.own_matrix

    @property
    def raw_matrix(self):
        return self.root_node.raw_matrix

    def finished(self):
        # methods
        self.draw = self.root_node.draw
        self.set_model_matrix = self.root_node.set_model_matrix
        self.set_offset = self.root_node.set_offset
        return self


NodeEvent = BaseEvent.create_meta('NodeEvent', ('node', ))
NodeDrawEvent = NodeEvent.create_meta('NodeDrawEvent')
NodeModelMatrixUpdateEvent = NodeEvent.create_meta('NodeModelMatrixUpdate')


class Node:
    def __init__(self, parent=None, childs=None, name=None, meshes=None, offset=vec3(0)):
        if childs is None:
            childs = []
        if meshes is None:
            meshes = []
        self.name = name  # for user identification only
        self.child_nodes = childs
        self.parent = parent
        self.meshes = meshes  # meshes are RenderCompound instances

        self.offset = offset
        self.raw_matrix = None  # source self transform matrix (offset not affected)
        self.own_matrix = None  # resulting self transform matrix (raw_matrix translated by offset)
        self.result_matrix = None  # resulting model matrix. bind-ready
        self.set_model_matrix(mat4(1))

    def set_offset(self, offset):
        if self.offset == offset:
            return
        self.offset = offset
        self.set_model_matrix(self.raw_matrix)

    def draw(self):
        MainEventManager.add_event(NodeDrawEvent(self, instant=True))
        for mesh in self.meshes:
            mesh.draw()
        for node in self.child_nodes:
            node.draw()

    def apply_transformation(self, transform_matrix: mat4):
        self.result_matrix = self.own_matrix * transform_matrix
        MainEventManager.add_event(NodeModelMatrixUpdateEvent(self, instant=True))
        for node in self.child_nodes:
            node.apply_transformation(self.result_matrix)

    def set_model_matrix(self, matrix: mat4):
        self.raw_matrix = matrix
        self.own_matrix = translate(matrix, self.offset)
        if self.parent is not None:  # root node
            mult_matrix = self.parent.result_matrix
        else:
            mult_matrix = mat4(1)
        self.apply_transformation(mult_matrix)
