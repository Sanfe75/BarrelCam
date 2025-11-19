#import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    'include_files':'templates/',
    #'packages': ["cadquery-ocp", "OCP", "vtk"]
    }

setup(
    name="Barrel Cam Editor",
    version="0.9.3",
    description="An editor for Barrel Cams",
    options={"build_exe": build_exe_options},
    executables=[Executable("barrelcameditor.py",
                            icon="icon.ico",
                            base="Win32GUI")])

