"""Apply known name readings before a caller converts ordinary numbers."""
from pathlib import Path
import json

DEFAULT_REGISTRY = Path(__file__).resolve().parents[2] / 'config/video_language.json'


def apply_name_readings(text: str, registry_path=DEFAULT_REGISTRY) -> str:
    registry = json.loads(Path(registry_path).read_text(encoding='utf-8-sig'))
    aliases = {}
    for entry in registry['protected_names']:
        for alias in [entry['canonical_name'], entry['display_name'], *entry.get('known_incorrect_readings', [])]:
            previous = aliases.setdefault(alias, entry['reading_text'])
            if previous != entry['reading_text']:
                raise ValueError('Conflicting pronunciation aliases')
    result = text
    for alias in sorted(aliases, key=len, reverse=True):
        result = result.replace(alias, aliases[alias])
    return result
