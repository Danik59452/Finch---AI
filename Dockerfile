# Берём официальный лёгкий образ Python
FROM python:3.9-slim

# Устанавливаем рабочую папку внутри сервера
WORKDIR /app

# Копируем список библиотек и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем сам код бота в сервер
COPY . .

# Открываем порт для веб-сервера
EXPOSE 7860

# Главная команда для запуска бота
CMD ["python", "Finch.py"]
