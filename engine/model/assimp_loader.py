from os.path import split, join

from pyassimp.material import aiTextureType_DIFFUSE, aiTextureType_SPECULAR, aiTextureType_NORMALS, aiTextureType_HEIGHT

from .model import Node, RenderCompound, Material, UnfinishedModel
from ..gl.mesh import VAOMesh
from ..gl.texture import Texture2D
from ..lib.assimp import load_scene, free_scene, get_material_texture, retrieve_mesh_data


def load_model(filename):
    obj_dir = split(filename)[0]
    assimp_scene = load_scene(filename)
    print('model load: %s, %d:%d' % (filename, len(assimp_scene.meshes), len(assimp_scene.materials)))
    model = UnfinishedModel(assimp_scene.meshes, assimp_scene.materials, assimp_scene.root_node,
                            process_mesh, process_material, process_node, lambda obj: free_scene(obj.scene_src))
    model.obj_dir = obj_dir
    model.scene_src = assimp_scene
    return model


def process_node(unfinished, model, node, parent=None):
    ret_node = Node(parent)
    for i in range(node.mNumMeshes):
        ret_node.meshes.append(model.meshes[node.mMeshes[i]])
    children_pointer = node.mChildren
    for i in range(node.mNumChildren):
        ret_node.child_nodes.append(process_node(unfinished, model, children_pointer[i].contents, ret_node))
    return ret_node


def process_material(unfinished, _model, material, texture_bind_data):
    # todo textures can have same paths. do not load them all
    # cache paths and then restore textures from it
    # todo deal with alpha, gamma and other texture sampler parameters
    textures = []
    for ai_tex_type, internal_type in ((aiTextureType_DIFFUSE, 'diffuse'),
                                       (aiTextureType_SPECULAR, 'specular'),
                                       (aiTextureType_NORMALS, 'normal'),
                                       (aiTextureType_HEIGHT, 'height')):
        tex = get_material_texture(material, ai_tex_type)
        block_id = texture_bind_data.get(internal_type)
        if block_id is None:
            continue
        if tex is not None:
            tex_path = join(unfinished.obj_dir, tex)
            if __debug__:
                print('found texture', internal_type, 'path:', tex_path, block_id.load_params)
            textures.append(Texture2D.tex_from_file(tex_path, block_id=block_id.bind_index, **block_id.load_params))
        else:
            if __debug__:
                print('not found texture:', internal_type)
            textures.append(block_id.bind_index)
    return Material(textures)


def process_mesh(_unfinished, model, mesh, attribute_data):
    int_attribute_data = tuple(map(lambda c_type: int(c_type[1] * c_type[0][2] // 4), attribute_data))
    mesh_data = retrieve_mesh_data(mesh, attribute_data)
    if __debug__:
        print('mesh data retrieving: %s vertices, %s faces' % (mesh.mNumVertices, mesh.mNumFaces))
    mesh_obj = VAOMesh(mesh_data[0], mesh_data[1], int_attribute_data)
    material = model.materials[mesh_data[2]]
    return RenderCompound(mesh_obj, material)
