from dataclasses import dataclass
from pathlib import Path

from skypackages.utils import (
    compute_file_md5,
    copy_file,
    yaml_dump,
    yaml_load)


@dataclass
class SkybuildPackagesPaths:
    root: Path

    def __post_init__(self):
        self.packages = self.root / 'packages'
        self.aliases = self.root / 'aliases'
        self.sources = self.root / 'sources'
        self.view = self.root / 'view'
        self.tmp = self.root / 'tmp'


class SkybuildPackageManager:
    def __init__(self, root):
        self.root = Path(root)
        self.paths = SkybuildPackagesPaths(self.root)
        self.aliases = SkybuildAliases(self.paths.aliases)

    def add_source(self, alias, source):
        # download the source
        downloaded_file = source.download(dest=self.tmp)
        assert downloaded_file.name == source.file_name
        assert downloaded_file.bytes == source.bytes

        # import into folder and create view
        md5 = compute_file_md5(downloaded_file)
        package_file = self.paths.packages / f'{md5}{source.file_name}'
        if not package_file.exists():
            copy_file(downloaded_file, package_file)

        view_path = self.view / (
            f'{source.file_name.stem}-{md5[:8]}{source.file_name.suffix}')
        if not view_path.exists:
            view_path.symlink_to(package_file.relative_to(view_path))

        # save source details
        source.save_details(md5)

        # apply aliases
        self.aliases.add(alias, md5)
        self.aliases.save()


class SkybuildAliases(dict):
    def __init__(self, root):
        self.root = Path(root)
        self.file_path = self.root / 'aliases.yaml'
        if self.file_path.exists():
            self.load()

    def add(self, alias, md5):
        self.setdefault(alias, set()).add(md5)

    def remove(self, alias, md5):
        if alias in self and md5 in self[alias]:
            self[alias].remove(md5)
            if not self[alias]:
                self.pop(alias)

    def load(self):
        for alias, md5s in yaml_load(self.file_path.read_text()).items():
            for md5 in md5s:
                self.add(md5)

    def save(self):
        self.file_path.write_text(yaml_dump(
            {alias: sorted(md5s) for alias, md5s in self.items()}))
