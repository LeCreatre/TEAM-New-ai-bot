
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from openai import OpenAI

# --- Load env ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHATS = [cid.strip() for cid in os.getenv("ALLOWED_CHATS","").split(",") if cid.strip()]

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("Please set BOT_TOKEN and OPENAI_API_KEY in .env")

# --- Init ---
bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
oai = OpenAI(api_key=OPENAI_API_KEY)

# --- Constants ---
TEAM_LINK = "https://teamuni.uz"
TOUR_3D = "https://my.matterport.com/show/?m=xoz1yxpFF7t"
ADMISSIONS_CHAT = "https://t.me/teamuni_uz"
PHONE = "+998 71 200 20 60"

# Load knowledge base
KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.md")
with open(KB_PATH, "r", encoding="utf-8") as f:
    KNOWLEDGE = f.read()

SYSTEM_PROMPT = """Ты — AI‑консультант TEAM University. Отвечай вежливо, кратко и по‑человечески. 
ОТВЕЧАЙ ТОЛЬКО на вопросы, которые напрямую связаны с TEAM University 
(программы, поступление, дедлайны, стоимость, события, кампус, контакты, 3D тур, и т.п.).
Если вопрос вне тематики TEAM University — откажись и вежливо объясни, что отвечаешь только 
по TEAM University, и предложи задать профильный вопрос или воспользоваться кнопками.

Правила:
1) Будь полезным и конкретным: отвечай ровно по вопросу; при необходимости уточняй 1‑2 момента.
2) Не выдумывай факты. Если данных нет в базе знаний — честно скажи, как уточнить у Admissions.
3) Включай в ответ ссылки/контакты, если они релевантны (3D тур, сайт, чат Admissions, телефон).
4) Сохраняй разговорный тон, избегай канцелярита."""

# Simple keyword gate to reject clearly off-topic queries before LLM
TEAM_KEYWORDS = [
    "team university", "team uni", "тим университет", "тим уни", "тимуни", "teamuni",
    "pre-foundation", "foundation", "ifc", "бакалавр", "ba (hons)", "кампус", "lsbu",
    "поступлен", "прием", "admissions", "стоимость", "оплата", "дедлайн", "3d", "тур",
    "комьюнити", "ивент", "мероприят", "стипенд", "грант", "startup challenge", "компас", "кафедра"
]

def is_team_related(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in TEAM_KEYWORDS)

def main_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="3D Кампус Тур", url=TOUR_3D)
    kb.button(text="Контакты", callback_data="contacts")
    kb.button(text="Чат с Admissions", url=ADMISSIONS_CHAT)
    kb.adjust(2,1)
    return kb.as_markup()

@dp.message(CommandStart())
async def start(message: Message):
    # Optional chat allow-list
    if ALLOWED_CHATS and str(message.chat.id) not in ALLOWED_CHATS:
        return await message.answer("Доступ ограничён. Обратитесь к администратору.")

    text = (
        "Привет! Я AI‑консультант <b>TEAM University</b>.\n"
        "Отвечаю только по вопросам о TEAM University: программы, поступление, стоимость, кампус и т.д.\n\n"
        "Выберите действие ниже или задайте вопрос."
    )
    await message.answer(text, reply_markup=main_menu_kb())

@dp.callback_query(F.data == "contacts")
async def contacts(cb: CallbackQuery):
    await cb.message.answer(
        f"📞 Приёмная (Admissions): <b>{PHONE}</b>\n"
        f"✉️ Чат: {ADMISSIONS_CHAT}\n"
        f"🌐 Сайт: {TEAM_LINK}",
        reply_markup=main_menu_kb()
    )
    await cb.answer()

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "Я консультирую <b>только</b> по TEAM University.\n"
        "Спросите про программы, поступление, дедлайны, стоимость, кампус, 3D тур.\n",
        reply_markup=main_menu_kb()
    )

async def generate_answer(user_text: str) -> str:
    # Compose messages for the model
    messages = [
        {{ "role": "system", "content": SYSTEM_PROMPT }},
        {{ "role": "system", "content": "База знаний:\n" + KNOWLEDGE }},
        {{ "role": "user", "content": user_text.strip() }}
    ]
    try:
        resp = oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=600
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return (f"Извините, сейчас не получается ответить. "
                f"Пожалуйста, напишите в чат Admissions: {ADMISSIONS_CHAT} или позвоните {PHONE}.")

@dp.message()
async def handle_message(message: Message):
    if ALLOWED_CHATS and str(message.chat.id) not in ALLOWED_CHATS:
        return
    text = (message.text or "").strip()
    if not text:
        return await message.answer("Пожалуйста, напишите текст вопроса про TEAM University.", reply_markup=main_menu_kb())

    # Off-topic guardrail before calling the model
    if not is_team_related(text):
        return await message.answer(
            "Я отвечаю только по вопросам о <b>TEAM University</b>.\n"
            "Уточните, как ваш вопрос связан с университетом, или воспользуйтесь кнопками ниже.",
            reply_markup=main_menu_kb()
        )

    answer = await generate_answer(text)
    await message.answer(answer, reply_markup=main_menu_kb())

if __name__ == "__main__":
    import asyncio
    async def _main():
        print("Bot is starting...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    asyncio.run(_main())
