import bbcode
from dataclasses import dataclass
import datetime
import html
from pathlib import Path
from pynxm import Nexus
from urllib.parse import urlparse

from skypackages.sources.nexus import NexusPackageSource
from skypackages.utils import ReadOnlyDictDataAttribute


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
            NexusModFile(self.api, self.game_id, self.mod_id, data)
            for data in self.api.mod_file_list(
                self.game_id, self.mod_id)['files']
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
    version = ReadOnlyDictDataAttribute('name')
    category_id = ReadOnlyDictDataAttribute('name')
    category_name = ReadOnlyDictDataAttribute('category_name')
    is_primary = ReadOnlyDictDataAttribute('is_primary')
    size = ReadOnlyDictDataAttribute('size')
    file_name = ReadOnlyDictDataAttribute('file_name')
    uploaded_timestamp = ReadOnlyDictDataAttribute('uploaded_timestamp')
    uploaded_time = ReadOnlyDictDataAttribute('uploaded_time')
    mod_version = ReadOnlyDictDataAttribute('mod_version')
    external_virus_scan_url = ReadOnlyDictDataAttribute('external_virus_scan_url')
    description = ReadOnlyDictDataAttribute('description')
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
