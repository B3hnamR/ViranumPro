# Changelog

All notable changes to this project will be documented in this file.
The format is based on Keep a Changelog, and the project aims (eventually) to follow Semantic Versioning.

## [0.4.1] - Dockerization and docs
### Added
- Dockerfile (webhook mode) with healthcheck and uvicorn entrypoint.
- Dockerfile.dev (polling mode) for local development.
- .env.example with required and optional environment variables.
- README.md with quick start (polling/webhook), Docker build/run commands, and env references.

### Notes
- Minimal env var required: `TELEGRAM_BOT_TOKEN`.
- Webhook requires: `BASE_URL` and `TELEGRAM_WEBHOOK_SECRET`.
- 5SIM private endpoints require: `FIVESIM_TOKEN`.

## [0.4.0] - Activation purchase flow
### Added
- `/buy <product> [country] [operator]` command with FSM wizard to collect missing parameters and optional `maxPrice` (effective only when `operator=any`).
- Inline order controls: `Check`, `Finish`, `Cancel`, `Ban`.
- Background polling for order status and SMS codes with backoff.
- Ephemeral in-memory order tracking (to be replaced with DB/Redis in production).

### Changed
- Improved help text to document the purchase flow and usage tips.

## [0.3.0] - FiveSim integration and caching
### Added
- `app/services/fivesim.py`: async `FiveSimClient` (httpx) with timeouts/retries and `FiveSimError`.
- `/profile` command to show 5SIM balance and rating (requires `FIVESIM_TOKEN`).
- In-memory TTL cache for public endpoints: `PRICES_TTL`, `COUNTRIES_TTL`.

### Changed
- `app/main.py` now uses `FiveSimClient` and shares a global `httpx.AsyncClient`.

## [0.2.0] - Public commands and utilities
### Added
- `/help`, `/prices <product>`, `/countries` commands.
- Global `httpx.AsyncClient` for guest endpoints.

### Changed
- Improved logging and error handling around HTTP calls and parsing.

## [0.1.0] - Initial scaffold
### Added
- `app/main.py`: FastAPI webhook application with `X-Telegram-Bot-Api-Secret-Token` validation.
- aiogram 3 Dispatcher/Router with `/start` command and basic welcome.
- Health endpoint: `GET /healthz`.
- `requirements.txt` with core dependencies (aiogram, fastapi, uvicorn, httpx, pydantic, python-dotenv).

### Notes
- Webhook registration on startup when `BASE_URL` is provided; pending updates are dropped.
- Local development recommended via polling runner (added later in v0.2.0+/0.3.0).

---

Known limitations
- Order storage is in-memory (non-persistent); replace with DB/Redis for production.
- Hosting and reuse flows are not implemented yet.
- Error mapping for 5SIM responses is basic and will be refined.
