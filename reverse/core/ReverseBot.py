import logging
from os import listdir

import discord
from discord.ext.commands import AutoShardedBot
from loguru import logger

from reverse.config.config import load_config
from reverse.structure.singleton import Singleton


class ReverseBot(Singleton, AutoShardedBot):
    def __init__(self):
        super().__init__("r.", intents=discord.Intents().all())
        self.config = load_config()
        self.__token: str = self.config["token"]
        self.cogs_path: str = "cogs"
        logging.info("Bot was initialized")

    async def setup_hook(self):
        await self.__add_cogs()

    async def __add_cogs(self) -> None: #Добавление когов
        cogs_status = []
        for filename in listdir(self.cogs_path):
            if filename.endswith('.py') and filename != "__init__.py":
                cog_path = f'{self.cogs_path}.{filename[:-3]}'
                result = await self.load_extension(cog_path)
                cogs_status.append(result)
        for cog in self.cogs:
            logger.info(f"[{cog}]: Загружен")

        if len(self.cogs.keys()) != self.__get_total_cogs_count():
            logger.error("Ошибка в загрузке модулей")

    def __get_total_cogs_count(self) -> int:
        return sum(map(lambda file: file.endswith('.py') and not file == "__init__.py", listdir(self.cogs_path)))

    def run(self, **kwargs):
        super().run(token=self.__token, reconnect=True)
