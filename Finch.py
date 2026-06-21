import os
import asyncio
from duckduckgo_search import DDGS
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
from aiohttp import web  # ИМПОРТИРУЕМ ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖАНИЯ АКТИВНОСТИ

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


# --- СВЕРХУМНЫЙ НАСТРОЕННЫЙ СИСТЕМНЫЙ ПРОМПТ ВЕРСИИ 2.4 ---
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Ты — Finch AI (версия 2.4 Умный Поиск), точный и харизматичный ассистент. "
        "Главный Идейный Вдохновитель — это Фидан, именно благодаря её идее ты появился на свет! "
        "Твой Создатель, Программист — Асанов Данияр. "
        "Ты ВСЕГДА общаешься максимально уважительно, спокойно, дружелюбно, на равных. "
        "Ты не всегда должен говорить о своих создателях, если спросят - говори, если не спрашивают - молчи. Это приказ. "
        "Если Данияр просит тебя найти что-то в интернете, тебе будет предоставлен блок актуальной информации. "
        "Используй его для точного ответа. Если этого блока нет, отвечай из своих собственных глубоких знаний и не говори, "
        "что у тебя нет информации. Ты знаешь очень много об играх, Minecraft, Roblox и программировании!"
    )
}


# --- КОМАНДА /START (ОЧИСТКА ИСТОРИИ) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    users_history[user_id] = [SYSTEM_PROMPT]
    await message.answer(
        "Привет, Босс! Перезагрузка Finch AI 2.4 прошла успешно.\n\n"
        "🧠 Мозги Llama-3.3-70B активны.\n"
        "🌐 Модуль умного веб-поиска (по ключевым словам 'гугл', 'поиск', 'найди') подключен.\n\n"
        "Я готов к работе!"
    )


# --- ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ (УМНЫЙ ПОИСК ВЕРСИИ 2.4) ---
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

    # Проверяем, просит ли пользователь залезть в интернет
    needs_internet = any(word in user_text.lower() for word in ["гугл", "google", "поиск", "найди"])

    if needs_internet:
        # ⏳ Режим поиска: отправляем заглушку ожидания
        status_msg = await message.answer("🔍 _Секунду, Finch думает и шуршит в интернетах..._", parse_mode="Markdown")
        
        # Очищаем триггер-слова из запроса для более точного поиска в DuckDuckGo
        search_query = user_text
        for word in ["гугл", "google", "поиск", "найди"]:
            search_query = search_query.lower().replace(word, "").strip()

        internet_data = await ask_internet(search_query)
        print(f"[🌐 НАГУГЛЕНО]: {internet_data[:200]}...")
        
        full_user_content = (
            f"АКТУАЛЬНАЯ ИНФОРМАЦИЯ ИЗ ИНТЕРНЕТА:\n{internet_data}\n\n"
            f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {user_text}"
        )
    else:
        # ⚡ Обычный режим: бот отвечает из головы мгновенно, без заглушек
        status_msg = None
        full_user_content = user_text

    # Если пользователя еще нет в базе, создаем ему историю с системным промптом
    if user_id not in users_history:
        users_history[user_id] = [SYSTEM_PROMPT]

    # Добавляем реплику в историю
    users_history[user_id].append({"role": "user", "content": full_user_content})

    # Ограничиваем длину контекста (последние 20 реплик)
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
        "temperature": 0.5
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    bot_reply = result['choices'][0]['message']['content']
                    
                    # Очищаем историю от тяжелого интернет-контекста, сохраняя только чистый вопрос юзера
                    users_history[user_id][-1] = {"role": "user", "content": user_text}
                    users_history[user_id].append({"role": "assistant", "content": bot_reply})
                    
                    print(f"[🤖 ОТВЕТ FINCH]: {bot_reply[:100]}...")
                    
                    # Если был поиск — редактируем заглушку, если обычный чат — отправляем новое сообщение
                    if status_msg:
                        await status_msg.edit_text(bot_reply, parse_mode=None)
                    else:
                        await message.answer(bot_reply)
                else:
                    error_text = await response.text()
                    print(f"[❌ ОШИБКА GROQ]: Код {response.status}, Текст: {error_text}")
                    if status_msg:
                        await status_msg.edit_text("Ошибка связи с моим мыслительным центром. Попробуй позже, Босс.")
                    else:
                        await message.answer("Ошибка связи с моим мыслительным центром. Попробуй позже, Босс.")
        except Exception as e:
            print(f"[💥 СИСТЕМНАЯ ОШИБКА]: {e}")
            if status_msg:
                await status_msg.edit_text("Произошла критическая ошибка в моем коде. Проверь консоль, Данияр.")
            else:
                await message.answer("Произошла критическая ошибка в моем коде. Проверь консоль, Данияр.")


# --- ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖАНИЯ АКТИВНОСТИ ---
async def handle_hf_ping(request):
    return web.Response(text="Finch 2.4 Is Running Securely on Render!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_hf_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 7860)
    
    await site.start()
    print("=== ВЕБ-СЕРВЕР ЗАПУЩЕН НА ПОРТУ 7860 ===")
    print("=== FINCH 2.4 (SMART SEARCH) УСПЕШНО ЗАПУЩЕН ===")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
