import hashlib
import os
from pathlib import Path
import shutil
import yaml


class IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentedSafeDumper, self).increase_indent(flow, False)


def yaml_dump(data, sort_keys=True):
    return yaml.dump(data,
                     Dumper=IndentedSafeDumper,
                     default_flow_style=False,
                     sort_keys=sort_keys)


def yaml_load(text):
    return yaml.safe_load(text)


def compute_file_md5(file_path, verbose=False):
    '''
    Utility function that computes the md5 checksum of a file at the given
    file path

    @param file_path: path to the file to get md5 checksum for
    @param verbose: print an informative line to stdout before computing md5
    @return: the computed md5 hexdigest
    '''
    if verbose:
        print(f'computing md5 for {file_path}')
    hash_md5 = hashlib.md5()
    with open(str(file_path), 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def copy_file(src, dest):
    src = Path(src)
    dest = Path(dest)

    try:
        os.link(src, dest)
    except OSError:
        shutil.copyfile(src, dest)
