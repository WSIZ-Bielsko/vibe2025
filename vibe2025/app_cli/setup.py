from cx_Freeze import setup, Executable

setup(
    name="app",
    version="1.0",
    executables=[Executable("a.py")]
)
