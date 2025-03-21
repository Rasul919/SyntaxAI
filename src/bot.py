import logging
import asyncio
import nest_asyncio
import json
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode


nest_asyncio.apply()


TELEGRAM_TOKEN = "7487815969:AAFOM9A9ObYv2pWaPReeMVqrLMkL7pvZA4w" 
OPENROUTER_API_KEY = "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"  
CHANNEL_USERNAME = "@SYNTAXA1" 


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, подписан ли пользователь на канал."""
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start: приветствие и проверка подписки."""
    user_id = update.message.from_user.id
    is_subscribed = await check_subscription(user_id, context)

    menu_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("/start"), KeyboardButton("/newchat")]],
        resize_keyboard=True
    )

    if is_subscribed:
        await update.message.reply_text(
            "👋 Привет! Этот бот поможет исправить ошибки в твоем тексте. "
            "Отправь мне свой текст, и я исправлю его. ✍️",
            reply_markup=menu_keyboard
        )
    else:
        text = (
            "Привет! Этот бот поможет исправить ошибки в твоем тексте. "
            "Отправь мне свой текст, и я исправлю его. ✍️\n\n"
            "Но сначала подпишись на наш канал, чтобы пользоваться ботом. 👇"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Подписаться", url="https://t.me/SYNTAXA1")],
            [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")]
        ])

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /newchat: начинает новый чат."""
    menu_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("/start"), KeyboardButton("/newchat")]],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Привет! Этот бот поможет исправить ошибки в твоем тексте. "
        "Отправь мне свой текст, а я исправлю его. ✍️",
        reply_markup=menu_keyboard
    )


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Проверить подписку'."""
    query = update.callback_query
    user_id = query.from_user.id
    is_subscribed = await check_subscription(user_id, context)

    if is_subscribed:
        await query.message.edit_text("Спасибо за подписку! Теперь вы можете пользоваться ботом. 😊")
    else:
        await query.answer("Вы не подписались на канал!", show_alert=True)


def get_ai_response(user_message: str) -> str:
    """Отправляет запрос к OpenRouter API и возвращает исправленный текст с пояснениями."""
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "deepseek/deepseek-r1",
                "messages": [
                    {"role": "system", "content": "Ты помощник, который исправляет ошибки в русском тексте. "
                                                  "Отвечай строго в формате: \n"
                                                  "Исправленный текст: <исправленный вариант> \n\n"
                                                  "Пояснения: \n1. <объяснение первой ошибки>\n2. <объяснение второй ошибки>"},
                    {"role": "user", "content": f"Исправь этот текст: {user_message}"}
                ]
            })
        )

        response_json = response.json()

        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"].strip()
        else:
            return "⚠ Ошибка: API не вернул корректный ответ."

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при вызове API: {e}")
        return "⚠ Ошибка сети при обработке запроса."

    except Exception as e:
        logger.error(f"Неизвестная ошибка API: {e}")
        return "⚠ Произошла ошибка. Попробуйте позже."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщения (только если подписан)."""
    user_id = update.message.from_user.id
    is_subscribed = await check_subscription(user_id, context)

    if not is_subscribed:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Подписаться", url="https://t.me/SYNTAXA1")],
            [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")]
        ])
        await update.message.reply_text(
            "Вы не подписаны на канал. Подпишитесь и нажмите 'Проверить подписку'.",
            reply_markup=keyboard,
        )
        return


    waiting_message = await update.message.reply_text("⏳ Ожидайте, выполняю ваш запрос...")

    user_message = update.message.text
    bot_response = get_ai_response(user_message)

    await context.bot.delete_message(chat_id=update.message.chat_id, message_id=waiting_message.message_id)
    await update.message.reply_text(bot_response)


async def main():
    """Запуск телеграм-бота."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newchat", new_chat))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="check_sub"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
