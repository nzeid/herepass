# -*- mode: python ; coding: utf-8 -*-

"""
Copyright (c) 2022 Nader G. Zeid

This file is part of HerePass.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with HerePass. If not, see <https://www.gnu.org/licenses/gpl.html>.
"""

from kivy.tools.packaging.pyinstaller_hooks import (
    get_deps_minimal,
    hookspath,
    runtime_hooks,
)

block_cipher = None

kivy_params = get_deps_minimal(
    audio=None,
    camera=None,
    clipboard=["xclip"],
    # Adding "image" will break things.
    spelling=None,
    text=["sdl2"],
    video=None,
    window=["sdl2"],
)

excluded_hidden_imports = [
    "kivy.core.image.img_dds",
    "kivy.core.image.img_pil",
    "kivy.core.image.img_tex",
    "kivy.graphics.cgl_backend.cgl_debug",
    "kivy.graphics.cgl_backend.cgl_mock",
    "kivy.graphics.svg",
    "kivy.graphics.tesselator",
    "xml.etree.cElementTree",
]

for i in excluded_hidden_imports:
    kivy_params["hiddenimports"].remove(i)

print("\n------------------")
print("| Hidden Imports |")
print("------------------")
for i in kivy_params["hiddenimports"]:
    print(i)
print("------------------\n")

kivy_params["excludes"].extend(excluded_hidden_imports)

excluded_imports = [
    "PIL",
    "_bz2",
    "_lzma",
    "_multibytecodec",
    "_posixshmem",
    "_ssl",
    "bdb",
    "bz2",
    "certifi",
    "csv",
    "docutils",
    "ftplib",
    "gzip",
    "html",
    "http",
    "imp",
    "inspector",
    "joycursor",
    "lzma",
    "mimetypes",
    "mmap",
    "monitor",
    "pdb",
    "pkg_resources",
    "pprint",
    "pydoc",
    "pydoc_data",
    "pygments",
    "quopri",
    "recorder",
    "screen",
    "shlex",
    "showborder",
    "site",
    "socketserver",
    "ssl",
    "statistics",
    "tarfile",
    "termios",
    "textwrap",
    "touchring",
    "tracemalloc",
    "unittest",
    "webbrowser",
    "xmlrpc",
    "zipimport",
]

print("\n--------------------")
print("| Excluded Imports |")
print("--------------------")
for i in excluded_imports:
    print(i)
print("--------------------\n")

kivy_params["excludes"].extend(excluded_imports)

a = Analysis(
    ["main.py"],
    pathex=[],
    datas=[],
    hookspath=hookspath(),
    hooksconfig={},
    runtime_hooks=runtime_hooks(),
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    **kivy_params,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

post_excluded_imports = ["kivy.modules"]

print("\n------------------------------")
print("| Post-Hook Excluded Imports |")
print("------------------------------")
excluded_pos = []
i = 0
for item in a.pure:
    if item[0] in post_excluded_imports:
        excluded_pos.append(i)
    i += 1
while len(excluded_pos):
    i = excluded_pos.pop()
    print(a.pure[i][0])
    del a.pure[i]
print("------------------------------\n")

post_excluded_data = ["kivy_install/modules/"]

print("\n---------------------------")
print("| Post-Hook Excluded Data |")
print("---------------------------")
excluded_pos = []
i = 0
for item in a.datas:
    for e_item in post_excluded_data:
        if item[0].startswith(e_item):
            excluded_pos.append(i)
    i += 1
while len(excluded_pos):
    i = excluded_pos.pop()
    print(a.datas[i][0])
    del a.datas[i]
print("---------------------------\n")

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="HerePass",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
