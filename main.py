import os
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError
import asyncio

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
    except FileNotFoundError:
        print("Файл config.txt не найден. Бот продолжит без фильтра.")

load_config()

@app.on_message(filters.group)
async def handle_message(client, message):
    chat_id = message.chat.id
    current_id = message.id
    previous_id = last_message_id.get(chat_id)

    if previous_id is not None:
        if current_id == previous_id + 1:
            pass
        elif current_id > previous_id + 1:
            try:
                trigger_msg = await client.get_messages(chat_id, previous_id)
                if trigger_msg.text and trigger_msg.text.lower() in config_texts:
                    skip_id = previous_id + 1
                    ids_to_delete = [i for i in range(previous_id + 1, current_id) if i != skip_id]
                else:
                    ids_to_delete = list(range(previous_id + 1, current_id))

                for msg_id in ids_to_delete:
                    try:
                        await client.delete_messages(chat_id, msg_id)
                        print(f"Удалено сообщение {msg_id} в чате {chat_id}")
                    except FloodWait as e:
                        print(f"FloodWait: ждём {e.value} сек")
                        await asyncio.sleep(e.value)
                    except RPCError as e:
                        print(f"Ошибка при удалении {msg_id}: {e}")

            except RPCError as e:
                print(f"Ошибка при получении предыдущего сообщения: {e}")

    last_message_id[chat_id] = current_id

print("Бот запущен...")
app.run()
