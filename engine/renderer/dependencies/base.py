from ...event.base import BaseEventReceiver
from ...gl.shader_buffer import StructuredShaderBuffer, StructuredShaderArrayBuffer
from ...gl.uniform_buffer import StructuredUniformBuffer, StructuredUniformArrayBuffer


class UniformBufferBindingPointManager:
    max_count = 0
    points = []

    @classmethod
    def get_available_index(cls):
        if not cls.points:
            cls.max_count = StructuredUniformBuffer.get_max_binding_points()
            cls.points = [None] * cls.max_count
        for i, point in enumerate(cls.points):
            if point is None:
                return i
        return None

    @classmethod
    def take_point(cls, buffer):
        index = cls.get_available_index()
        if index is None:
            raise BufferError("[CRITICAL] maximum number of binding points reached")  # todo add this to logging
        cls.points[index] = buffer
        buffer.bind_to_block(index)
        return index


class BaseRendererDependence(BaseEventReceiver):
    DEPENDENCY_NAME = 'BaseRendererDependence'
    BUFFER_IS_ARRAY = False

    def __init__(self, scene, take_point=True, buffer_type='UBO', structure=(), **buf_kwargs):
        buffers = [{'SSBO': StructuredShaderBuffer, 'UBO': StructuredUniformBuffer},
                   {'SSBO': StructuredShaderArrayBuffer, 'UBO': StructuredUniformArrayBuffer}]
        buffer_type = buffers[self.BUFFER_IS_ARRAY][buffer_type]
        self.scene = scene
        self.buffer = buffer_type(self.DEPENDENCY_NAME, structure, **buf_kwargs)
        self.array_type_size = self.buffer.get_buffer_data().dtype.itemsize
        self.setters = {}
        self.binding_point = None
        super(BaseRendererDependence, self).__init__()
        if take_point:
            self.binding_point = UniformBufferBindingPointManager.take_point(self.buffer)

    def add_setter(self, name, offset, size):
        func = self.buffer.get_array_chunk_setter(offset, size)
        end_point = offset + size
        self.setters[name] = func
        self.recalculate_size(end_point)

    def upload_buffer(self):
        self.buffer.upload()

    def recalculate_size(self, end_point):
        if end_point > self.buffer.size:
            self.buffer.resize(end_point)


# todo this shitty import system suxxxx, rewrite
class DependencyImporter:
    importers = []

    @classmethod
    def add_importer(cls, module_obj):
        cls.importers.append(module_obj.import_module)

    @classmethod
    def load(cls, name):
        for func in reversed(cls.importers):
            try:
                return func(name).CurrentDependence
            except ImportError:
                pass
        raise ImportError("Dependency %s not found" % name)


DependencyImporter.add_importer(__import__('_importer', globals(), locals(), level=1))
