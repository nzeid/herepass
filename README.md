# HerePass

## Introduction

HerePass is yet another password manager, but:

- Offline! No cloud, no internet.

- Cross-platform! Built on [Kivy](https://kivy.org/) to target all major operating systems.

- File-based! You specify portable files to create, access, or update.

- Flexible! Label and organize your data any way you want.

- Open source! We have nothing to hide.

- Standards-based! Uses strong and well known key derivation and encryption algorithms.

## Development Notes

Tooling:
```
pip3.10 install --upgrade pytest isort black flake8
```

Lint/format:
```
isort ./ -s "" --profile black --ext py && black ./ && flake8 --max-line-length=88 ./;
```

Debian dependencies:
```
sudo apt install xclip
```

On the `venv` for building with Pyinstaller:
```
pip3.10 install --no-binary pycryptodome,pydantic,ujson,kivy[base] pyinstaller pycryptodome pydantic ujson kivy[base]
```

Pyinstaller initial:
```
pyinstaller --name HerePass -F main.py
```

Pyinstaller subsequent:
```
pyinstaller --clean --upx-dir ~/Desktop/upx-3.96-amd64_linux HerePass.spec;
```

Buildozer preparations on Debian distributions:
```
sudo apt install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

python3.10 -m venv ~/Desktop/python3.10-buildozer-venv
source ~/Desktop/python3.10-buildozer-venv/bin/activate;
pip3.10 install --upgrade pip Cython==0.29.19
pip3.10 install --no-binary pycryptodome,pydantic,ujson,kivy[base] pycryptodome pydantic ujson kivy[base]
```

## Contributing

Please communicate changes over this project's GitLab/GitHub pages.

- [https://github.com/nzeid/herepass](https://github.com/nzeid/herepass)
- [https://gitlab.com/nzeid/herepass](https://gitlab.com/nzeid/herepass)

## License

Copyright (c) 2022 Nader G. Zeid

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see [https://www.gnu.org/licenses/gpl.html](https://www.gnu.org/licenses/gpl.html).
