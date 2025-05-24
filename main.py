import os
import threading
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError
from background import start_server

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("rm-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

last_message_id = {}
config_texts = set()

# Загружаем config.txt
def load_config():
    global config_texts
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            config_texts = set(line.strip().lower() for line in f if line.strip())
            print(f"Загружено {len(config_texts)} триггеров из config.txt")
    except FileNotFoundError:
        print("Файл config.txt не найден. Бот продолжит без фильтра.")

load_config()

@app.on_message(filters.group)
async def handle_message(client, message):
    chat_id = message.chat.id
    current_id = message.id
    previous_id = last_message_id.get(chat_id)

    if previous_id is not None and current_id > previous_id + 1:
        # Собираем set ID-ов, которые не будем удалять
        ids_to_skip = set()

        # Попробуем получить текст предыдущего сообщения B
        try:
            msg_b = await client.get_messages(chat_id, previous_id)
            text_b = msg_b.text.lower().strip() if msg_b.text else ""
            if text_b in config_texts:
                # Если B — триггер, пропускаем сообщение B+1
                skip_id = previous_id + 1
                ids_to_skip.add(skip_id)
                print(f"Сообщение {previous_id} является триггером; пропускаем сообщение {skip_id}")
        except RPCError as e:
            print(f"Не удалось получить сообщение B (ID {previous_id}): {e}")

        # Удаляем все сообщения между B и A, кроме пропущенных
        for msg_id in range(previous_id + 1, current_id):
            if msg_id in ids_to_skip:
                continue
            try:
                await client.delete_messages(chat_id, msg_id)
                print(f"Удалено сообщение {msg_id} в чате {chat_id}")
            except FloodWait as e:
                print(f"FloodWait при удалении {msg_id}: ждём {e.value} сек")
                await asyncio.sleep(e.value)
            except RPCError as e:
                print(f"Ошибка при удалении {msg_id}: {e}")

    # Обновляем ID последнего сообщения для данного чата
    last_message_id[chat_id] = current_id

if __name__ == "__main__":
    # Запускаем фоновый Flask-сервер
    threading.Thread(target=start_server, daemon=True).start()
    print("Фоновый сервер Flask запущен...")
    print("Бот запущен...")
    app.run()
