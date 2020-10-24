import platform
from opcode import opmap

import numpy as np


SHOULD_DISABLE_ON_PYPY = True
_do_not_wrap = platform.python_implementation().lower() == 'pypy'


def wrap(inline=(), force=False):
    return lambda func: _wrap(func, inline, force)


def _wrap(src_func, inline, force):
    if not force and _do_not_wrap and SHOULD_DISABLE_ON_PYPY:
        return src_func

    code = src_func.__code__
    code_class = (lambda: 0).__code__.__class__
    function_class = (lambda: 0).__class__

    new_const = list(code.co_consts)
    new_code = bytearray(code.co_code)
    const_ids = {}

    for string, const in inline.items():
        if string in code.co_names:
            new_const.append(const)
            const_ids[string] = len(new_const) - 1

    for i in range(0, len(new_code), 2):
        if new_code[i] == opmap['LOAD_GLOBAL']:
            new_code[i] = opmap['LOAD_CONST']
            current_obj_name = code.co_names[new_code[i + 1]]
            new_code[i + 1] = const_ids[current_obj_name]

    new_code_obj = code_class(code.co_argcount, code.co_kwonlyargcount, code.co_nlocals, code.co_stacksize,
                              code.co_flags, bytes(new_code), tuple(new_const), code.co_names, code.co_varnames,
                              code.co_filename, code.co_name, code.co_firstlineno, code.co_lnotab, code.co_freevars,
                              code.co_cellvars)
    new_func_obj = function_class(new_code_obj, src_func.__globals__, src_func.__name__)

    return new_func_obj


if __name__ == '__main__':
    @wrap(inline={'np': np})
    def test_func():
        b = np.empty(4)
        return b

    print(test_func())
