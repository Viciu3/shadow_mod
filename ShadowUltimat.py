import json
import os
import pathlib
import re
import asyncio
import logging
from hikkatl.types import Message
from .. import loader, utils

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@loader.tds
class ShadowUltimat(loader.Module):
    """ v777 by @shadow_mod777 для управления BFGB"""

    strings = {
        "name": "ShadowUltimat",
        "base_template": (
            "📓  | Shadow_Ultimat > <b><i><u>BFGB</u></i></b> < @bfgbunker_bot\n"
            "╔═╣════════════════╗\n"
            "║  🔻СТАТУС |💣| BFGB🔻\n"
            "╠══════════════════╣\n"
            "{greenhouse_status}"
            "╠══════════════════╣\n"
            "{garden_status}"
            "╠══════════════════╣\n"
            "║👁‍🗨 Команды: \n"
            "╠═╣<code>{prefix}теплица</code> - on/off\n"
            "╠═╣<code>{prefix}сад</code> - on/off\n"
            "╚═══════════════════"
        ),
        "base_template_premium": (
            "<emoji document_id=5337046505129799969>📔</emoji> | Shadow_Ultimat > <b><i><u>BFGB</u></i></b> < @bfgbunker_bot\n"
            "╔═╣════════════════╗\n"
            "║  <emoji document_id=5442623686098056812>🔻</emoji>СТАТУС |<emoji document_id=5226813248900187912>💣</emoji>| BFGB<emoji document_id=5442623686098056812>🔻</emoji>\n"
            "╠══════════════════╣\n"
            "{greenhouse_status}"
            "╠══════════════════╣\n"
            "{garden_status}"
            "╠══════════════════╣\n"
            "║<emoji document_id=5873224578775387997>👁‍🗨</emoji> Команды: \n"
            "╠═╣<code>{prefix}теплица</code> - on/off\n"
            "╠═╣<code>{prefix}сад</code> - on/off\n"
            "╚═══════════════════"
        ),
        "greenhouse_active": (
            "║~$ 🌱 Теплица: 🟢\n"
            "║~# ( картошка | {experience}.xp )\n"
        ),
        "greenhouse_inactive": (
            "║~$ 🌱 Теплица: 🔴\n"
        ),
        "garden_active": (
            "║~$ 🌳 Сад: 🟢\n"
            "║\n"
            "║~# ✨ Рост: Яблоки \n"
            "║~#      ( время: )\n"
            "║\n"
            "║~# 📦 Склад:\n"
            "║~#    🍏 Яблоко 0шт\n"
            "║~#    🍒 Черешня 0шт\n"
            "║~#    🍑 Персик 0шт\n"
            "║~#    🍊 Мандарин 0шт\n"
        ),
        "garden_inactive": (
            "║~$ 🌳 Сад: 🔴\n"
        ),
        "greenhouse_active_premium": (
            "║~$ <emoji document_id=5449885771420934013>🌱</emoji> Теплица: <emoji document_id=5474212414645882920>🟢</emoji>\n"
            "║~# ( картошка | {experience}.xp )\n"
        ),
        "greenhouse_inactive_premium": (
            "║~$ <emoji document_id=5449885771420934013>🌱</emoji> Теплица: <emoji document_id=5949785428843302949>❌</emoji>\n"
        ),
        "garden_active_premium": (
            "║~$ <emoji document_id=5449918202718985124>🌳</emoji> Сад: <emoji document_id=5267231042934154418>🟢</emoji>\n"
            "║\n"
            "║~# <emoji document_id=5472164874886846699>✨</emoji> Рост: Яблоки \n"
            "║~#      ( время: )\n"
            "║\n"
            "║~# <emoji document_id=5422536330213088080>📦</emoji> Склад:\n"
            "║~#    <emoji document_id=5393416000974626525>🍏</emoji> Яблоко 0шт\n"
            "║~#    <emoji document_id=5352672210332966665>🍒</emoji> Черешня 0шт\n"
            "║~#    <emoji document_id=5386831554116855357>🍑</emoji> Персик 0шт\n"
            "║~#    <emoji document_id=5161401880529601474>🥺</emoji> Мандарин 0шт\n"
        ),
        "garden_inactive_premium": (
            "║~$ <emoji document_id=5449918202718985124>🌳</emoji> Сад: <emoji document_id=5949785428843302949>❌</emoji>\n"
        ),
        "capacity_template": (
            "📓  | Shadow_Ultimat > <b><i><u>BFGB</u></i></b> < @bfgbunker_bot\n"
            "╔═╣════════════════╗\n"
            "║  🔻СТАТУС |💣| BFGB🔻\n"
            "╠══════════════════╣\n"
            "║~$ 👜 Вместимость \n"
            "╠══════════════════╣\n"
            "{rooms}"
            "╠══════════════════╣\n"
            "║~$ 👥 Людей сейчас: {current_people}\n"
            "║~$ 📊 Макс. мест: {max_capacity}\n"
            "║~$ 🚪 Открыто: {open_rooms}/18\n"
            "╠══════════════════╣\n"
            "║👁‍🗨 Команда:\n"
            "╠═╣<code>{prefix}вл</code> - Чел. в бункере \n"
            "╠═╣<code>{prefix}вл</code> <ид> - Чел. в игрока\n"
            "╚═══════════════════"
        ),
        "capacity_template_premium": (
            "<emoji document_id=5337046505129799969>📔</emoji> | Shadow_Ultimat > <b><i><u>BFGB</u></i></b> < @bfgbunker_bot\n"
            "╔═╣════════════════╗\n"
            "║  <emoji document_id=5442623686098056812>🔻</emoji>СТАТУС |<emoji document_id=5226813248900187912>💣</emoji>| BFGB<emoji document_id=5442623686098056812>🔻</emoji>\n"
            "╠══════════════════╣\n"
            "║~$ <emoji document_id=5380056101473492248>👜</emoji> Вместимость \n"
            "╠══════════════════╣\n"
            "{rooms}"
            "╠══════════════════╣\n"
            "║~$ <emoji document_id=5870772616305839506>👥</emoji> Людей сейчас: {current_people}\n"
            "║~$ <emoji document_id=5870930636742595124>📊</emoji> Макс. мест: {max_capacity}\n"
            "║~$ <emoji document_id=5877341274863832725>🚪</emoji> Открыто: {open_rooms}/18\n"
            "╠══════════════════╣\n"
            "║<emoji document_id=5873224578775387997>👁‍🗨</emoji> Команда:\n"
            "╠═╣<code>{prefix}вл</code> - Чел. в бункере \n"
            "╠═╣<code>{prefix}вл</code> <ид> - Чел. в игрока\n"
            "╚═══════════════════"
        ),
        "room_active": "║~$ 🔹 K{room_num} - {capacity} чел.\n",
        "room_inactive": "║~$ 🔻 K{room_num} - {capacity} чел.\n",
        "room_active_premium": "║~$ <emoji document_id=5339513551524481000>🔵</emoji> K{room_num} - {capacity} чел.\n",
        "room_inactive_premium": "║~$ <emoji document_id=5411225014148014586>🔴</emoji> K{room_num} - {capacity} чел.\n",
        "id_template": (
            "╔═╣════════════════╣\n"
            "║  🔻СТАТУС |💣| BFGB🔻\n"
            "╠══════════════════╣\n"
            "║ ID : <code>{user_id}</code>\n"
            "╚═╣════════════════╣"
        ),
        "id_template_premium": (
            "╔═╣════════════════╣\n"
            "║ <emoji document_id=5442623686098056812>🔻</emoji>СТАТУС |<emoji document_id=5226813248900187912>💣</emoji>| BFGB<emoji document_id=5442623686098056812>🔻</emoji>\n"
            "╠══════════════════╣\n"
            "║ ID : <code>{user_id}</code>\n"
            "╚═╣════════════════╣"
        ),
        "profile_template": (
            "📓  | Shadow_Ultimat > <b><i><u>BFGB</u></i></b> < @bfgbunker_bot\n"
            "╔═╣════════════════╗\n"
            "║  🔻СТАТУС |💣| BFGB🔻\n"
            "╠══════════════════╣\n"
            "║~$      🪪 Профиль 💻/👿\n"
            "{admin_status}"
            "{vip_status}"
            "╠══════════════════╣\n"
            "║~$ 👤 {username}\n"
            "║~$ 🏢 Бункер №{bunker_id}\n"
            "║\n"
            "║~$ 💰 Баланс: {balance}\n"
            "║~$ 🍾 Бутылок: {bottles}\n"
            "║~$ 🪙 BB-coins: {bb_coins}\n"
            "║~$ 🍪 GPoints: {gpoints}\n"
            "║\n"
            "║~$ 💵 {profit}\n"
            "╠══════════════════╣\n"
            "║👁‍🗨 Команда:\n"
            "╠═╣<code>{prefix}б</code> - Мой профиль\n"
            "╠═╣<code>{prefix}б</code> <ид> - Профиль игрока\n"
            "╚═══════════════════"
        ),
        "profile_template_premium": (
            "<emoji document_id=5337046505129799969>📔</emoji> | Shadow_Ultimat > <b><i><u>BFGB</u></i></b> < @bfgbunker_bot\n"
            "╔═╣════════════════╗\n"
            "║  <emoji document_id=5442623686098056812>🔻</emoji>СТАТУС |<emoji document_id=5226813248900187912>💣</emoji>| BFGB<emoji document_id=5442623686098056812>🔻</emoji>\n"
            "╠══════════════════╣\n"
            "║~$      <emoji document_id=5985817223749439505>✉️</emoji> Профиль <emoji document_id=5870748341150683538>💻</emoji>/<emoji document_id=5197225640104837259>👿</emoji>\n"
            "{admin_status}"
            "{vip_status}"
            "╠══════════════════╣\n"
            "║~$ <emoji document_id=5870994129244131212>👤</emoji> {username}\n"
            "║~$ <emoji document_id=5967822972931542886>🏠</emoji> Бункер №{bunker_id}\n"
            "║\n"
            "║~$ <emoji document_id=5967390100357648692>💵</emoji> Баланс: {balance}\n"
            "║~$ <emoji document_id=5967688845397855939>🥂</emoji> Бутылок: {bottles}\n"
            "║~$ <emoji document_id=5987880246865565644>💰</emoji> BB-coins: {bb_coins}\n"
            "║~$ <emoji document_id=5845945815549350824>🧹</emoji> GPoints: {gpoints}\n"
            "║\n"
            "║~$ <emoji document_id=5870478797593120516>💵</emoji> {profit}\n"
            "╠══════════════════╣\n"
            "║<emoji document_id=5873224578775387997>👁‍🗨</emoji> Команда:\n"
            "╠═╣<code>{prefix}б</code> - Мой профиль\n"
            "╠═╣<code>{prefix}б</code> <ид> - Профиль игрока\n"
            "╚═══════════════════"
        ),
        "admin_tech": "║~$ 💻 Тех. Администратор 💻\n",
        "admin_tech_premium": "║~$ <emoji document_id=5870748341150683538>💻</emoji> Тех. Администратор <emoji document_id=5870748341150683538>💻</emoji>\n",
        "admin_chat": "║~$ 😈 Администратор оф.чата 😈\n",
        "admin_chat_premium": "║~$ <emoji document_id=5197225640104837259>👿</emoji> Администратор оф.чата <emoji document_id=5197225640104837259>👿</emoji>\n",
        "vip1": "║~$ ✨✨✨VIP1✨✨✨\n",
        "vip1_premium": "║~$ <emoji document_id=5821051356173046126>⛈</emoji><emoji document_id=5821051356173046126>⛈</emoji><emoji document_id=5821051356173046126>⛈</emoji>VIP1<emoji document_id=5821051356173046126>⛈</emoji><emoji document_id=5821051356173046126>⛈</emoji><emoji document_id=5821051356173046126>⛈</emoji>\n",
        "vip2": "║~$ 🔥🔥🔥VIP2🔥🔥🔥\n",
        "vip2_premium": "║~$ <emoji document_id=5354839412175816000>🔥</emoji><emoji document_id=5354839412175816000>🔥</emoji><emoji document_id=5354839412175816000>🔥</emoji>VIP2<emoji document_id=5354839412175816000>🔥</emoji><emoji document_id=5354839412175816000>🔥</emoji><emoji document_id=5354839412175816000>🔥</emoji>\n",
        "vip3": "║~$ 💎💎💎VIP3💎💎💎\n",
        "vip3_premium": "║~$ <emoji document_id=5343636681473935403>💎</emoji><emoji document_id=5343636681473935403>💎</emoji><emoji document_id=5343636681473935403>💎</emoji>VIP3<emoji document_id=5343636681473935403>💎</emoji><emoji document_id=5343636681473935403>💎</emoji><emoji document_id=5343636681473935403>💎</emoji>\n",
        "vip4": "║~$ ⭐️⭐️⭐️VIP4⭐️⭐️⭐️\n",
        "vip4_premium": "║~$ <emoji document_id=5395851457884866228>🌟</emoji><emoji document_id=5395851457884866228>🌟</emoji><emoji document_id=5395851457884866228>🌟</emoji>VIP4<emoji document_id=5395851457884866228>🌟</emoji><emoji document_id=5395851457884866228>🌟</emoji><emoji document_id=5395851457884866228>🌟</emoji>\n",
        "prefix_set": "Префикс успешно изменен на: `{}`",
        "prefix_current": "Текущий префикс: `{}`",
        "greenhouse_toggled": "Теплица: {}",
        "garden_toggled": "Сад: {}",
        "capacity_error": "Не удалось получить данные о бункере. Попробуйте позже.",
        "id_error": "Ответьте на сообщение пользователя для получения его ID.",
        "timeout_error": (
            "👀 Извините но у вас нету подходящего вип статуса !\n"
            "Пожалуйста купите вип статус минимум 3 уровня."
        )
    }

    strings_ru = {
        "prefix_set": "Префикс успешно изменен на: `{}`",
        "prefix_current": "Текущий префикс: `{}`",
        "greenhouse_toggled": "Теплица: {}",
        "garden_toggled": "Сад: {}",
        "shs_doc": "Показывает статус BFGB",
        "prefix_doc": "Установите свой префикс!",
        "greenhouse_doc": "Запускает/останавливает автофарм для теплицы",
        "garden_doc": "Запускает/останавливает автофарм для сада",
        "vl_doc": "Показывает количество людей в бункере и вместимость комнат",
        "id_doc": "Показывает Telegram ID пользователя по реплею",
        "profile_doc": "Показывает профиль игрока"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "experience",
                0,
                "Текущий опыт для отображения в статусе",
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "prefix",
                ".",
                "Префикс для команд",
                validator=loader.validators.String(),
            )
        )
        # Путь к JSON-файлу в папке ~/.hikka
        self.data_file = os.path.join(pathlib.Path.home(), ".hikka", "shadow_ultimat_data.json")
        # Создаем директорию ~/.hikka, если она не существует
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        # Инициализация JSON-файла с начальными данными
        self._init_data()

    def _init_data(self):
        """Инициализация JSON-файла с начальными данными"""
        default_data = {
            "greenhouse_active": False,
            "garden_active": False
        }
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4)

    def _load_data(self):
        """Загрузка данных из JSON-файла"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._init_data()
            return self._load_data()

    def _save_data(self, data):
        """Сохранение данных в JSON-файл"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def _get_data(self, key, default):
        """Получение значения из JSON-файла"""
        data = self._load_data()
        return data.get(key, default)

    def _set_data(self, key, value):
        """Установка значения в JSON-файле"""
        data = self._load_data()
        data[key] = value
        self._save_data(data)

    @loader.command(ru_doc="Показывает статус BFGB")
    async def shs(self, message: Message):
        """Показывает статус BFGB"""
        is_premium = (await self._client.get_me()).premium
        greenhouse_active = self._get_data("greenhouse_active", False)
        garden_active = self._get_data("garden_active", False)
        prefix = self.config["prefix"]
        experience = self.config["experience"]

        template_key = "base_template_premium" if is_premium else "base_template"
        greenhouse_key = ("greenhouse_active_premium" if is_premium else "greenhouse_active") if greenhouse_active else ("greenhouse_inactive_premium" if is_premium else "greenhouse_inactive")
        garden_key = ("garden_active_premium" if is_premium else "garden_active") if garden_active else ("garden_inactive_premium" if is_premium else "garden_inactive")
        
        greenhouse_status = self.strings[greenhouse_key].format(experience=experience)
        garden_status = self.strings[garden_key].format(experience=experience)

        formatted_message = self.strings[template_key].format(
            greenhouse_status=greenhouse_status,
            garden_status=garden_status,
            prefix=prefix,
            experience=experience
        )

        await utils.answer(message, formatted_message)

    @loader.command(ru_doc="Установите свой префикс!")
    async def prefix(self, message: Message):
        """Устанавливает или показывает текущий префикс"""
        args = utils.get_args_raw(message)
        if args:
            self.config["prefix"] = args
            await utils.answer(message, self.strings["prefix_set"].format(args))
        else:
            await utils.answer(message, self.strings["prefix_current"].format(self.config["prefix"]))

    @loader.command(ru_doc="Запускает/останавливает автофарм для теплицы")
    async def теплица(self, message: Message):
        """Запускает/останавливает автофарм для теплицы"""
        current_state = self._get_data("greenhouse_active", False)
        new_state = not current_state
        self._set_data("greenhouse_active", new_state)
        state_text = "включена" if new_state else "выключена"
        await utils.answer(message, self.strings["greenhouse_toggled"].format(state_text))

    @loader.command(ru_doc="Запускает/останавливает автофарм для сада")
    async def сад(self, message: Message):
        """Запускает/останавливает автофарм для сада"""
        current_state = self._get_data("garden_active", False)
        new_state = not current_state
        self._set_data("garden_active", new_state)
        state_text = "включен" if new_state else "выключен"
        await utils.answer(message, self.strings["garden_toggled"].format(state_text))

    @loader.command(ru_doc="Показывает количество людей в бункере и вместимость комнат")
    async def вл(self, message: Message):
        """Показывает количество людей в бункере и вместимость комнат"""
        is_premium = (await self._client.get_me()).premium
        args = utils.get_args_raw(message)

        async with self._client.conversation("@bfgbunker_bot") as conv:
            if args:
                try:
                    user_id = int(args)
                    await conv.send_message(f"Узнать о {user_id}")
                except ValueError:
                    await utils.answer(message, self.strings["capacity_error"])
                    return
            else:
                await conv.send_message("Б")
            
            try:
                response = await asyncio.wait_for(conv.get_response(), timeout=5)
            except asyncio.TimeoutError:
                await utils.answer(message, self.strings["timeout_error"])
                return

        text = response.text
        current_people = re.search(r"🧍 Людей в бункере: <b>(\d+)</b>", text)
        max_capacity = re.search(r"Макс\. вместимость людей: (\d+)", text)
        rooms_section = re.search(r"🏠 Комнаты:([\s\S]*?)(?=(💵 Общая прибыль|💵 Бункер не работает!|\Z))", text)

        if not (current_people and max_capacity and rooms_section):
            logger.error(f"Failed to parse capacity data. Response: {text}")
            await utils.answer(message, self.strings["capacity_error"])
            return

        current_people = int(current_people.group(1))
        max_capacity = int(max_capacity.group(1))
        rooms_text = rooms_section.group(1).strip()

        base_capacities = [6, 6, 6, 6, 12, 20, 32, 52, 92, 144, 234, 380, 520, 750, 1030, 1430, 2020, 3520]
        rooms = []
        room_lines = rooms_text.split("\n")
        open_rooms = 0
        for line in room_lines:
            line = line.strip()
            if not line:
                continue
            match = re.match(r"\s*(\d+️⃣)\s*(❗️)?\s*([^\d]+)\s*(\d+)\s*ур\.|.*'(.+?)'\s*Цена:\s*(\d+)\s*крышек", line)
            if match:
                if match.group(4):  # Room with level
                    room_num = int(match.group(1).replace("️⃣", ""))
                    warning = bool(match.group(2))
                    level = int(match.group(4))
                    capacity = base_capacities[room_num - 1] + 2 * (level - 1)
                    rooms.append({"num": room_num, "warning": warning, "capacity": capacity})
                    open_rooms += 1
                elif match.group(5):  # Room available for purchase
                    room_num = int(match.group(1).replace("️⃣", ""))
                    capacity = base_capacities[room_num - 1]  # Base capacity for unbuilt room
                    rooms.append({"num": room_num, "warning": True, "capacity": capacity})
                    open_rooms += 1

        rooms_str = ""
        for room in rooms:
            room_num = room["num"]
            capacity = room["capacity"]
            warning = room["warning"]
            room_key = "room_inactive_premium" if is_premium and warning else "room_active_premium" if is_premium else "room_inactive" if warning else "room_active"
            rooms_str += self.strings[room_key].format(room_num=room_num, capacity=capacity)

        template_key = "capacity_template_premium" if is_premium else "capacity_template"
        formatted_message = self.strings[template_key].format(
            rooms=rooms_str,
            current_people=current_people,
            max_capacity=max_capacity,
            open_rooms=open_rooms,
            prefix=self.config["prefix"]
        )

        await utils.answer(message, formatted_message)

    @loader.command(ru_doc="Показывает Telegram ID пользователя по реплею")
    async def ид(self, message: Message):
        """Показывает Telegram ID пользователя по реплею"""
        is_premium = (await self._client.get_me()).premium
        reply = await message.get_reply_message()
        
        if not reply:
            await utils.answer(message, self.strings["id_error"])
            return

        user_id = reply.sender_id
        template_key = "id_template_premium" if is_premium else "id_template"
        formatted_message = self.strings[template_key].format(user_id=user_id)
        
        await utils.answer(message, formatted_message)

    @loader.command(ru_doc="Показывает профиль игрока")
    async def б(self, message: Message):
        """Показывает профиль игрока"""
        is_premium = (await self._client.get_me()).premium
        args = utils.get_args_raw(message)

        async with self._client.conversation("@bfgbunker_bot") as conv:
            if args:
                try:
                    user_id = int(args)
                    await conv.send_message(f"Узнать о {user_id}")
                except ValueError:
                    await utils.answer(message, self.strings["capacity_error"])
                    return
            else:
                await conv.send_message("Б")
            
            try:
                response = await asyncio.wait_for(conv.get_response(), timeout=5)
            except asyncio.TimeoutError:
                await utils.answer(message, self.strings["timeout_error"])
                return

        text = response.text
        logger.debug(f"Bot response: {text}")  # Log raw response for debugging

        # Extract profile data with more flexible regex
        username = re.search(r"🙎‍♂️ (.+?)(?=\n|$)", text)
        bunker_id = re.search(r"🏢 Бункер №(\d+)", text)
        balance = re.search(r"💰 Баланс: ([\d,]+/[\d,]+(?:kk)?\s*кр\.)", text)
        bottles = re.search(r"🍾 Бутылок: (\d+)", text) or re.search(r"🥂 Бутылок: (\d+)", text)
        bb_coins = re.search(r"🪙 BB-coins: (\d+)", text) or re.search(r"💰 BB-coins: (\d+)", text)
        gpoints = re.search(r"🍪 GPoints: (\d+)", text) or re.search(r"🧹 GPoints: (\d+)", text)
        profit = re.search(r"💵 (.+?)(?=\n📅|\n🧍|\Z)", text)

        # Check if critical fields are missing
        if not (username and bunker_id):
            logger.error(f"Failed to parse critical fields. Username: {username}, Bunker ID: {bunker_id}")
            await utils.answer(message, self.strings["capacity_error"])
            return

        # Assign default values for optional fields
        username = username.group(1)
        bunker_id = bunker_id.group(1)
        balance = balance.group(1) if balance else "0/0 кр."
        bottles = bottles.group(1) if bottles else "0"
        bb_coins = bb_coins.group(1) if bb_coins else "0"
        gpoints = gpoints.group(1) if gpoints else "0"
        profit = profit.group(1) if profit else "Нет данных о прибыли"

        # Extract admin and VIP statuses
        admin_status = ""
        if "💻 Тех. Администратор 💻" in text:
            admin_status = self.strings["admin_tech_premium" if is_premium else "admin_tech"]
        elif "😈 Администратор оф.чата 😈" in text:
            admin_status = self.strings["admin_chat_premium" if is_premium else "admin_chat"]

        vip_status = ""
        if "⭐️⭐️⭐️VIP4⭐️⭐️⭐️" in text:
            vip_status = self.strings["vip4_premium" if is_premium else "vip4"]
        elif "💎💎💎VIP3💎💎💎" in text:
            vip_status = self.strings["vip3_premium" if is_premium else "vip3"]
        elif re.search(r"🔥🔥🔥?VIP2🔥🔥🔥?", text):  # Handle both 🔥🔥VIP2🔥🔥 and 🔥🔥🔥VIP2🔥🔥🔥
            vip_status = self.strings["vip2_premium" if is_premium else "vip2"]
        elif "⚡️VIP1⚡️" in text:
            vip_status = self.strings["vip1_premium" if is_premium else "vip1"]

        template_key = "profile_template_premium" if is_premium else "profile_template"
        formatted_message = self.strings[template_key].format(
            admin_status=admin_status,
            vip_status=vip_status,
            username=username,
            bunker_id=bunker_id,
            balance=balance,
            bottles=bottles,
            bb_coins=bb_coins,
            gpoints=gpoints,
            profit=profit,
            prefix=self.config["prefix"]
        )

        await utils.answer(message, formatted_message)