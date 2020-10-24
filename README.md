# Sgemu game engine
Game engine in pure python. Probably incomplete

## Installation
Just download it, do a `pip install -r requirements.txt`.

Note: on Windows you may have problems with PyOpenGL and PyOpenGL_accelerate. Then just download prebuilt [wheels](www.lfd.uci.edu/~gohlke/pythonlibs) for Widows.

Also there may be a pyassimp bug with ctypes structure size (pyassimp v4.1.4), it is already fixed, but still not in PyPi repos. If so, you need to fix this manually or use older assimp dll.
To fix you need to find class `String`, field `length` (line 79) and change its type to `c_uint32`.

## Models to use:
To run `main.py` you need to download a [gltf sample models](github.com/KhronosGroup/glTF-Sample-Models).

Or just do `git clone https://github.com/KhronosGroup/glTF-Sample-Models` in project home.