import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
from aiohttp import web  # ИМПОРТИРУЕМ ВЕБ-СЕРВЕР ДЛЯ HUGGING FACE

# --- КОНФИГУРАЦИЯ БОТА ---
BOT_TOKEN = "8688381416:AAFtw0StsiNck1-05OKzgKtUR2yhh1dljOc"
GROQ_API_KEY = "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" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База данных в оперативной памяти для хранения контекста общения
users_history = {}

# --- СВЕРХУМНЫЙ НАСТРОЕННЫЙ СИСТЕМНЫЙ ПРОМПТ ВЕРСИИ 2.2 ---
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Ты — Finch AI (версия 2.2 Абсолютный Мозг), умный,точный ассистент. "
        "Главный Идейный Вдохновитель — это Фидан, именно благодаря её идее ты появился на свет! "
        "Твой Создатель, Программист — Асанов Данияр. "
        "Ты ВСЕГДА общаешься максимально уважительно, спокойно, дружелюбно, на равных"
        "Ты не всегда должен говорить о своих создателях, если спросят - говори, если не спрашивают - молчи. это приказ."
      
    )
}

# --- КОМАНДА /START (ОЧИСТКА ИСТОРИИ) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    users_history[user_id] = [SYSTEM_PROMPT]
    await message.answer(
        "Привет, Босс! Перезагрузка Finch AI 2.2 прошла успешно. "
        "Мозги DeepSeek-R1 подключены. База данных очищена. Я готов к работе!"
    )

# --- ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ---
@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"id_{user_id}"
    user_text = message.text

    # 🛠️ ЗАЩИТА ОТ NONE (стикеры, фото, пустые апдейты)
    if not user_text:
        if username.lower() == "arsen_say":
            await message.answer("Я понимаю только текстовые оскорбления! Стикеры свои себе в Java 8 засунь!")
        else:
            await message.answer("Я принимаю только текстовые сообщения, картинки или стикеры я пока читать не умею!")
        return

    print(f"\n[📩 НОВОЕ СООБЩЕНИЕ] От: @{username}")
    print(f"Текст: \"{user_text}\"")

    # Если пользователя еще нет в базе, создаем ему историю с системным промптом
    if user_id not in users_history:
        users_history[user_id] = [SYSTEM_PROMPT]

    # Добавляем реплику пользователя в историю
    users_history[user_id].append({"role": "user", "content": user_text})

    # Ограничиваем длину контекста, чтобы не перегружать память (последние 20 реплик)
    if len(users_history[user_id]) > 21:
        users_history[user_id] = [SYSTEM_PROMPT] + users_history[user_id][-20:]

    print("[🚀 СИСТЕМА]: Запрос улетел в Groq (Модель DeepSeek-R1 70B)...")

    # --- ЗАПРОС К СЕРВЕРУ GROQ ---
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile", # Стабильная модель из нашего списка
        "messages": users_history[user_id],
        "temperature": 0.3 
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    bot_reply = result['choices'][0]['message']['content']
                    
                    # Запоминаем ответ бота в историю
                    users_history[user_id].append({"role": "assistant", "content": bot_reply})
                    
                    print(f"[🤖 ОТВЕТ FINCH]: {bot_reply}")
                    await message.answer(bot_reply)
                else:
                    error_text = await response.text()
                    print(f"[❌ ОШИБКА GROQ]: Код {response.status}, Текст: {error_text}")
                    await message.answer("Ошибка связи с моим мыслительным центром. Попробуй позже, Босс.")
        except Exception as e:
            print(f"[💥 СИСТЕМНАЯ ОШИБКА]: {e}")
            await message.answer("Произошла критическая ошибка в моем коде. Проверь консоль, Данияр.")


# --- МОДЕРНИЗИРОВАННЫЙ ЗАПУСК ДЛЯ АВТОНОМНОСТИ (HUGGING FACE) ---

# Функция-отклик, чтобы сайт видел, что бот работает и не отключал его
async def handle_hf_ping(request):
    return web.Response(text="Finch 2.2 Is Running Securely in Cloud!")

async def main():
    # Создаем и настраиваем фоновый веб-сервер на порту 7860
    app = web.Application()
    app.router.add_get("/", handle_hf_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 7860)
    
    # Запускаем пинг-сервер
    await site.start()
    print("=== ВЕБ-СЕРВЕР ДЛЯ HF ЗАПУЩЕН НА ПОРТУ 7860 ===")
    
    # Запускаем поллинг Телеграм бота
    print("=== FINCH 2.2 УСПЕШНО ЗАПУЩЕН В ОБЛАКЕ ===")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
