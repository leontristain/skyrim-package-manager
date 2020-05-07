from dataclasses import dataclass, asdict

from skypackages.utils import yaml_dump, yaml_load


@dataclass
class NexusPackageSource:
    game: str
    mod_id: int
    file_id: int
    file_name: str
    size: str

    def __repr__(self):
        return (
            f'NexusPackageSource('
            f'{self.game}, '
            f'{self.mod_id}, '
            f'{self.file_id}, '
            f'{self.file_name}, '
            f'{self.size})')

    @property
    def url(self):
        return f'https://www.nexusmods.com/{self.game}/mods/{self.mod_id}'

    @property
    def entry(self):
        return {**{'class': self.__class__.__name__}, **asdict(self)}

    def validate(self, file_path):
        assert file_path.name == self.file_name
        size = int(file_path.stat().st_size / 1024)
        assert size == self.size, (
            f'file sizes do not match for {file_path}, got {size}, expected '
            f'{self.size}')

    def save_details(self, blob_id, sources_folder):
        sources_file = sources_folder / f'{blob_id}.yaml'
        sources = {}
        if sources_file.exists():
            sources = yaml_load(sources_file.read_text())

        entries = sources.setdefault('entries', [])
        if self.entry not in entries:
            entries.append(self.entry)

        sources_file.write_text(yaml_dump(sources))

    @classmethod
    def from_mod_file(cls, mod_file):
        return cls(
            game=mod_file.game,
            mod_id=mod_file.mod_id,
            file_id=mod_file.file_id,
            file_name=mod_file.file_name,
            size=mod_file.size)

    @classmethod
    def from_entry(cls, entry):
        return cls(**entry)
