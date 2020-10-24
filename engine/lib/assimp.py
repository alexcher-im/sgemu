from pyassimp.postprocess import *
from pyassimp.core import _assimp_lib
import numpy as np
import ctypes

from collections import namedtuple

from .np_helper import map_ct_pointer

USE_C_LOADER = True  # c loader is now deprecated todo remove assimp c loader

c_loader = None
try:
    uint = ctypes.c_uint32
    float_ptr = ctypes.POINTER(ctypes.c_float)
    cast = ctypes.cast
    c_loader = ctypes.CDLL('out.dll').load
    c_loader.argtypes = [float_ptr, float_ptr, float_ptr, uint, float_ptr]
except Exception as exc:
    print('[ERROR]: cannot load assimp c loader')  # todo add this to logging

Scene = namedtuple('Scene', 'scene animations cameras flags lights materials meshes metadata textures root_node')


def read_data_by_pointer(pointer, num):
    return b''.join(map(lambda i: pointer[i], range(num)))


def load_scene(filename, postprocess=aiProcess_PreTransformVertices
                                   | aiProcess_Triangulate
                                   | aiProcess_FlipUVs
                                   | aiProcess_CalcTangentSpace
                                   | aiProcess_GenNormals):
    if __debug__:
        print('starting loading assimp model')
    scene_src = _assimp_lib.dll.aiImportFile(filename.encode(), postprocess)
    scene = scene_src.contents
    animations = [scene.mAnimations[i].contents for i in range(scene.mNumAnimations)]
    cameras    = [scene.mCameras[i].contents    for i in range(scene.mNumCameras   )]
    lights     = [scene.mLights[i].contents     for i in range(scene.mNumLights    )]
    materials  = [scene.mMaterials[i].contents  for i in range(scene.mNumMaterials )]
    meshes     = [scene.mMeshes[i].contents     for i in range(scene.mNumMeshes    )]
    textures   = [scene.mTextures[i].contents   for i in range(scene.mNumTextures  )]
    flags      = scene.mFlags
    metadata   = scene.mMetadata.contents
    try:
        root_node = scene.mRootNode.contents
    except ValueError:
        root_node = None

    return Scene(scene_src, animations, cameras, flags, lights, materials, meshes, metadata, textures, root_node)


def free_scene(scene: Scene):
    _assimp_lib.dll.aiReleaseImport(scene.scene)


def retrieve_mesh_data(mesh, attribute_data):
    if USE_C_LOADER and c_loader is not None:
        return retrieve_mesh_c(mesh, attribute_data)
    else:
        return retrieve_mesh_numpy(mesh, attribute_data)


def retrieve_mesh_c(mesh, _):
    faces = np.empty((mesh.mNumFaces, 3), 'uint32')
    final_data = np.empty((mesh.mNumVertices, 8), dtype='float32')
    fin_ptr = final_data.ctypes.data_as(float_ptr)
    c_loader(cast(mesh.mVertices, float_ptr),
             cast(mesh.mNormals, float_ptr),
             cast(mesh.mTextureCoords[0], float_ptr),
             mesh.mNumVertices, fin_ptr)

    m_faces = mesh.mFaces
    for i in range(mesh.mNumFaces):
        curr_face = m_faces[i]
        curr_indices = curr_face.mIndices
        faces[i] = curr_indices[0], curr_indices[1], curr_indices[2]
    faces = faces.reshape(mesh.mNumFaces * 3)

    material_index = mesh.mMaterialIndex
    # todo make a `numpy-based` loader that makes arrays from pointers
    #  aaaaand copy new face-loader to python mesh retriever

    # return vertex data, index data, material index
    return final_data, faces, material_index


def _get_attr_pos(attr_data, substr, exclude=' '):  # returns [offset, size, orig]
    size = 0
    for f in attr_data:
        if substr in f[2] and exclude not in f[2]:
            return f, int(size), f[0][2] * f[1] // f[0][3].itemsize
        size += f[0][2] * f[1] // f[0][3].itemsize
    return None


def retrieve_mesh_numpy(mesh, attribute_data):
    # 'bitangent' in tangent means it is excluded substring
    params = (('pos', mesh.mVertices, 3), ('normal', mesh.mNormals, 3), ('uv', mesh.mTextureCoords[0], 3),
              ('tangent', mesh.mTangents, 3, 'bitangent'), ('bitangent', mesh.mBitangents, 3))
    params = ((_get_attr_pos(attribute_data, f[0], *f[3:]), f[1], f[2]) for f in params)
    params = [f for f in params if f[0]]

    arr_size = sum((f[0][2] for f in params))
    final_data = np.empty((mesh.mNumVertices, arr_size), dtype='float32')

    for item in filter(bool, params):
        (_, start, size), ptr, ptr_2dim = item
        map_arr = map_ct_pointer(ptr, ctypes.c_float, (mesh.mNumVertices, ptr_2dim))[:, :size] if ptr else 0
        final_data[:, start: start + size] = map_arr

    # todo add other attributes like tangent, bitangent

    faces = np.empty((mesh.mNumFaces, 3), 'uint32')
    m_faces = mesh.mFaces
    for i in range(mesh.mNumFaces):
        curr_face = m_faces[i]
        curr_indices = curr_face.mIndices
        faces[i] = curr_indices[:3]
    faces = faces.reshape(mesh.mNumFaces * 3)

    return final_data, faces, mesh.mMaterialIndex


def retrieve_mesh_python(mesh, _):
    final_data = np.empty((mesh.mNumVertices, 8), dtype='float32')
    faces = []

    m_vertices = mesh.mVertices
    m_normals = mesh.mNormals
    m_texture_coords = mesh.mTextureCoords[0]
    # [WARNING] assimp meshes can have up to 8 texture coordinates, but here we process only 1
    for i in range(mesh.mNumVertices):

        assimp_pos = m_vertices[i]
        assimp_normal = m_normals[i]
        assimp_tex_coords = m_texture_coords[i] if m_texture_coords else ()

        final_data[i] = (assimp_pos.x, assimp_pos.y, assimp_pos.z,
                         assimp_normal.x, assimp_normal.y, assimp_normal.z,
                         assimp_tex_coords.x if m_texture_coords else 0.0,
                         assimp_tex_coords.y if m_texture_coords else 0.0)

    m_faces = mesh.mFaces
    for i in range(mesh.mNumFaces):
        curr_face = m_faces[i]
        curr_indices = curr_face.mIndices
        faces.extend([curr_indices[index] for index in range(curr_face.mNumIndices)])

    material_index = mesh.mMaterialIndex

    # return vertex data, index data, material index
    return final_data, faces, material_index


def get_material_property(ai_mat, prop_name, semantic=0):
    for prop_id in range(ai_mat.mNumProperties):
        prop = ai_mat.mProperties[prop_id].contents
        if prop.mKey.data[1:].decode() == prop_name and prop.mSemantic == semantic:
            print('kek found!')
            return read_data_by_pointer(prop.mData, prop.mDataLength)
    return None


def get_material_texture(ai_mat, tex_type):
    prop = get_material_property(ai_mat, 'tex.file', tex_type)
    return prop[4:-1].decode() if prop is not None else None
