from discord import Embed

from reverse.config.colors import Colors

colors = Colors()

def build_error_embed(description: str) -> Embed:
    return build_embed("Ошибка!", description, colors.red)

def build_embed(title: str, description: str, color: int) -> Embed:
    res = Embed()
    res.title = title
    res.description = description
    res.colour = color
    return res

def build_until_ready_embed() -> Embed:
    embed = Embed(
        title=f'Подождите!',
        description=f'Этот процесс может занять некоторое время',
        color=colors.red
    )
    return embed
