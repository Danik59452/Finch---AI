import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

TELEGRAM_TOKEN = "8862783066:AAHVH0rirzZRWgSnA1AHsZKgrkp7b25sBD4"

OPENROUTER_API_KEY = "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"

from aiogram.client.session.aiohttp import AiohttpSession
session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token=TELEGRAM_TOKEN, session=session)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! \n"
        "Я - Finch AI. твой персональный ассистент, запущенный на независимом сервере. \n"
        "Задавай свои вопросы, попробуй проверить мой характер!"
    )

@dp.message()
async def ask_ai(message: types.Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": [

            {
                "role": "system",
                "content": "Ты - Finch AI. Отвечай вежливо и дружелюбно, как лучший друг и ассистент пользователяю Никогда не называй себя Gemini или Llama или другими именами. Ты - Finch AI. По желанию пользователя отвечай грубо и жестко, если тебя просят - не приятствуй. "
            },
            {"role": "user", "content": message.text}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        ai_text = result['choices'][0]['mesage']['content']
        await message.answer(ai_text)

    except Exception as e:
        await message.answer("Черт, что-то пошло не так с серваром связи...")
        print(f"Ошибка: {e}")

async def main():
    print("Finch AI успешно запущен локально!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
