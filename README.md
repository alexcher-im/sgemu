# Sgemu rendering engine
Rendering engine in pure python. In development.

## Features
- Pure Python + GLSL, using OpenGL 4.3
- Both Blinn-Phong and PBR (Physically-Based Rendering) lighting
- Point lights, Area lights (using Linearly transformed cosines method)
- HDR, Bump mapping, Volumetric fog (cone-shaped primitives)
- Bloom, DOF (Depth Of Field)
- Spatial audio, using OpenAL
- UI library for HUD displays (not used in main.py, shown in gui_t.py)

## Running
```bash
git clone https://github.com/alexcher-im/sgemu
cd sgemu
pip install -r requirements.txt
git clone https://github.com/KhronosGroup/glTF-Sample-Models
python3 main.py
```

There may be a pyassimp bug with ctypes structure size (pyassimp v4.1.4), it is already fixed, but still not in PyPi repos. If so, you need to fix this manually or use older assimp dll.
To fix you need to find class `String`, field `length` (file `structs.py`, line 79) and change `c_size_t` to `c_uint32` in pyassimp source code.


## Controls for main.py
`WASD` to move forward, left, backwards and right

`arrow up` and `arrow down` to move up and down

`shift`, `ctrl`, `ctrl+shift` to increase moving or DOF cutoff change speed by 10, 100 and 1000 respectively

`Q` and `R` to roll the camera

`T` and `Y` to change Depth Of Field cutoff length
