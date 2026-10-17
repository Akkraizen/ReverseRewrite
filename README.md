> [!IMPORTANT]
> Reverse is back?? \
> Reverse is back!

# What is Reverse?
Reverse is a multifunctional discord bot, which is made for my own discord server, but now it is offline. \
This repository contains a bot code rewrote version.

> [!IMPORTANT]
> Bot under development.

# Functional
- Basic moderation
- Basic Role Play Action
- Squads System
- Audit

## Running

Python 3.13. Install dependencies with `uv sync`, then set in `.env`:

```dotenv
TOKEN=bot_token
DATABASE_URL=sqlite+aiosqlite:///reverse.db   # optional, this is the default
LOG_DIR=logs                                  # optional
```

Run from the project root: `uv run python -m reverse.main`.
On startup the bot applies database migrations (Alembic), then connects to Discord.
Plain `sqlite://` and `postgresql://` URLs are automatically switched to the async
drivers (aiosqlite, asyncpg).

Before the first run, enable two privileged intents in the [Discord Developer Portal](https://discord.com/developers/applications)
(Bot → Privileged Gateway Intents):
- **Server Members Intent**: member updates tell the bot that a timeout was lifted manually;
- **Message Content Intent**: without it Discord returns messages with empty text, and the `contains`
  and `links` filters of `/clear` stop matching anything.

If they are not enabled, Discord closes the connection with error 4014 (Disallowed intents) and the bot does not start.

## General

- `/ping`: the bot's latency, with two values: REST (time of a request to the Discord API)
  and WebSocket (gateway heartbeat).

## Moderation

Commands are registered globally and act on the server where they are used:

- `/warn member reason [days]`: a warning, optionally expiring after `days` days.
  The bot reports the number of active warnings. When the limit (3) is reached, the member
  is muted for a day and their active warnings are lifted.
- `/unwarn member warn_id`: lift a warning.
- `/warns member`: a member's warnings.
- `/clearwarns member`: lift all of a member's warnings (they stay in the history).
- `/ban member reason`: a permanent ban.
- `/unban user reason`: lift a ban.
- `/bans [user]`: the server's active bans, or a user's ban status and history.
- `/mute member minutes reason`: a Discord timeout of 1 to 40320 minutes (28 days).
- `/unmute member reason`: lift a timeout.
- `/mutes member`: whether the member is muted right now, and their mute history.
- `/kick member reason`: kick a member from the server (kicks are not stored in the database).
- `/clear amount [user] [bots] [contains] [links] [attachments]`: delete up to 100 recent messages
  in the channel. Filters combine: only from a user, only from bots, containing text (case-insensitive),
  with links, with attachments. Pinned messages are never deleted. Discord does not allow bulk-deleting
  messages older than 14 days, so the search stops at them; with filters, at most the 500 most recent
  messages are scanned.

Banning requires the Ban Members permission, kicking requires Kick Members, `/clear` requires Manage Messages,
and the other commands require Moderate Members (or Administrator).
The server owner can do anything. You cannot sanction yourself, the bot, the server owner or a member
with an equal or higher role. The bot's role must also be above the member's role.

Records are kept separately for each server. A timeout that expired on its own counts as inactive.
The bot also records bans and timeouts issued manually in Discord: it takes the moderator and the reason
from the audit log, so it needs the View Audit Log permission. If a sanction is lifted manually, the bot marks
the record as revoked (this works without the audit log too). `/mutes` and `/bans` also check the status
against Discord in case the bot missed an event, for example while it was offline.
If the action in Discord succeeded but the record could not be saved to the database, the command reports a partial success.

## Languages

The bot replies in the language of the user's Discord client: Russian (the default) or English.
Command descriptions are translated too. Translations live in `reverse/modules/<module>/locales/*.toml`;
to add a language, create a file named after a Discord locale code (for example, `uk.toml`) with the same
keys as `ru.toml`.

## Development

```sh
uv run python -m unittest                    # tests, no Discord connection needed
uv run ruff check . && uv run ruff format .  # lint and format
uv run pyright                               # type check
uv run alembic -c migrations/alembic.ini revision --autogenerate -m "description"   # new migration after schema changes
```

PostgreSQL migration tests run only when `TEST_POSTGRES_URL` points to a throwaway database
(they drop the `public` schema):

```sh
docker run -d --rm --name reverse-test-db -e POSTGRES_PASSWORD=test -p 127.0.0.1:55432:5432 postgres:17-bookworm
TEST_POSTGRES_URL=postgresql+asyncpg://postgres:test@127.0.0.1:55432/postgres uv run python -m unittest tests.test_migrations
```

## Docker Compose

Add the values from `.env.example` to `.env`: TOKEN and POSTGRES_PASSWORD.

```sh
docker compose up -d --build
docker compose logs -f bot
```

Compose runs the bot and PostgreSQL 17; the bot waits until the database is ready. Data is stored in the
`postgres_data` volume, logs in `bot_logs`. The password is passed to the bot via `PGPASSWORD`,
so it does not need to be URL-encoded.

The database is reachable from the host at `localhost:${POSTGRES_PORT}` (5432 by default), for example for an IDE
or for running the bot outside Docker: `DATABASE_URL=postgresql+asyncpg://reverse:password@localhost:5432/reverse`.
The port is bound to `127.0.0.1` only; to accept connections from other machines, set `POSTGRES_HOST=0.0.0.0`.
`POSTGRES_PASSWORD` is applied only when the volume is first created; to change it later, run
`docker compose exec db psql -U reverse -c "ALTER USER reverse PASSWORD '...'"`.

Stop with `docker compose down`. Named volumes are kept.

