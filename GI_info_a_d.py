#Данный модуль был сделан для гильдии Meteor
#Несанкционированное использование модуля карается -rep.
#Категорически запрещено распостронять модуль.
#Продажа модуля запрещена.
#этот модуль был создан спецыально для управления гильлиями!
#за розпространение модуля _rip(×_×) ak tg будет 
#Developer: @Yaukais, @Shadow_red1

__version__ = (7, 7, 7)  # meta developer: @Yaukais, @Shadow_red1,

import asyncio
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils

class GI_info_a_dMod(loader.Module):
    strings = {"name": "GI_info_a_d"}

    async def info_ataka_defcmd(self, message: Message):
        """Просмотр сколько атаки или защиты получится из количества банок."""
        
        reply = await message.get_reply_message()
        if not reply:
            await message.edit("<b>Ответь на сообщение с информацией о банках!</b>")
            return

        # Пробуем получить количество банок из сообщения
        content = reply.message
        try:
            # Ищем строку с количеством банок
            lines = content.split('\n')
            for line in lines:
                if "Количество банок:" in line:
                    # Извлекаем число из строки
                    bank_count = int(line.split(":")[1].strip())
                    break
            else:
                await message.edit("<b>Не удалось найти количество банок в сообщении!</b>")
                return
            
            # Делим количество банок на 100, чтобы получить количество атаки/защиты
            bottle_count = bank_count // 100
            
            # Пробуем получить название гильдии из сообщения
            gi_name = None
            for line in lines:
                if "Название гильдии:" in line:
                    # Извлекаем название из строки
                    gi_name = line.split(":")[1].strip()
                    break
            if not gi_name:
                await message.edit("<b>Не удалось найти название гильдии в сообщении!</b>")
                return
                
            # Пробуем получить номер гильдии из сообщения
            gi_nomer = None
            for line in lines:
                if "Гильдия №" in line:
                    # Извлекаем номер из строки
                    gi_nomer = line.split("№")[1].strip()  # Изменено для правильного извлечения номера
                    break
            if not gi_nomer:
                await message.edit("<b>Не удалось найти номер гильдии в сообщении!</b>")
                return    

            # Формируем ответ
            response = f" Список покупки из:\n💠Гильдии: {gi_name}\n📊Номер гильдии: №<code>{gi_nomer}</code>\n\n🫙Количество банок: <code>{bank_count}</code>\n🚀Покупка атаки/защиты: <code>{bottle_count}</code>\n\n🎮Игровой бот: <button>@bfgbunker_bot</button>"
            await message.edit(response)

        except Exception as e:
            await message.edit(f"<b>Произошла ошибка: {str(e)}</b>")

# Не забудьте зарегистрировать модуль в вашей системе, чтобы его можно было использовать.