#Данный модуль был сделан для гильдии Meteor
#Несанкционированное использование модуля карается -rep.
#Категорически запрещено распостронять модуль.
#Продажа модуля запрещена.
#этот модуль был создан спецыально для управления гильлиями!
#за розпространение модуля _rip(×_×) ak tg будет 
#Developer: @Yaukais, @Shadow_red1

__version__ = (7, 7, 7)  # meta developer: @Yaukais, @Shadow_red1

import asyncio
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils

class btautoMod(loader.Module):
    strings = {"name": "btauto"}

    def __init__(self):
        self.running = False

    async def bytcmd(self, message: Message):
        """Запуск пополнения бутилок в гильдию."""
        self.running = True
        await message.client.send_message('@bfgbunker_bot', 'Бункер')
        await message.reply("🌶btauto🍒 запущен! Команда для остановки: .aytbyt")

        while self.running:
            for _ in range(500):
                if not self.running:  # Проверка на остановку
                    break  # Если модуль остановлен, выйти из цикла
                
                # Отправка сообщения в чат бота @bfgbunker_bot
                await message.client.send_message('@bfgbunker_bot', 'Пополнить бутылки максимум')
                await asyncio.sleep(3)

            if self.running:
                await message.reply("🌶btauto🍒 Остановил обмен на 1 минуту связи с перегрузкой API.")
                await asyncio.sleep(60)  # Пауза на 1 минуту

    async def aytbytcmd(self, message: Message):
        """Остановка модуля."""
        self.running = False
        await message.reply("🌶btauto🍒 Пополнение успешно остановлено! ✅️")