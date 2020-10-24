def import_module(module_name: str):
    return __import__(module_name, globals(), locals(), level=1)
