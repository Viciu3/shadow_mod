# Данный модуль был сделан для гильдии Meteor
# Несанкционированное использование модуля карается -rep.
# Категорически запрещено распостранять модуль.
# Продажа модуля запрещена.
# Этот модуль был создан специально для управления гильдиями!
# За роспостранение модуля _rip(×_×) ak tg будет 
# Developer: @Yaukais, @Shadow_red1, @dream23041

__version__ = (7, 7, 7)  # meta developer: @Yaukais, @Shadow_red1, @dream23041

import asyncio
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils
from telethon import functions, types
from ..inline.types import InlineCall

class GIBFGBMod(loader.Module):
    strings = {"name": "GIBFGB"}

    # Определение конфигурации модуля
    config = loader.ModuleConfig(
        loader.ConfigValue(
            "chat_id",
            -4536633154,  # Значение по умолчанию
            "ID чата гильдии !!!",
            validator=loader.validators.Integer(),
        )
    )
    
    _bot = "@bfgbunker_bot"    
    confirmation_chat_id = None  # ID чата для подтверждений
        
    async def client_ready(self):
        # Создаем чат для подтверждений
        self.confirmation_chat, _ = await utils.asset_channel(
            self._client,
            "Bfgbunker - подтверждения",
            "Этот чат предназначен для подтверждений покупок от модуля Bfgb.",
            silent=True,
            archive=False,
            _folder="hikka",
        )
        # Сохраняем ID созданного чата
        self.confirmation_chat_id = self.confirmation_chat.id

    async def atakcmd(self, message: Message):
        """Купить атаку."""
        args = utils.get_args(message)
        amount = args[0] if args else "1"  # Если аргументов нет, используем 1 по умолчанию.

        # Формируем сообщение
        order_message = f"Купить атаку {amount}"

        # Отправляем сообщение в указанный чат
        await self.client.send_message(self.config["chat_id"], order_message)

        # Формируем и отправляем подтверждающее сообщение в другой чат
        confirmation_message = f"Вы купили атаку на количество: {amount}"
        await self.client.send_message(self.confirmation_chat_id, confirmation_message)
        
    async def defcmd(self, message: Message):
        """Купить защиту."""
        args = utils.get_args(message)
        amount = args[0] if args else "1"  # Если аргументов нет, используем 1 по умолчанию.

        # Формируем сообщение
        order_message = f"Купить защиту {amount}"

        # Отправляем сообщение в указанный чат
        await self.client.send_message(self.config["chat_id"], order_message)

        # Формируем и отправляем подтверждающее сообщение в другой чат
        confirmation_message = f"Вы купили защиту на количество: {amount}"
        await self.client.send_message(self.confirmation_chat_id, confirmation_message)

    async def btcmd(self, message: Message):
        """Информация твого бункера"""

        async with self._client.conversation(self._bot) as conv:
            await conv.send_message("Бункер")
            response = await conv.get_response()

            info_text = response.raw_text
            nick_start = info_text.find("🙎‍♂️")
            nick_end = info_text.find("\n", nick_start)  
            nick = info_text[nick_start+4:nick_end].strip()  
            bottles_text = info_text.split("Бутылок:")[1].split()[0].strip()
            bottles = int("".join(filter(str.isdigit, bottles_text)))
            bottles = "{:,}".format(int(bottles)).replace(",", ".")
            money_parts = info_text.split("Баланс:")[1].split()[0].strip().split('/')
            formatted_money = f"{money_parts[0]}/{money_parts[1]}"
            people = int("".join(filter(str.isdigit, info_text.split("Людей в бункере:")[1].split('\n')[0].strip())))
            people_in_line = int("".join(filter(str.isdigit, info_text.split("Людей в очереди в бункер:")[1].split('/')[0].strip())))
            max_people = int("".join(filter(str.isdigit, info_text.split("Макс. вместимость людей:")[1].split()[0].strip())))
            profit_start = info_text.find("💵")
            profit_end = info_text.find("\n", profit_start)  
            profit = info_text[profit_start+1:profit_end].strip()  

            formatted_info = f'''🙎‍♂️ {nick}\n\n🍾 <b>Бутылок:</b> {bottles}\n💰 <b>Крышек:</b> {formatted_money} кр.\n\n🧍 <b>Людей в бункере:</b> {people}\n     ↳<b>Людей в очереди:</b> {people_in_line}\n\n<code>Макс. человек: </code>{max_people}\n\n💵 <b>{profit}</b> '''

            await message.edit(formatted_info) 
            
    async def g5cmd(self, message: Message):
        """отправляет информацию о 5%"""

        reply = await message.get_reply_message()
        if not reply:
            await message.edit("<b>Ответь на сообщение с информацией о бутылках!</b>")
            return

        args = message.text.split()
        if len(args) > 1:
            try:
                multiplier = float(args[1])
            except ValueError:
                await message.edit("<b>Второй аргумент должен быть числом!</b>")
                return
        else:
            multiplier = 1.2

        self.result_list = []
        self.monday_bottles_list = []  
        self.five_percent_bonus_list = [] 
        self.total_bottles = 0
        self.total_five_percent_bonus = 0  
        self.total_monday_bottles = 0
        for line in reply.text.splitlines():
            if " - " in line:
                parts = line.split(" - ")
                nick = parts[0].strip()
                
                bottles_str = parts[1].strip()[:-1]  
                bottles_str = bottles_str.replace('.', '')  
                bottles = int(bottles_str)  
                bottles = bottles // 10
                self.total_bottles += bottles 
                bottles_str = self.format_number(bottles)
                self.result_list.append(f"{nick} - {bottles_str} 🍾")

                monday_bottles = int(bottles * multiplier)
                self.total_monday_bottles += monday_bottles
                monday_bottles_str = self.format_number(monday_bottles)
                self.monday_bottles_list.append(f"{nick} - {monday_bottles_str} 🍾")

                five_percent_bonus = int(monday_bottles / 20)
                five_percent_bonus_str = self.format_number(five_percent_bonus)
                self.five_percent_bonus_list.append(f"{nick} - {five_percent_bonus_str} 🍾")
                self.total_five_percent_bonus += five_percent_bonus
                
        self.total_bottles_str = self.format_number(self.total_bottles) 
        self.total_five_percent_bonus_str = self.format_number(self.total_five_percent_bonus)  
        self.total_monday_bottles_str = self.format_number(self.total_monday_bottles)
        
        result_message = f"<blockquote>📊 Статистика гильдии за текущую неделю:</blockquote>\n\n"
        result_message += "\n".join(self.result_list)
        result_message += f"\n\n<blockquote><b>🗒Всего бутылок:</b> {self.total_bottles_str} 🍾</blockquote>"  

        await self.inline.form(
            text=result_message,
            message=message,
            reply_markup=[
                [
                    {
                        "text": "Проценты",
                        "callback": self.five_percent
                    },
                    {
                        "text": "Понедельник",            
                        "callback": self.monday
                    }
                ]
            ]
        )

    async def five_percent(self, call: InlineCall):
        result_message = f"<blockquote>5% в понедельник:\n\n"
        result_message += "\n".join(self.five_percent_bonus_list)
        result_message += f"\n\n<b>🗒Всего бутылок в 5% —</b> {self.total_five_percent_bonus_str} 🍾</blockquote>" 
        await call.edit(result_message, reply_markup=[
            [
                {
                    "text": "Назад",
                    "callback": self.back  
                }
            ]
        ])

    async def monday(self, call: InlineCall):
        result_message = f"<blockquote>Понедельник:\n\n"
        result_message += "\n".join(self.monday_bottles_list)
        result_message += f"\n\n<b>🗒Всего бутылок в понедельник —</b> {self.total_monday_bottles_str} 🍾</blockquote>" 
        await call.edit(result_message, reply_markup=[
            [
                {
                    "text": "Назад",
                    "callback": self.back  
                }
            ]
        ])

    async def back(self, call: InlineCall):
        result_message = f"<blockquote>📊 Статистика гильдии за текущую неделю:\n\n"
        result_message += "\n".join(self.result_list)
        result_message += f"\n\n<b>🗒Всего бутылок:</b> {self.total_bottles_str} 🍾</blockquote>" 
        await call.edit(result_message, reply_markup=[
            [
                {
                    "text": "Проценты",
                    "callback": self.five_percent
                },
                {
                    "text": "Понедельник",            
                    "callback": self.monday
                }
            ]
        ])

    def format_number(self, number):
        number_str = str(number)
        result = []
        for i in range(len(number_str) - 1, -1, -3):
            result.append(number_str[max(0, i - 2):i + 1])
        return ".".join(reversed(result))

class GuildAttacker(loader.Module):
    def __init__(self):
        self._sending = False
        self._task = None
        self.chat_id = None  # Ensure chat_id is initialized

    async def gncmd(self, message: Message):
        """Initiate or stop an attack on the guild"""
        if not self._sending:
            self._sending = True
            self._task = asyncio.create_task(self._send_attack_message())
            await message.respond("Начинаю нападение на гильдию!")
        else:
            self._sending = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task  # Wait for the task to finish
                except asyncio.CancelledError:
                    pass
                self._task = None
            await message.respond("Остановлено нападение на гильдию!")

    async def _send_attack_message(self):
        while self._sending:
            await utils.get_bot().send_message(self.chat_id, "Напасть на гильдию")
            await asyncio.sleep(2)  # Interval between messages