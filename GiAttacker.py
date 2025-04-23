# Данный модуль был сделан для гильдии Meteor
# Несанкционированное использование модуля карается -rep.
# Категорически запрещено распостронять модуль.
# Продажа модуля запрещена.
# Этот модуль был создан специально для управления гильдиями!
# За роспостранение модуля _rip(×_×) ak tg будет 
# Developer: @Yaukais, @Shadow_red1

__version__ = (7, 7, 7)  # meta developer: @Yaukais, @Shadow_red1

import asyncio
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils

class GiAttackerMod(loader.Module):
    strings = {"name": "GiAttacker"}

    # Определение конфигурации модуля
    config = loader.ModuleConfig(
        loader.ConfigValue(
            "chat_id",
            None,  # Значение по умолчанию установлено в None
            "ID чата гильдии !!!",
            validator=loader.validators.Hidden(),
        ),
        loader.ConfigValue(
            "auto_attack",
            False,  # Значение по умолчанию установлено в False
            "Включить авто режим нападения на гильдию?",
            validator=loader.validators.Boolean(),
        )
    )

    def __init__(self):
        self._sending = False
        self._task = None

    async def gncmd(self, message: Message):
        """Запуск атаки на гильдию."""
        if self._sending:
            await message.edit("Атака уже запущена!")
            return

        self._sending = True
        await message.edit("Запуск атаки на гильдию...")

        try:
            while self._sending:
                chat_id = self.config["chat_id"]  # Получаем chat_id из конфигурации
                if chat_id is None:
                    await message.edit("chat_id не установлен. Установите его в конфигурации.")
                    self._sending = False
                    return
                await message.client.send_message(chat_id, "Напасть на гильдию")
                await asyncio.sleep(21600)  # Отправка сообщения каждые 6 часов (21600 секунд)
        except asyncio.CancelledError:
            pass
        finally:
            self._sending = False
            await message.edit("Атака прекращена!")

    async def stop_taskcmd(self, message: Message):
        """Остановить текущую атаку."""
        if self._sending:
            self._sending = False
            await message.edit("Атака успешно прекращена!")
        else:
            await message.edit("Атака не была запущена!")

    async def gn777cmd(self, message: Message):
        """Атаковать гильдию по коду!."""
        args = utils.get_args(message)
        amount = args[0] if args else "1"  # Если аргументов нет, используем 1 по умолчанию.

        order_message = f"Напасть на гильдию {amount}"

        chat_id = self.config["chat_id"]  # Получаем chat_id из конфигурации
        
        if chat_id is None:
            await message.edit("chat_id не установлен. Установите его в конфигурации.")
            return
        
        # Если авто режим включен, запускаем бесконечную атаку
        if self.config["auto_attack"]:
            await message.edit("Авто режим нападения включен. Запускаем бесконечную атаку...")
            self._sending = True
            try:
                while self._sending:
                    await message.client.send_message(chat_id, order_message)
                    await asyncio.sleep(21600)  # Отправка сообщения каждые 6 часов (21600 секунд)
            except asyncio.CancelledError:
                pass
            finally:
                self._sending = False
                await message.edit("Авто режим нападения прекращен!")
        else:
            # Отправляем сообщение в указанный чат
            await message.client.send_message(chat_id, order_message)

            # Подтверждаем отправку
            await message.reply(f"Ваше сообщение отправлено в чат для атаки гильдии под номером: {amount}")