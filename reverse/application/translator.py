from abc import ABC, abstractmethod
from dataclasses import dataclass


class MissingTranslation(KeyError):
    pass


class Translator(ABC):
    @property
    @abstractmethod
    def default_locale(self) -> str: ...

    @abstractmethod
    def translate(self, locale: str, key: str, /, **kwargs: object) -> str: ...

    def bind(self, locale: str) -> "Translation":
        return Translation(self, str(locale))


@dataclass(frozen=True, slots=True)
class Translation:
    translator: Translator
    locale: str

    def __call__(self, key: str, /, **kwargs: object) -> str:
        return self.translator.translate(self.locale, key, **kwargs)
