import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import os
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
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
       "Authorization": "Bearer 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",
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
        import requests
        # Делаем прямой запрос БЕЗ proxies=...
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            reply_text = result["choices"][0]["message"]["content"]
            await message.answer(reply_text)
        else:
            await message.answer(f"Ошибка OpenRouter: {response.status_code}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("Черт, что-то пошло не так с серваром связи...")
        print(f"Ошибка: {e}")

async def main():
    print("Finch AI успешно запущен локально!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
