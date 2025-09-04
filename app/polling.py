import asyncio
import logging
import os
from typing import Optional

import httpx
from aiogram import Bot

# Reuse the same Dispatcher/Router and shared objects from the webhook app
import app.main as app_main
from app.main import dp


async def main() -> None:
    """Run the bot in long-polling mode for local development/testing."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    logger = logging.getLogger("viranumpro.polling")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")

    bot = Bot(token=token)

    # Create shared HTTP client for 5SIM guest calls (same headers/timeouts as webhook app)
    app_main.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        headers={"Accept": "application/json"},
    )

    # Ensure webhook is removed so getUpdates works
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning("Failed to delete webhook (may be not set): %s", e)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "callback_query",
            ],
        )
    finally:
        logger.info("Shutting down...")
        try:
            if app_main.http_client is not None:
                await app_main.http_client.aclose()
        except Exception:
            pass
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
