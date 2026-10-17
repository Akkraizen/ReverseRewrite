import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Self, override

import hikari

from reverse.application.translator import MissingTranslation, Translator


def _language(locale: str) -> str:
    return locale.split("-", 1)[0]


def _flatten(table: Mapping[str, object], prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, value in table.items():
        if isinstance(value, Mapping):
            flat |= _flatten(value, f"{prefix}{key}.")
        else:
            flat[f"{prefix}{key}"] = str(value)
    return flat


class TomlTranslator(Translator):
    def __init__(self, catalogs: Mapping[str, Mapping[str, str]], fallback: str = hikari.Locale.RU) -> None:
        self.fallback = str(fallback)
        self._catalogs = {str(locale): dict(catalog) for locale, catalog in catalogs.items()}
        if self.fallback not in self._catalogs:
            raise ValueError(f"No catalog for the fallback locale `{self.fallback}`.")

    @classmethod
    def load(cls, directories: Iterable[Path], fallback: str = hikari.Locale.RU) -> Self:
        catalogs: dict[str, dict[str, str]] = {}
        for directory in directories:
            for path in sorted(directory.glob("*.toml")):
                entries = _flatten(tomllib.loads(path.read_text("utf-8")))
                catalog = catalogs.setdefault(path.stem, {})
                if duplicates := catalog.keys() & entries.keys():
                    raise ValueError(f"{path}: keys already defined by another module: {', '.join(sorted(duplicates))}")
                catalog |= entries
        return cls(catalogs, fallback)

    @property
    @override
    def default_locale(self) -> str:
        return self.fallback

    @property
    def catalogs(self) -> Mapping[str, Mapping[str, str]]:
        return self._catalogs

    def resolve(self, locale: str) -> str:
        locale = str(locale)
        if locale in self._catalogs:
            return locale
        language = _language(locale)
        return next((known for known in self._catalogs if _language(known) == language), self.fallback)

    def translated_locales(self) -> list[hikari.Locale]:
        return [locale for locale in hikari.Locale if self.resolve(locale) != self.fallback]

    def lookup(self, locale: str, key: str) -> str | None:
        return self._catalogs[self.resolve(locale)].get(key)

    @override
    def translate(self, locale: str, key: str, /, **kwargs: object) -> str:
        text = self.lookup(locale, key) or self._catalogs[self.fallback].get(key)
        if text is None:
            raise MissingTranslation(key)
        return text.format(**kwargs)
