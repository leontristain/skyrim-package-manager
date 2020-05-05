import hashlib
import os
from pathlib import Path
import requests
import shutil
from tqdm import tqdm
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


class ReadOnlyDictDataAttribute:
    def __init__(self, attr, postprocess=None):
        self.attr = attr
        self.postprocess = postprocess

    def __get__(self, obj, type=None):
        value = obj.data[self.attr]
        return self.postprocess(value) if self.postprocess else value


def download_url(url, output_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 kilobyte
    with tqdm(total=total_size, unit='iB', unit_scale=True) as t:
        with open(output_path, 'wb') as f:
            for data in response.iter_content(block_size):
                t.update(len(data))
                f.write(data)
    if total_size != 0:
        assert t.n == total_size, (
            f'response is nonzero yet progress bar result is not total_size; '
            f'something is wrong: {t.n} {total_size}')
