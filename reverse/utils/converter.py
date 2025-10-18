import re

from discord.ext.commands import Converter, BadArgument, Context


class TimeConverter(Converter):
    def __init__(self):
        self.time_regex = re.compile(r"(?:(\d{1,5})([чсмдdmsh]))+?")
        self.time_dict = {
            "ч": 3600,
            "с": 1,
            "м": 60,
            "д": 86400,
            "d": 86400,
            "m": 60,
            "s": 1,
            "h": 3600
        }

    async def convert(self, context: Context, argument: str, **kwargs) -> int:
        args = argument.lower()
        matches = re.findall(self.time_regex, args)
        time = 0
        for key, value in matches:
            try:
                time += self.time_dict[value] * float(key)
            except KeyError:
                raise BadArgument(f"{value} is an invalid time key! ч|м|с|д|d|m|s|h are valid arguments")
            except ValueError:
                raise BadArgument(f"{key} is not a number!")
        return round(time)