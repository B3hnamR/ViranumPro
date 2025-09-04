# ViranumPro Bot

Telegram bot for selling virtual numbers via 5SIM.

- Stack: Python 3.12, FastAPI (webhook), aiogram 3, httpx
- Features:
  - Public: /start, /help, /prices <product>, /countries
  - Private (requires 5SIM token): /profile, /buy <product> [country] [operator]
  - Inline order controls: Check / Finish / Cancel / Ban
  - Background polling for order status and SMS codes

## Run locally (polling)

```bash
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
set TELEGRAM_BOT_TOKEN=your-telegram-bot-token
# optional for purchase/profile
set FIVESIM_TOKEN=your-5sim-bearer-token
python -m app.polling
```

## Run with webhook (local HTTPS reverse proxy or production)

```bash
pip install -r requirements.txt
set TELEGRAM_BOT_TOKEN=your-telegram-bot-token
set BASE_URL=https://your-domain
set TELEGRAM_WEBHOOK_SECRET=random-secret
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker

Build and run webhook image:

```bash
docker build -t viranumpro:latest .
# provide envs via --env-file or -e flags
# Required: TELEGRAM_BOT_TOKEN
# For webhook: BASE_URL, TELEGRAM_WEBHOOK_SECRET
# For 5SIM: FIVESIM_TOKEN

docker run --rm -p 8000:8000 \
  --env-file .env \
  viranumpro:latest
```

Development (polling) image:

```bash
docker build -f Dockerfile.dev -t viranumpro-dev:latest .
docker run --rm \
  --env-file .env \
  viranumpro-dev:latest
```

## Environment variables

See `.env.example` for a complete list.

- TELEGRAM_BOT_TOKEN (required)
- BASE_URL, TELEGRAM_WEBHOOK_SECRET (webhook)
- FIVESIM_TOKEN (purchase/profile)
- PRICES_TTL, COUNTRIES_TTL (cache)
- LOG_LEVEL

## Notes

- Current order storage is in-memory and should be replaced by DB/Redis for production.
- Hosting and reuse flows are pending.
