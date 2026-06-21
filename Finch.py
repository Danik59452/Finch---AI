import os
import asyncio
from duckduckgo_search import DDGS
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
from aiohttp import web  # ИМПОРТИРУЕМ ВЕБ-СЕРВЕР ДЛЯ HUGGING FACE

# --- КОНФИГУРАЦИЯ БОТА ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База данных в оперативной памяти для хранения контекста общения
users_history = {}


# --- ФУНКЦИЯ ПОИСКА В ИНТЕРНЕТЕ ---
async def ask_internet(query: str) -> str:
    """Функция ищет инфу в утиной поисковухе и собирает краткий текст"""
    try:
        # Запускаем поиск в асинхронном потоке, чтобы бот не зависал
        loop = asyncio.get_event_loop()
        def do_search():
            with DDGS() as ddgs:
                # Берем топ-3 результата из выдачи
                results = [r for r in ddgs.text(query, max_results=3)]
                return results
        
        raw_results = await loop.run_in_executor(None, do_search)
        
        if not raw_results:
            return "В интернете ничего не найдено по этому запросу."
            
        # Склеиваем заголовки и краткое описание сайтов в один кусок текста
        context = ""
        for i, res in enumerate(raw_results, 1):
            context += f" Источник {i}: {res['title']} -> {res['body']}\n"
        return context
        
    except Exception as e:
        print(f"[⚠️ ОШИБКА ПОИСКА]: {e}")
        return "Не удалось подключиться к поисковой системе."


# --- СВЕРХУМНЫЙ НАСТРОЕННЫЙ СИСТЕМНЫЙ ПРОМПТ ВЕРСИИ 2.3 ---
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Ты — Finch AI (версия 2.3 Интернет-Ищейка), умный, точный ассистент. "
        "Главный Идейный Вдохновитель — это Фидан, именно благодаря её идее ты появился на свет! "
        "Твой Создатель, Программист — Асанов Данияр. "
        "Ты ВСЕГДА общаешься максимально уважительно, спокойно, дружелюбно, на равных. "
        "Ты не всегда должен говорить о своих создателях, если спросят - говори, если не спрашивают - молчи. Это приказ. "
        "Если пользователю предоставлена АКТУАЛЬНАЯ ИНФОРМАЦИЯ ИЗ ИНТЕРНЕТА, используй её для точного и правдивого ответа, "
        "особенно если речь идет о мифах Roblox, играх, коде или свежих событиях. Не выдумывай факты!"
    )
}


# --- КОМАНДА /START (ОЧИСТКА ИСТОРИИ) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    users_history[user_id] = [SYSTEM_PROMPT]
    await message.answer(
        "Привет, Босс! Перезагрузка Finch AI 2.3 прошла успешно. "
        "Мозги Модели Llama-3.3-70B и модуль веб-поиска подключены! Я готов к работе!"
    )


# --- ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ (ОБНОВЛЕННЫЙ) ---
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

    # ⏳ ЭФФЕКТ ОЖИДАНИЯ: Сразу отправляем статус, что Finch пошел работать
    status_msg = await message.answer("🔍 _Секунду, Finch думает и шуршит в интернетах..._", parse_mode="Markdown")

    # 🌐 ИЩЕМ ИНФОРМАЦИЮ В СЕТИ
    internet_data = await ask_internet(user_text)
    print(f"[🌐 НАГУГЛЕНО]: {internet_data[:200]}...")  # Выводим кусочек лога в консоль

    # Если пользователя еще нет в базе, создаем ему историю с системным промптом
    if user_id not in users_history:
        users_history[user_id] = [SYSTEM_PROMPT]

    # Формируем итоговый запрос для ИИ, склеивая результаты поиска и вопрос Данияра
    full_user_content = (
        f"АКТУАЛЬНАЯ ИНФОРМАЦИЯ ИЗ ИНТЕРНЕТА:\n{internet_data}\n\n"
        f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {user_text}"
    )

    # Добавляем реплику пользователя в историю (но саму историю не перегружаем поисковым спамом, храним чистый лог)
    users_history[user_id].append({"role": "user", "content": full_user_content})

    # Ограничиваем длину контекста, чтобы не перегружать память (последние 20 реплик)
    if len(users_history[user_id]) > 21:
        users_history[user_id] = [SYSTEM_PROMPT] + users_history[user_id][-20:]

    print("[🚀 СИСТЕМА]: Запрос улетел в Groq (Модель Llama 3.3 70B)...")

    # --- ЗАПРОС К СЕРВЕРУ GROQ ---
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": users_history[user_id],
        "temperature": 0.4  # Чуть-чуть подняли для более живых ответов
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    bot_reply = result['choices'][0]['message']['content']
                    
                    # Запоминаем ответ бота в историю (чистый ответ, без системных тегов)
                    users_history[user_id].append({"role": "assistant", "content": bot_reply})
                    
                    print(f"[🤖 ОТВЕТ FINCH]: {bot_reply[:100]}...")
                    
                    # ✨ ЭФФЕКТНЫЙ ФИНИШ: Редактируем сообщение "Секунду..." на настоящий ответ!
                    # Используем HTML, так как Markdown в aiogram может ломаться из-за спецсимволов ИИ
                    await status_msg.edit_text(bot_reply, parse_mode=None)
                else:
                    error_text = await response.text()
                    print(f"[❌ ОШИБКА GROQ]: Код {response.status}, Текст: {error_text}")
                    await status_msg.edit_text("Ошибка связи с моим мыслительным центром. Попробуй позже, Босс.")
        except Exception as e:
            print(f"[💥 СИСТЕМНАЯ ОШИБКА]: {e}")
            await status_msg.edit_text("Произошла критическая ошибка в моем коде. Проверь консоль, Данияр.")


# --- ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖАНИЯ АКТИВНОСТИ ---

async def handle_hf_ping(request):
    return web.Response(text="Finch 2.3 Is Running Securely in Cloud!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_hf_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 7860)
    
    await site.start()
    print("=== ВЕБ-СЕРВЕР ЗАПУЩЕН НА ПОРТУ 7860 ===")
    print("=== FINCH 2.3 (WEB SEARCH) УСПЕШНО ЗАПУЩЕН ===")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
