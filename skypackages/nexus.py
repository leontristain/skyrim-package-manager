import bbcode
from dataclasses import dataclass
import datetime
import html
from pathlib import Path
from pynxm import Nexus
from urllib.parse import urlparse

from skypackages.sources.nexus import NexusPackageSource
from skypackages.utils import (
    compute_file_md5,
    download_url,
    ReadOnlyDictDataAttribute,
    yaml_dump,
    yaml_load)


@dataclass
class NexusMod:
    api: Nexus
    data: dict

    allow_rating = ReadOnlyDictDataAttribute('allow_rating')
    author = ReadOnlyDictDataAttribute('author')
    available = ReadOnlyDictDataAttribute('available')
    category_id = ReadOnlyDictDataAttribute('category_id')
    contains_adult_content = ReadOnlyDictDataAttribute('contains_adult_content')
    created_time = ReadOnlyDictDataAttribute('created_time')
    created_timestamp = ReadOnlyDictDataAttribute('created_timestamp')
    description = ReadOnlyDictDataAttribute('description')
    domain_name = ReadOnlyDictDataAttribute('domain_name')
    endorsement = ReadOnlyDictDataAttribute('encorsement')
    endorsement_count = ReadOnlyDictDataAttribute('endorsement_count')
    game_id = ReadOnlyDictDataAttribute('game_id')
    mod_id = ReadOnlyDictDataAttribute('mod_id')
    name = ReadOnlyDictDataAttribute('name')
    picture_url = ReadOnlyDictDataAttribute('picture_url')
    status = ReadOnlyDictDataAttribute('status')
    summary = ReadOnlyDictDataAttribute('summary')
    updated_time = ReadOnlyDictDataAttribute('updated_time')
    updated_timestamp = ReadOnlyDictDataAttribute('updated_timestamp')
    uploaded_by = ReadOnlyDictDataAttribute('uploaded_by')
    uploaded_users_profile_url = ReadOnlyDictDataAttribute('uploaded_users_profile_url')
    user = ReadOnlyDictDataAttribute('user')
    version = ReadOnlyDictDataAttribute('version')

    @property
    def game(self):
        return self.domain_name

    @property
    def description_html(self):
        parser = bbcode.Parser()

        def render_size(name, value, options, parent, context):
            return f'<span style="font-size: 4;">{value}</span>'

        parser.add_formatter('size', render_size)
        return html.unescape(parser.format(self.description))

    @property
    def url(self):
        return f'https://www.nexusmods.com/{self.domain_name}/mods/{self.mod_id}'

    @classmethod
    def from_url(cls, api, url):
        url_parts = urlparse(url)
        assert url_parts.netloc == 'www.nexusmods.com', (
            f'entered url netloc must be www.nexusmods.com; you entered '
            f'{url_parts.netloc}')

        url_path_parts = Path(url_parts.path.strip('/')).parts
        game = None
        mod_id = None
        for i, part in enumerate(url_path_parts):
            if part == 'mods':
                if i - 1 >= 0:
                    game = url_path_parts[i - 1]
                if i + 1 < len(url_path_parts):
                    mod_id = int(url_path_parts[i + 1])
        assert game and mod_id, (
            f'could not parse a game and a mod id from url {url}')

        return cls.from_game_and_id(api=api, game=game, mod_id=mod_id)

    @classmethod
    def from_game_and_id(cls, api, game, mod_id):
        data = api.mod_details(game, mod_id)
        return cls(api=api, data=data)

    @property
    def file_list(self):
        return [
            NexusModFile(self.api, self.game, self.mod_id, data)
            for data in self.api.mod_file_list(
                self.game, self.mod_id)['files']
            if data['category_name']
        ]


@dataclass
class NexusModFile:
    api: Nexus
    game: str
    mod_id: int
    data: dict

    file_id = ReadOnlyDictDataAttribute('file_id')
    name = ReadOnlyDictDataAttribute('name')
    version = ReadOnlyDictDataAttribute('version')
    category_id = ReadOnlyDictDataAttribute('category_id')
    category_name = ReadOnlyDictDataAttribute('category_name')
    is_primary = ReadOnlyDictDataAttribute('is_primary')
    size = ReadOnlyDictDataAttribute('size')
    file_name = ReadOnlyDictDataAttribute('file_name')
    uploaded_timestamp = ReadOnlyDictDataAttribute('uploaded_timestamp')
    uploaded_time = ReadOnlyDictDataAttribute('uploaded_time')
    mod_version = ReadOnlyDictDataAttribute('mod_version')
    external_virus_scan_url = ReadOnlyDictDataAttribute('external_virus_scan_url')
    description = ReadOnlyDictDataAttribute('description', postprocess=html.unescape)
    size_kb = ReadOnlyDictDataAttribute('size_kb')
    changelog_html = ReadOnlyDictDataAttribute('changelog_html')
    content_preview_link = ReadOnlyDictDataAttribute('content_preview_link')

    @property
    def uploaded_datetime(self):
        return datetime.datetime.fromtimestamp(self.uploaded_timestamp)

    @property
    def package_source(self):
        return NexusPackageSource.from_mod_file(self)

    def generate_download_links(self):
        return {
            info['short_name']: info['URI']
            for info in self.api.mod_file_download_link(
                    self.game, self.mod_id, self.file_id)}

    def download_into(self, folder):
        folder = Path(folder)
        index_file = folder / 'nexus_download_index.yaml'
        if index_file.exists():
            index = yaml_load(index_file.read_text())
        else:
            index = {}

        key = (
            f'{self.file_id} '
            f'{self.file_name} '
            f'{self.version} '
            f'{self.uploaded_timestamp}')

        existing = index.get(key)
        if existing:
            file_name = existing.get('file_name')
            md5 = existing.get('md5')
            if (file_name and md5 and
                    (folder / file_name).exists() and
                    compute_file_md5(folder / file_name) == md5):
                assert int(
                    (folder / file_name).stat().st_size / 1024) == self.size, (
                        'found in cache but size mismatch')
                return folder / file_name

        target = folder / self.file_name
        if target.exists():
            target.unlink()

        links = self.generate_download_links()
        assert links, f'no download links for {self}'

        default_server = 'Nexus CDN'
        preferred_server = 'Los Angeles'
        if preferred_server in links:
            link = links[preferred_server]
        elif default_server in links:
            link = links[default_server]
        else:
            link = list(links.values())[0]

        assert not target.exists(), f'{target} unexpectedly exists'
        download_url(link, target)
        assert target.exists(), f'{target} still does not exist after download'

        md5 = compute_file_md5(target)
        index[key] = {'file_name': self.file_name, 'md5': md5}
        index_file.write_text(yaml_dump(index))

        return target
