from collections import namedtuple

from OpenGL.GL import glUniformBlockBinding, glShaderStorageBlockBinding

from ..gl.types import get_type
from ..gl.uniform_buffer import StructuredUniformBuffer
from ..renderer.dependencies.base import DependencyImporter
from .base import BaseRenderer


TextureInfo = namedtuple('TextureInfo', 'name bind_index load_params')


class UniformedRenderer:
    def __init__(self, src_renderer: BaseRenderer, ssbo_list: list=None):
        if ssbo_list is None:
            ssbo_list = []
        self.ssbo_list = ssbo_list
        self.src_renderer = src_renderer
        self.program = src_renderer.shader_prog

        self.buf_info = None
        self.sampler_data = None
        self.attribute_data = None
        self.deps = None

        self._setup_uniforms()
        self.src_renderer.on_created_uniformed(self)

    @staticmethod
    def spec_dep(dep, data):
        for name, offset, size in data:
            offset //= dep.array_type_size
            size //= dep.array_type_size
            # adding setters to dependency object
            dep.add_setter(name, offset, size)

    def process_deps(self, scene):
        self.program.use()
        self.deps = []
        for name, index, data, buf_type in self.buf_info:
            # finding dependency
            try:
                dep = scene.renderer_dependencies[name + buf_type]
            except KeyError:
                dep = DependencyImporter.load(name)(scene, buffer_type=buf_type)
                scene.renderer_dependencies[name + buf_type] = dep
            # setting up
            self.deps.append(dep)
            self.spec_dep(dep, data)
            # binding current uniform block of buffer to required binding point
            func = {'SSBO': glShaderStorageBlockBinding, 'UBO': glUniformBlockBinding}[buf_type]
            func(self.program.gl_program, index, dep.binding_point)

    def _setup_uniforms(self):
        self.program.use()
        # gathering
        attrib_data = self.program.get_attributes()
        ssbo_blocks = self.program.get_ssbo_block_indices()
        uni_blocks = {ind: name for name, ind in self.program.get_uniform_block_indices().items()}  # reversed
        uniforms = self.program.get_uniforms()
        ubos_indices = StructuredUniformBuffer.get_block_indices(self.program, len(uniforms))
        ubos_offsets = StructuredUniformBuffer.get_offsets(self.program, len(uniforms))
        # parts: (name, size, type, ubo_index, ubo_offset)
        uniform_full_data = [(*comm, ind, offs) for comm, ind, offs in zip(uniforms, ubos_indices, ubos_offsets)]

        # processing attributes
        self.attribute_data = []
        for name, attr_size, attr_type in attrib_data:
            curr_type = get_type(attr_type)
            self.attribute_data.append((curr_type, attr_size, name.decode()))

        # getting uniform buffers
        self.buf_info = []
        for index, name in uni_blocks.items():
            curr_data = (part for part in uniform_full_data if part[3] == index)
            self.buf_info.append((name, index, self._get_ubo(curr_data), 'UBO'))

        # getting ssbo data
        for name, index in ssbo_blocks.items():
            self.buf_info.append((name, index, (), 'SSBO'))

        # processing uniforms
        uniforms = {}
        self.sampler_data = {}
        sampler_count = 0
        for name, _, v_type, ubo_index, _ in uniform_full_data:
            if ubo_index != -1:
                continue
            name = name.decode()
            type_name, setter_postfix, _, np_type, setter_wrapper = get_type(v_type)
            if type_name == 'SomeSampler':
                stored_name = name.split('.')[-1].replace('_map', '').replace('Map', '')
                self.sampler_data[stored_name] = TextureInfo(stored_name, sampler_count,
                                                             self.src_renderer.load_params.get(stored_name) or {})
                self.program.get_uniform_setter(name, setter_postfix)(1, sampler_count)
                sampler_count += 1
            else:
                setter = setter_wrapper(self.program.get_uniform_setter(name, setter_postfix))
                uniforms[name] = (setter, np_type)
        self.setters = uniforms

    @staticmethod
    def _get_ubo(data):
        elems = []
        for name, arr_size, v_type, _, ubo_offset in data:
            _, _, type_size, _, setter_wrapper = get_type(v_type)
            elems.append((name.decode(), ubo_offset, arr_size * type_size))
        return elems
