from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import pytz
import os
import asyncio

# Введите данные своего созданного telegram API
api_id = ''
api_hash = ''
phone_number = '' #+71234567890

channel_username = 'bcs_express'  # без 't.me/'

client = TelegramClient('session_name', api_id, api_hash)

os.makedirs('messages', exist_ok=True)

async def main():
    # Подключаемся к клиенту
    await client.start(phone_number)
    
    # Проверяем, нужна ли двухфакторная аутентификация
    if not await client.is_user_authorized():
        try:
            await client.send_code_request(phone_number)
            code = input('Введите код, полученный в Telegram: ')
            await client.sign_in(phone_number, code)
        except SessionPasswordNeededError:
            password = input('Введите ваш пароль двухфакторной аутентификации: ')
            await client.sign_in(password=password)
    
    # Получаем entity канала
    channel = await client.get_entity(channel_username)
    
    # Задаем часовой пояс Москвы
    moscow_tz = pytz.timezone('Europe/Moscow')
    
    # Получаем последние 100 сообщений из канала
    async for message in client.iter_messages(channel, limit=100):
        if message.text:
            # Получаем дату и время сообщения в часовом поясе Москвы
            date_time = message.date.astimezone(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
            # Формируем имя файла как id сообщения
            filename = os.path.join('messages', f'{message.id}.txt')
            # Записываем в файл
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(f'{date_time}\n{message.text}\n')

with client:
    client.loop.run_until_complete(main())