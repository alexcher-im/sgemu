from typing import Union, Iterable, Optional

from glm import ivec2, vec2

cvec = ivec2
vec_type = Union[vec2, ivec2, Iterable, cvec]
nullable_vec_type = Optional[vec_type]
