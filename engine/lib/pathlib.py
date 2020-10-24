from os.path import abspath, join, split
import importlib.util


def get_rel_path(file, *join_paths):
    return join(split(abspath(file))[0], *join_paths)


def import_module_from_full_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module_obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module_obj)
    return module_obj


def read_file(filename, mode='r'):
    fp = open(filename, mode)
    text = fp.read()
    fp.close()
    return text
