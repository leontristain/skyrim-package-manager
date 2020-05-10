from cached_property import cached_property
import os
from pathlib import Path
import subprocess


DEFAULT_7Z_EXE = 'C:\\Program Files\\7-Zip\\7z.exe'


class Tarball7zOperationError(Exception):
    pass


class Tarball:
    def __init__(self, tarball_path, bin_7z=DEFAULT_7Z_EXE):
        self.tarball = Path(tarball_path)
        self.bin_7z = bin_7z
        assert self.tarball.exists(), f'tarball {self.tarball} does not exist'

    @cached_property
    def fomod_root(self):
        for path in sorted(self.contents, key=lambda p: len(str(p))):
            if (path.name.lower() == 'moduleconfig.xml' and
                    path.parent.name.lower() == 'fomod'):
                return path.parent.parent

    @cached_property
    def contents(self):
        command = [
            self.bin_7z,
            'l',  # list contents
            '-ba',  # suppress headers; undocumented
            '-slt',  # show technical information for l command
            str(self.tarball)  # operate on this file
        ]

        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            command_str = ' '.join(command)
            raise Tarball7zOperationError(
                f'command `{command_str}; returncode={p.returncode}; '
                f'stdout: `{stdout}`; stderr: `{stderr}`')

        files_info_data = (
            stdout.decode('utf-8').split(f'{os.linesep}{os.linesep}'))
        files_info_data = [
            info_data.strip() for info_data in files_info_data
            if info_data.strip()]

        file_infos = {}
        for info_data in files_info_data:
            path, info = self.parse_file_info_data(info_data)
            assert path not in file_infos, (
                f'encountered the same path `{path}` twice in {self.tarball}')
            file_infos[path] = info

        return {key: value for key, value in sorted(file_infos.items())}

    def extract(self, dest):
        command = [
            self.bin_7z,
            'x', str(self.tarball),  # extract this file
            f'-o{dest}',  # to this destination
            '-aoa'  # overwrite all existing files without prompt
        ]

        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            command_str = ' '.join(command)
            raise Tarball7zOperationError(
                f'command `{command_str}; returncode={p.returncode}; '
                f'stdout: `{stdout}`; stderr: `{stderr}`')

    @staticmethod
    def parse_file_info_data(file_info_data):
        info = {}
        for line in file_info_data.splitlines():
            line = line.strip()
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            info[key] = value
        try:
            path = Path(info['Path'])
        except Exception:
            print(f'{file_info_data}')
            raise
        info['Path'] = path
        return path, info
