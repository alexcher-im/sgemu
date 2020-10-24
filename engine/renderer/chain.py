class RenderChain:
    def __init__(self, first_pass, *second_pass):
        self.first = first_pass
        self.second = second_pass
        if second_pass:
            self.second[0].fbo.add_depth_buffer()  # should we?
        self._cached_draw_data = None  # only used when there's only 1 renderer

        # for compatibility with SceneRenderer
        self.attribute_data = first_pass.attribute_data
        self.sampler_data = first_pass.sampler_data

    def draw(self, out_fbo, data):
        self.first_pass(data)
        self.second_pass(out_fbo)

    def first_pass(self, data):
        if self.second:
            self.first.draw(self.second[0].fbo, data)
        else:
            self._cached_draw_data = data

    def second_pass(self, out_fbo):
        if self.second:
            for renderer, fbo_data in zip(self.second, self.second[1:]):
                renderer.draw(fbo_data.fbo, renderer.meshes)
            if len(self.second) > 0:
                self.second[-1].draw(out_fbo, self.second[-1].meshes)
        else:
            self.first.draw(out_fbo, self._cached_draw_data)
