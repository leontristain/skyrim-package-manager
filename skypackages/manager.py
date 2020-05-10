from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import shutil

from skypackages.sources import NexusPackageSource, GenericPackageSource
from skypackages.tarballs import Tarball
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
        # folder of tarball blobs
        self.blobs = self.root / 'blobs'

        # folder of metadata for tarball blobs
        self.meta = self.root / 'meta'

        # folder for alias management; aliases form a many-to-many relationship
        # with tarball blobs
        self.aliases = self.root / 'aliases'

        # folder for sources; sources form a many-to-one relationship with
        # tarball blobs
        self.sources = self.root / 'sources'

        # folder for shortcuts to blobs created with names resembling the
        # original names of source files; useful for manual browsing
        self.view = self.root / 'view'

        # tmp folder; various processes may use this folder for temporary work
        self.tmp = self.root / 'tmp'

        # download cache; nexus downloads go here first before getting imported
        # into blobs
        self.download_cache = self.root / 'download_cache'

    def create_all(self):
        self.blobs.mkdir(parents=True, exist_ok=True)
        self.meta.mkdir(parents=True, exist_ok=True)
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

    def update_source(self, blob_id, source):
        source.save_details(blob_id, self.paths.sources)

    def fetch_tarball(self, blob_id):
        return Tarball(self.paths.blobs / blob_id)

    def meta(self, blob_id):
        meta_file = self.paths.meta / f'{blob_id}.yaml'
        if meta_file.exists():
            meta = yaml_load(meta_file.read_text())
        else:
            blob = self.paths.blobs / blob_id
            tarball = Tarball(blob)
            meta = {
                'filelist': [str(key) for key in tarball.contents.keys()],
                'fomod_root': str(tarball.fomod_root)
            }
            meta_file.write_text(yaml_dump(meta))
        return meta

    def clean_tmp(self):
        shutil.rmtree(self.paths.tmp)
        self.paths.tmp.mkdir(parents=True, exist_ok=True)


class SkybuildSources:
    SOURCE_CLASSES = {
        class_.__name__: class_ for class_ in [
            NexusPackageSource,
            GenericPackageSource
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
        self.aliases_file = self.root / 'aliases.yaml'
        self.selection_file = self.root / 'selection.yaml'

    @contextmanager
    def session(self, file_, read_only=False):
        if file_.exists():
            data = yaml_load(file_.read_text())
        else:
            data = {}
        yield data
        if not read_only:
            file_.write_text(yaml_dump(data))

    @property
    def data(self):
        with self.session(self.aliases_file, read_only=True) as aliases_data:
            return aliases_data

    def add(self, alias, blob_id):
        with self.session(self.aliases_file) as data:
            blob_ids = data.setdefault(alias, [])
            if blob_id not in blob_ids:
                blob_ids.append(blob_id)

    def rename(self, old_alias, new_alias):
        with self.session(self.aliases_file) as data:
            if old_alias not in data:
                raise Exception(
                    f'cannot rename {old_alias} to {new_alias}; {old_alias} '
                    f'is not a currently valid alias')
            if new_alias in data:
                raise Exception(
                    f'cannot rename {old_alias} to {new_alias}; {new_alias} '
                    f'is already an existing valid alias')
            data[new_alias] = data.pop(old_alias)

    def remove(self, alias, blob_id):
        with self.session(self.aliases_file) as data:
            if alias in data and blob_id in data[alias]:
                data[alias].remove(blob_id)
                if not data[alias]:
                    data.pop(alias)

    def get_selections(self):
        all_selections = {}
        with (
            self.session(self.aliases_file, read_only=True),
            self.session(self.selection_file, read_only=True)) as (
                aliases, selection):
            for alias, blob_ids in aliases.items():
                selected = None
                if alias in selection:
                    selected = selection[alias]
                elif len(blob_ids) == 1:
                    selected = blob_ids[0]
                if not selected:
                    raise Exception(
                        f'alias {alias} does not have a valid selection')
        return all_selections

    def get_selection(self, alias):
        with self.session(self.selection_file, read_only=True) as selection:
            if alias in selection:
                return selection['alias']
        with self.session(self.aliases_file, read_only=True) as aliases:
            if alias in aliases:
                blob_ids = aliases[alias]
                if len(blob_ids) == 1:
                    return blob_ids[0]

    def set_selection(self, alias, blob_id):
        with self.session(self.aliases_file, read_only=True) as aliases:
            if alias not in aliases or blob_id not in aliases[alias]:
                raise Exception(
                    f'cannot set selection for alias {alias} to be blob_id '
                    f'{blob_id}; alias does not exist or does not contain '
                    f'the blob_id')

        with self.session(self.selection_file) as selection:
            selection[alias] = blob_id
