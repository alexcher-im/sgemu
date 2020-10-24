from ctypes import c_uint8, cast, POINTER, c_void_p

import numpy as np


def map_ct_pointer(ptr, data_type=c_uint8, shape=(4,)):
    for part in shape[::-1]:
        data_type = data_type * part
    ptr = cast(ptr, POINTER(data_type))

    # mapping ctypes array
    return np.array(ptr[0], copy=False)


def int2ptr(address, data_type=c_uint8):
    address = c_void_p(address)
    ptr = cast(address, POINTER(data_type))
    return ptr


def int2array(address, data_type, size):
    ptr = int2ptr(address, data_type)
    return map_ct_pointer(ptr, data_type, size)
