from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from skypackages.sources import NexusPackageSource
from skypackages.utils import (
    compute_file_md5,
    copy_file,
    create_shortcut,
    yaml_dump,
    yaml_load)


@dataclass
class SkybuildPackagesPaths:
    root: Path

    def __post_init__(self):
        self.blobs = self.root / 'blobs'
        self.aliases = self.root / 'aliases'
        self.sources = self.root / 'sources'
        self.view = self.root / 'view'
        self.tmp = self.root / 'tmp'
        self.download_cache = self.root / 'download_cache'

    def create_all(self):
        self.blobs.mkdir(parents=True, exist_ok=True)
        self.aliases.mkdir(parents=True, exist_ok=True)
        self.sources.mkdir(parents=True, exist_ok=True)
        self.view.mkdir(parents=True, exist_ok=True)
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.download_cache.mkdir(parents=True, exist_ok=True)


class SkybuildPackageManager:
    def __init__(self, root):
        self.root = Path(root)
        self.paths = SkybuildPackagesPaths(self.root)
        self.paths.create_all()
        self.aliases = SkybuildAliases(self.paths.aliases)
        self.sources = SkybuildSources(self.paths.sources)

    def add_source(self, alias, source, file_path):
        source.validate(file_path)

        # import into folder and create view
        file_name = Path(source.file_name)
        md5 = compute_file_md5(file_path)
        blob_id = f'{md5}{file_name.suffix}'
        blob = self.paths.blobs / blob_id
        if not blob.exists():
            copy_file(file_path, blob)

        view_path = (
            self.paths.view / f'{file_name.stem}-{md5[:8]}{file_name.suffix}.lnk')
        if not view_path.exists():
            create_shortcut(blob, view_path)

        # save source details
        source.save_details(blob_id, self.paths.sources)

        # apply aliases
        self.aliases.add(alias, blob_id)


class SkybuildSources:
    SOURCE_CLASSES = {
        class_.__name__: class_ for class_ in [
            NexusPackageSource
        ]
    }

    def __init__(self, root):
        self.root = Path(root)

    def fetch(self, blob_id):
        sources = []
        file_path = self.root / f'{blob_id}.yaml'
        if file_path.exists():
            data = yaml_load(file_path.read_text())
            if data:
                for entry in data['entries']:
                    class_ = self.SOURCE_CLASSES[entry.pop('class')]
                    sources.append(class_.from_entry(entry))
        return sources


class SkybuildAliases:
    def __init__(self, root):
        self.root = Path(root)
        self.file_path = self.root / 'aliases.yaml'

    @contextmanager
    def session(self, read_only=False):
        if self.file_path.exists():
            data = yaml_load(self.file_path.read_text())
        else:
            data = {}
        yield data
        if not read_only:
            self.file_path.write_text(yaml_dump(data))

    @property
    def data(self):
        with self.session(read_only=True) as aliases_data:
            return aliases_data

    def add(self, alias, blob_id):
        with self.session() as data:
            blob_ids = data.setdefault(alias, [])
            if blob_id not in blob_ids:
                blob_ids.append(blob_id)

    def remove(self, alias, blob_id):
        with self.session() as data:
            if alias in data and blob_id in data[alias]:
                data[alias].remove(blob_id)
                if not data[alias]:
                    data.pop(alias)
