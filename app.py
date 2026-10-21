import asyncio
import logging
import os

from dotenv import load_dotenv

# Load .env BEFORE importing the bot: agent.agent (CLAUDE_AI_MODEL) and the
# listeners (SLACK_CODE_ENABLED, via load_slack_code_config) read their settings
# at import time, so loading afterwards silently ignored the file.
load_dotenv(dotenv_path=".env", override=False)

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler  # noqa: E402
from slack_bolt.async_app import AsyncApp  # noqa: E402
from slack_sdk.web.async_client import AsyncWebClient  # noqa: E402

from agent.agent import log_model_check  # noqa: E402
from listeners import register_listeners  # noqa: E402

# DEBUG by default (local dev). On a host, LOG_LEVEL=INFO drops the Socket Mode
# PING/PONG noise from the logs.
logging.basicConfig(level=getattr(logging, os.environ.get("LOG_LEVEL", "DEBUG").upper(), logging.DEBUG))

app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    client=AsyncWebClient(
        base_url=os.environ.get("SLACK_API_URL", "https://slack.com/api"),
        token=os.environ.get("SLACK_BOT_TOKEN"),
    ),
)

register_listeners(app)


async def main():
    # Startup self-check: log the configured model + what the gateway actually
    # serves, so a 401 / silent reroute is visible in the init log (never fatal).
    await log_model_check()
    handler = AsyncSocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
