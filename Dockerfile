FROM python:3.12-slim

WORKDIR /app

# Зависимости
RUN pip install --no-cache-dir pyTelegramBotAPI python-dotenv

# Копируем все файлы
COPY *.py ./
COPY *.json ./
COPY .env ./

# Создаём папку для данных
RUN mkdir -p /app/data

# Запускаем
CMD ["python", "main.py"]