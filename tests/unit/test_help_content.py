import json
from pathlib import Path


def test_help_topics_have_matching_translations_and_required_fields():
    root = Path(__file__).resolve().parents[2] / 'frontend' / 'i18n'
    topics = [json.loads((root / f'help-{language}.json').read_text()) for language in ('uz', 'en', 'ru')]
    expected = [item['id'] for item in topics[0]]
    assert len(expected) == len(set(expected)) == 14
    for locale in topics:
        assert [item['id'] for item in locale] == expected
        for item in locale:
            assert all(isinstance(item.get(key), str) and item[key].strip() for key in ('title', 'what', 'protects', 'limits', 'guardboard', 'example'))
