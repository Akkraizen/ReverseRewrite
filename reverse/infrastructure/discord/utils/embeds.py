from collections.abc import Callable

from hikari import Embed

from reverse.settings import EMBED_COLORS

EMBED_LIMIT = 4096
_OVERFLOW_RESERVE = 64


def build_embed(title: str, description: str = "", colour: int = EMBED_COLORS.info) -> Embed:
    return Embed(title=title, description=description or None, colour=colour)


def build_listing(title: str, header: str, lines: list[str], *, history: str, overflow: Callable[[int], str]) -> Embed:
    text = header + (f"\n\n{history}" if header and lines else "")
    for shown, line in enumerate(lines):
        if len(text) + len(line) + _OVERFLOW_RESERVE > EMBED_LIMIT:
            text += "\n" + overflow(len(lines) - shown)
            break
        text += "\n" + line
    return build_embed(title, text.strip())
