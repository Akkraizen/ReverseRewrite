from asyncio import run

from dotenv import load_dotenv
from loguru import logger

from reverse.infrastructure.data.database import create_engine, create_sessions, migrate
from reverse.infrastructure.discord.client import ReverseBot
from reverse.infrastructure.i18n.translator import TomlTranslator
from reverse.log import configure_logging
from reverse.modules.general.plugin import LOCALES as GENERAL_LOCALES
from reverse.modules.general.plugin import GeneralPlugin
from reverse.modules.moderation.plugin import LOCALES as MODERATION_LOCALES
from reverse.modules.moderation.plugin import ModerationPlugin
from reverse.settings import Settings


async def serve(settings: Settings) -> None:
    engine = create_engine(settings.database_url)
    sessions = create_sessions(engine)
    translator = TomlTranslator.load([GENERAL_LOCALES, MODERATION_LOCALES])
    bot = ReverseBot(
        settings.token,
        plugins=[GeneralPlugin(translator), ModerationPlugin(sessions, translator)],
        translator=translator,
    )
    try:
        await bot.start()
        await bot.join()
    finally:
        await bot.close()
        await engine.dispose()


def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    configure_logging(settings.log_dir)
    logger.info("Applying database migrations")
    migrate(settings.database_url)
    run(serve(settings))


if __name__ == "__main__":
    main()
