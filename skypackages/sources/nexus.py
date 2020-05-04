from dataclasses import dataclass


@dataclass
class NexusPackageSource:
    game_id: str
    mod_id: int
    file_id: int
    file_name: str
    size: str

    @classmethod
    def from_mod_file(cls, mod_file):
        return cls(
            game_id=mod_file.game_id,
            mod_id=mod_file.mod_id,
            file_id=mod_file.file_id,
            file_name=mod_file.file_name,
            size=mod_file.size)
