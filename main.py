import asyncio
import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# 1. Авторизация Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8315686050:AAGtTqMzAtPZMkeznSLfnhoE5VSaQZUrhwA")
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! \n"
        "Я - Finch AI, твой персональный ассистент, запущенный на независимом сервере. \n"
        "Задавай свои вопросы, попробуй проверить мой характер!"
    )

@dp.message()
async def ask_ai(message: types.Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    url = "https://openrouter.ai/api/v1/chat/completions"

    # 2. Достаем секретный ключ из настроек Render прямо в момент запроса
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    # Если ты забыл добавить переменную в Render, бот сам скажет об этом в ТГ
    if not openrouter_key:
        await message.answer("Ошибка: Render не видит переменную OPENROUTER_API_KEY в настройках Environment!")
        return

    # Подставляем скрытый ключ сюда
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "qwen/qwen-2.5-7b-instruct:free",
        "messages": [
            {
                "role": "system",
                "content": "Ты - Finch AI. Отвечай вежливо и дружелюбно, как лучший друг и ассистент пользователя. Никогда не называй себя Gemini или Llama или другими именами. Ты - Finch AI. По желанию пользователя отвечай грубо и жестко, если тебя просят - не приветствуй."
            },
            {"role": "user", "content": message.text}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            reply_text = result["choices"][0]["message"]["content"]
            await message.answer(reply_text)
        else:
            # Если OpenRouter вернет 401, мы поймем, что сам ключ кривой
            await message.answer(f"Ошибка OpenRouter: {response.status_code}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("Черт, что-то пошло не так с серваром связи...")

async def main():
    print("Finch AI успешно запущен локально!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
