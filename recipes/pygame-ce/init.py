from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.toolchain import shprint, current_directory
import os
import sh

class PygameCeRecipe(CythonRecipe):
    version = '2.5.2'
    url = 'https://github.com/pygame-community/pygame-ce/archive/refs/tags/{version}.tar.gz'
    depends = ["python3", "sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf"]
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['MESON_CROSS_FILE'] = self.get_cross_file(arch)
        return env

recipe = PygameCeRecipe()
