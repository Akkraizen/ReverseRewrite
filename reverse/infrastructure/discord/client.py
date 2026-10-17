from collections.abc import Sequence
from functools import partial

from arc import CommandLocaleRequest, GatewayClient, LocaleResponse, OptionLocaleRequest
from hikari import Activity, ActivityType, GatewayBot, Intents

from reverse.application.plugin import Plugin
from reverse.infrastructure.i18n.translator import TomlTranslator

INTENTS = Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS | Intents.MESSAGE_CONTENT


def _command_key(request: CommandLocaleRequest | OptionLocaleRequest) -> str:
    return "commands." + ".".join(request.qualified_name)


def command_locale(translator: TomlTranslator, request: CommandLocaleRequest) -> LocaleResponse:
    return LocaleResponse(description=translator.lookup(request.locale, f"{_command_key(request)}.description"))


def option_locale(translator: TomlTranslator, request: OptionLocaleRequest) -> LocaleResponse:
    description = translator.lookup(
        request.locale, f"{_command_key(request)}.options.{request.name}"
    ) or translator.lookup(request.locale, f"options.{request.name}")
    return LocaleResponse(description=description)


class ReverseBot:
    def __init__(self, token: str, plugins: Sequence[Plugin], translator: TomlTranslator) -> None:
        self.gateway = GatewayBot(token, intents=INTENTS, logs=None, banner=None)
        self.client = GatewayClient(self.gateway, provided_locales=translator.translated_locales())
        self.client.set_command_locale_provider(partial(command_locale, translator))
        self.client.set_option_locale_provider(partial(option_locale, translator))
        self._plugins = list(plugins)
        for plugin in self._plugins:
            plugin.install(self.client)

    async def start(self) -> None:
        await self.gateway.start(activity=Activity(name="на своего Создателя", type=ActivityType.WATCHING))

    async def join(self) -> None:
        await self.gateway.join()

    async def close(self) -> None:
        try:
            if self.gateway.is_alive:
                await self.gateway.close()
        finally:
            for plugin in self._plugins:
                await plugin.close()
