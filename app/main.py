import asyncio
import logging
import os
import time
from typing import Optional, Dict, Any, List, Tuple, Set

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Update
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from app.services.fivesim import FiveSimClient, FiveSimError

# -------------------------------------------------
# Logging & Settings
# -------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("viranumpro")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
BASE_URL: Optional[str] = (os.getenv("BASE_URL", "").strip() or None)
WEBHOOK_PATH = os.getenv("TELEGRAM_WEBHOOK_PATH", "/telegram/webhook").strip()

# Optional 5SIM user token for private endpoints (profile, orders, purchase)
FIVESIM_TOKEN = os.getenv("FIVESIM_TOKEN", "").strip() or None

# Async HTTP client for 5SIM public/user API (created on startup or lazily)
http_client: Optional[httpx.AsyncClient] = None
fs_client: Optional[FiveSimClient] = None

# In-memory order tracking (ephemeral; replace with DB later)
ORDERS: Dict[str, Dict[str, Any]] = {}
USER_LAST_ORDER: Dict[int, str] = {}

# Dispatcher/Router and FSM storage
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()


# -------------------------------------------------
# Simple in-memory TTL cache
# -------------------------------------------------
class TTLCache:
    def __init__(self) -> None:
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return None
        exp, value = item
        if exp < now:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: float) -> None:
        self._store[key] = (time.time() + ttl, value)


cache = TTLCache()
PRICES_TTL = float(os.getenv("PRICES_TTL", "60"))  # seconds
COUNTRIES_TTL = float(os.getenv("COUNTRIES_TTL", "300"))  # seconds


# -------------------------------------------------
# Utilities
# -------------------------------------------------
def _format_text(text: str, limit: int = 4000) -> str:
    return text[:limit]


def _flatten_product_prices(data: Dict[str, Any]) -> List[Tuple[str, str, float, int]]:
    """Flatten 5sim prices response (product-filtered or nested all) into (country, operator, cost, count)."""
    rows: List[Tuple[str, str, float, int]] = []
    for country, level1 in data.items():
        if not isinstance(level1, dict):
            continue
        # case A: directly operator -> {cost, count, rate}
        if any(isinstance(v, dict) and ("cost" in v or "count" in v) for v in level1.values()):
            for operator, info in level1.items():
                if not isinstance(info, dict):
                    continue
                if "cost" in info or "count" in info:
                    cost = float(info.get("cost", 0) or 0)
                    count = int(info.get("count", 0) or 0)
                    rows.append((country, operator, cost, count))
            continue
        # case B: one more level (product -> operator -> {...})
        for _product, operators in level1.items():
            if not isinstance(operators, dict):
                continue
            for operator, info in operators.items():
                if not isinstance(info, dict):
                    continue
                if "cost" in info or "count" in info:
                    cost = float(info.get("cost", 0) or 0)
                    count = int(info.get("count", 0) or 0)
                    rows.append((country, operator, cost, count))
    return rows


def _count_country_operators(country_obj: Dict[str, Any]) -> int:
    cnt = 0
    for k, v in country_obj.items():
        if k in ("iso", "prefix") or (isinstance(k, str) and k.startswith("text_")):
            continue
        if isinstance(v, dict):
            cnt += 1
    return cnt


def _get_fs_client() -> FiveSimClient:
    global fs_client, http_client
    if fs_client is None:
        fs_client = FiveSimClient(token=FIVESIM_TOKEN, client=http_client)
    return fs_client


def _order_keyboard(order_id: str) -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Check", callback_data=f"order:check:{order_id}")
    kb.button(text="Finish", callback_data=f"order:finish:{order_id}")
    kb.button(text="Cancel", callback_data=f"order:cancel:{order_id}")
    kb.button(text="Ban", callback_data=f"order:ban:{order_id}")
    kb.adjust(2, 2)
    return kb.as_markup()


async def _poll_order_updates(bot: Bot, order_id: str, chat_id: int) -> None:
    """Poll order status and notify on new SMS or status changes."""
    backoff = [2, 4, 8, 15, 30]
    seen_sms_ids: Set[int] = set()
    last_status: Optional[str] = None

    while True:
        try:
            data = await _get_fs_client().order_check(order_id=order_id)
        except Exception as e:
            logger.warning("Order %s polling error: %s", order_id, e)
            await asyncio.sleep(5)
            continue

        status = str(data.get("status"))
        sms_list = data.get("sms") or []
        new_codes: List[str] = []
        for s in sms_list:
            sid = s.get("id")
            code = s.get("code")
            if sid is None:
                # fallback dedup
                txt = s.get("text")
                sid = hash((txt, s.get("date")))
            if sid not in seen_sms_ids:
                seen_sms_ids.add(sid)
                if code:
                    new_codes.append(str(code))

        if new_codes:
            await bot.send_message(chat_id, _format_text("New code(s) received: " + ", ".join(new_codes)))

        if status != last_status:
            last_status = status
            await bot.send_message(chat_id, _format_text(f"Order status: {status}"))

        if status in {"FINISHED", "CANCELED", "TIMEOUT", "BANNED"}:
            break

        # sleep with increasing backoff
        delay = backoff[0] if backoff else 30
        await asyncio.sleep(delay)
        if len(backoff) > 1:
            backoff.pop(0)


# -------------------------------------------------
# FSM for purchase (Activation)
# -------------------------------------------------
class BuyStates(StatesGroup):
    wait_product = State()
    wait_country = State()
    wait_operator = State()
    wait_maxprice = State()


# -------------------------------------------------
# Handlers
# -------------------------------------------------
@router.message(CommandStart())
async def on_start(message: types.Message) -> None:
    text = (
        "Hello!\n"
        "I am a virtual-number sales bot.\n\n"
        "Available commands:\n"
        "/start - show welcome\n"
        "/help - show help\n"
        "/prices <product> - list cheapest options for a product (public data)\n"
        "/countries - list available countries (public data)\n"
        "/profile - show 5SIM balance/rating (if configured)\n"
        "/buy <product> [country] [operator] - start purchase (activation)\n"
    )
    await message.answer(_format_text(text))


@router.message(Command("help"))
async def on_help(message: types.Message) -> None:
    text = (
        "Help:\n"
        "- Use /prices <product> to see public prices and availability from 5SIM.\n"
        "  Example: /prices telegram\n"
        "- Use /countries to see available countries.\n"
        "- Use /profile to check 5SIM balance and rating (requires token).\n"
        "- Use /buy <product> [country] [operator] to purchase an activation number.\n"
        "  You can type 'any' for country or operator.\n"
        "  After options, you may specify a max price (operator must be 'any' for per-request maxPrice).\n"
    )
    await message.answer(_format_text(text))


@router.message(Command("profile"))
async def on_profile(message: types.Message) -> None:
    if not FIVESIM_TOKEN:
        await message.answer("5SIM token is not configured.")
        return
    try:
        profile = await _get_fs_client().get_user_profile()
    except FiveSimError as e:
        logger.warning("5SIM error on profile: %s", e)
        await message.answer("Failed to fetch 5SIM profile. Please try again later.")
        return
    except Exception as e:
        logger.exception("HTTP error on profile: %s", e)
        await message.answer("Failed to fetch profile. Please try again later.")
        return

    balance = profile.get("balance")
    rating = profile.get("rating")
    vendor = profile.get("vendor")
    email = profile.get("email")

    lines = [
        "5SIM Profile:",
        f"- Email: {email}",
        f"- Vendor: {vendor}",
        f"- Balance: {balance}",
        f"- Rating: {rating}",
    ]
    await message.answer(_format_text("\n".join(lines)))


@router.message(Command("prices"))
async def on_prices(message: types.Message) -> None:
    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /prices <product>\nExample: /prices telegram")
        return

    product = parts[1].strip().lower()
    cache_key = f"prices:product:{product}"
    cached = cache.get(cache_key)
    if cached is None:
        try:
            data = await _get_fs_client().get_guest_prices(product=product)
        except FiveSimError as e:
            logger.warning("5SIM error on prices: %s", e)
            await message.answer("Failed to fetch prices from 5SIM. Please try again later.")
            return
        except Exception as e:
            logger.exception("HTTP error on prices: %s", e)
            await message.answer("Failed to fetch prices. Please try again later.")
            return
        cache.set(cache_key, data, PRICES_TTL)
    else:
        data = cached

    rows = _flatten_product_prices(data)
    if not rows:
        await message.answer("No prices found for this product.")
        return

    rows.sort(key=lambda x: (x[2], -x[3]))

    lines = [f"Top options for product '{product}':"]
    for i, (country, operator, cost, count) in enumerate(rows[:15], start=1):
        lines.append(f"{i}. {country} / {operator} — cost: {cost}, available: {count}")

    await message.answer(_format_text("\n".join(lines)))


@router.message(Command("countries"))
async def on_countries(message: types.Message) -> None:
    cache_key = "countries:list"
    cached = cache.get(cache_key)
    if cached is None:
        try:
            data = await _get_fs_client().get_countries()
        except FiveSimError as e:
            logger.warning("5SIM error on countries: %s", e)
            await message.answer("Failed to fetch countries from 5SIM. Please try again later.")
            return
        except Exception as e:
            logger.exception("HTTP error on countries: %s", e)
            await message.answer("Failed to fetch countries. Please try again later.")
            return
        cache.set(cache_key, data, COUNTRIES_TTL)
    else:
        data = cached

    items: List[Tuple[str, int, str]] = []  # (display_name, count, key)
    for key, obj in data.items():
        if not isinstance(obj, dict):
            continue
        display = obj.get("text_en") or str(key)
        count_ops = _count_country_operators(obj)
        if count_ops > 0:
            items.append((str(display), count_ops, str(key)))

    if not items:
        await message.answer("No countries available.")
        return

    items.sort(key=lambda x: x[0].lower())

    lines = ["Available countries (with operator count):"]
    for name, cnt, key in items[:25]:
        lines.append(f"- {name} ({key}) — operators: {cnt}")

    await message.answer(_format_text("\n".join(lines)))


# ---------------------- BUY FLOW ----------------------
@router.message(Command("buy"))
async def on_buy(message: types.Message, state: FSMContext) -> None:
    if not FIVESIM_TOKEN:
        await message.answer("5SIM token is not configured. Purchase is unavailable.")
        return

    parts = (message.text or "").split()
    # /buy <product> [country] [operator]
    args = parts[1:]
    data: Dict[str, Any] = {}

    if len(args) >= 1:
        data["product"] = args[0].lower()
    if len(args) >= 2:
        data["country"] = args[1].lower()
    if len(args) >= 3:
        data["operator"] = args[2].lower()

    await state.update_data(**data)

    if "product" not in data:
        await state.set_state(BuyStates.wait_product)
        await message.answer("Enter product name (e.g., telegram):")
        return

    if "country" not in data:
        await state.set_state(BuyStates.wait_country)
        await message.answer("Enter country (use key from /countries or 'any'):")
        return

    if "operator" not in data:
        await state.set_state(BuyStates.wait_operator)
        await message.answer("Enter operator (e.g., beeline) or 'any':")
        return

    await state.set_state(BuyStates.wait_maxprice)
    await message.answer("Enter max price (number) or type 'skip':")


@router.message(BuyStates.wait_product)
async def buy_product(message: types.Message, state: FSMContext) -> None:
    await state.update_data(product=(message.text or "").strip().lower())
    await state.set_state(BuyStates.wait_country)
    await message.answer("Enter country (use key from /countries or 'any'):")


@router.message(BuyStates.wait_country)
async def buy_country(message: types.Message, state: FSMContext) -> None:
    await state.update_data(country=(message.text or "").strip().lower())
    await state.set_state(BuyStates.wait_operator)
    await message.answer("Enter operator (e.g., beeline) or 'any':")


@router.message(BuyStates.wait_operator)
async def buy_operator(message: types.Message, state: FSMContext) -> None:
    await state.update_data(operator=(message.text or "").strip().lower())
    await state.set_state(BuyStates.wait_maxprice)
    await message.answer("Enter max price (number) or type 'skip':")


@router.message(BuyStates.wait_maxprice)
async def buy_maxprice(message: types.Message, state: FSMContext) -> None:
    txt = (message.text or "").strip().lower()
    max_price: Optional[float] = None
    if txt not in {"", "skip", "none"}:
        try:
            max_price = float(txt)
        except Exception:
            await message.answer("Invalid number. Please enter a numeric value or 'skip':")
            return

    data = await state.get_data()
    product = data.get("product")
    country = data.get("country")
    operator = data.get("operator")

    await state.clear()

    # Note: per 5SIM docs, maxPrice works only if operator="any"
    try:
        order = await _get_fs_client().buy_activation(
            country=country,
            operator=operator,
            product=product,
            max_price=max_price if operator == "any" else None,
        )
    except FiveSimError as e:
        logger.warning("5SIM buy error: %s payload=%s", e, getattr(e, "payload", None))
        await message.answer("Purchase failed. Try different options or later.")
        return
    except Exception as e:
        logger.exception("HTTP error on buy: %s", e)
        await message.answer("Purchase failed due to network error. Please try again.")
        return

    order_id = str(order.get("id"))
    phone = order.get("phone")
    price = order.get("price")
    status = order.get("status")
    expires = order.get("expires")

    ORDERS[order_id] = {
        "data": order,
        "seen_sms_ids": set(),
        "chat_id": message.chat.id,
        "user_id": message.from_user.id if message.from_user else None,
    }
    USER_LAST_ORDER[message.from_user.id] = order_id if message.from_user else order_id

    text = (
        "Order created:\n"
        f"- ID: {order_id}\n"
        f"- Phone: {phone}\n"
        f"- Product: {product}\n"
        f"- Country/Operator: {country}/{operator}\n"
        f"- Price: {price}\n"
        f"- Status: {status}\n"
        f"- Expires: {expires}\n"
        "Use the buttons to manage the order."
    )
    await message.answer(_format_text(text), reply_markup=_order_keyboard(order_id))

    # Start background polling for updates (status/SMS)
    bot = message.bot
    asyncio.create_task(_poll_order_updates(bot, order_id, message.chat.id))


# ---------------------- ORDER BUTTONS ----------------------
@router.callback_query(F.data.startswith("order:"))
async def on_order_action(callback: types.CallbackQuery) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        await callback.answer("Invalid action.", show_alert=True)
        return
    _, action, order_id = parts

    try:
        if action == "check":
            data = await _get_fs_client().order_check(order_id=order_id)
            status = data.get("status")
            phone = data.get("phone")
            sms = data.get("sms") or []
            codes = ", ".join([s.get("code") for s in sms if s.get("code")]) if sms else "-"
            msg = f"Status: {status}\nPhone: {phone}\nCodes: {codes}"
            await callback.message.answer(_format_text(msg), reply_markup=_order_keyboard(order_id))
        elif action == "finish":
            data = await _get_fs_client().order_finish(order_id=order_id)
            await callback.message.answer(_format_text(f"Order finished. Status: {data.get('status')}"))
        elif action == "cancel":
            data = await _get_fs_client().order_cancel(order_id=order_id)
            await callback.message.answer(_format_text(f"Order canceled. Status: {data.get('status')}"))
        elif action == "ban":
            data = await _get_fs_client().order_ban(order_id=order_id)
            await callback.message.answer(_format_text(f"Order banned. Status: {data.get('status')}"))
        else:
            await callback.answer("Unknown action.", show_alert=True)
            return
    except FiveSimError as e:
        logger.warning("5SIM order action error: %s payload=%s", e, getattr(e, "payload", None))
        await callback.message.answer("Operation failed. Please try again later.")
    except Exception as e:
        logger.exception("HTTP error on order action: %s", e)
        await callback.message.answer("Network error. Please try again later.")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


# Register router
dp.include_router(router)


# -------------------------------------------------
# FastAPI App & Webhook lifecycle
# -------------------------------------------------
app = FastAPI(title="ViranumPro Bot", version="0.4.0")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup() -> None:
    # Create bot lazily to avoid constructing with empty token
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Startup continues but bot will not be functional.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    app.state.bot = bot

    # Create global HTTP client
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            headers={"Accept": "application/json"},
        )

    # Pre-create fs_client with shared http client
    _get_fs_client()

    if BASE_URL:
        webhook_url = f"{BASE_URL.rstrip('/')}{WEBHOOK_PATH}"
        if not WEBHOOK_SECRET:
            logger.warning("WEBHOOK secret is not set. Consider setting TELEGRAM_WEBHOOK_SECRET for extra security.")
        try:
            await bot.set_webhook(
                url=webhook_url,
                secret_token=WEBHOOK_SECRET or None,
                allowed_updates=[
                    "message",
                    "callback_query",
                    # Add more update types when needed
                ],
                drop_pending_updates=True,
            )
            logger.info("Webhook configured: %s", webhook_url)
        except Exception as e:
            logger.exception("Failed to set webhook: %s", e)
    else:
        logger.warning(
            "BASE_URL is not set. Webhook is not configured. Set BASE_URL for production or use polling during development."
        )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    bot: Optional[Bot] = getattr(app.state, "bot", None)
    try:
        if bot:
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.session.close()
    except Exception as e:
        logger.exception("Error during bot shutdown: %s", e)

    global http_client
    try:
        if http_client is not None:
            await http_client.aclose()
    except Exception as e:
        logger.exception("Error during http client shutdown: %s", e)
    finally:
        http_client = None


@app.post(WEBHOOK_PATH)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None),
):
    # Validate secret token if configured
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="invalid webhook secret")

    bot: Optional[Bot] = getattr(app.state, "bot", None)
    if not bot:
        raise HTTPException(status_code=503, detail="bot not initialized")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid JSON")

    try:
        update = Update.model_validate(data)
    except Exception as e:
        logger.warning("Invalid update payload: %s", e)
        raise HTTPException(status_code=422, detail="invalid update")

    try:
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.exception("Error while processing update: %s", e)
        # Always respond 200 to avoid Telegram retries for handled exceptions
    return JSONResponse({"ok": True})


# Local run (webhook):
#   uvicorn app.main:app --host 0.0.0.0 --port 8000
# Required env vars:
#   TELEGRAM_BOT_TOKEN=...  BASE_URL=https://<your-domain>  TELEGRAM_WEBHOOK_SECRET=<random>
# Optional env vars:
#   FIVESIM_TOKEN=...  PRICES_TTL=60  COUNTRIES_TTL=300
