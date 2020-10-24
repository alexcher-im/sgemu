from typing import Union, Optional

import numpy as np
from glm import ivec4, vec4

from ...gl.texture import Texture2D
from ..adaptive import ResizeModes, AlignModes
from ..base import BaseElement
from ..typedefs import vec_type, nullable_vec_type, cvec

texture_type = Optional[Union[np.ndarray, int, ivec4, str, Texture2D, vec4]]


class ImageElement(BaseElement):
    def __init__(self, parent: 'BaseElement', pos: vec_type = cvec(), size: nullable_vec_type = None,
                 resize_act=ResizeModes.stretch, align_act=AlignModes.stretch,
                 picture: texture_type = 1, set_orig_size=False):
        super().__init__(parent, pos, size, resize_act, align_act)
        self.render_data.color = vec4(1)
        self.set_picture(picture, set_orig_size)

    def set_picture(self, picture: texture_type, set_orig_size=False):
        if isinstance(picture, str):
            width, height = self.render_data.opengl_texture.load_from_file(picture, gamma_corr=False)
        elif isinstance(picture, Texture2D):
            self.render_data.opengl_texture = picture
            width, height = picture.width, picture.height
        else:
            width, height = self.render_data.set_data(picture)

        if set_orig_size:
            self.set_size((width, height))
