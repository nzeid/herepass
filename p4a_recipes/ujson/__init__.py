from pythonforandroid.recipe import CompiledComponentsPythonRecipe


class UJsonRecipe(CompiledComponentsPythonRecipe):
    version = "5.4.0"
    url = "https://pypi.python.org/packages/source/u/ujson/ujson-{version}.tar.gz"
    depends = []
    call_hostpython_via_targetpython = False
    need_stl_shared = True


recipe = UJsonRecipe()
