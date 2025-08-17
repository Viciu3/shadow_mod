from herokutl.types import Message
from .. import loader, utils
import asyncio
import re
import typing
from telethon.tl.types import Message, ChatAdminRights
from telethon import functions
from datetime import datetime, timedelta

@loader.tds
class ShadowUltimat(loader.Module):
    """Shadow_Ultimat - Auto-farming module for @bfgbunker_bot by @familiarrrrrr"""
    strings = {"name": "ShadowUltimat", "status_on": "🟢", "status_off": "🔴"}
    strings_ru = {"status_on": "🟢", "status_off": "🔴"}

    def __init__(self):
        self._bot = "@bfgbunker_bot"
        self._Shadow_Ultimat_channel = None
        self._lock = asyncio.Lock()  # Lock for exclusive conversation
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "PeopleEnabled", True, "Enable auto-farming for people", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "BonusEnabled", True, "Enable daily bonus collection", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "FuelEnabled", True, "Enable auto-farming for fuel", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "GreenhouseEnabled", True, "Enable auto-farming for greenhouse", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "WastelandEnabled", True, "Enable auto-farming for wasteland", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "GardenEnabled", True, "Enable auto-farming for garden", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "MineEnabled", True, "Enable auto-farming for mine", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "GuildEnabled", True, "Enable auto-farming for guild", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "StimulatorsToBuy", 1, "Number of stimulators to buy", validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "WeaponsToBuy", 1, "Number of weapons to buy", validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "MineCooldown", 6, "Cooldown between mining attempts (minutes)", validator=loader.validators.Integer(minimum=1)
            ),
            loader.ConfigValue(
                "MineDiamond", True, "Mine diamonds automatically", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "SkipNonUranium", False, "Skip non-uranium resources", validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "MineProbability", True, "Mine based on probability (80-100%)", validator=loader.validators.Boolean()
            )
        )
        self._resources_map = {
            range(0, 500): "картошка",
            range(501, 2000): "морковь",
            range(2001, 10000): "рис",
            range(10001, 25000): "свекла",
            range(25001, 60000): "огурец",
            range(60001, 100000): "фасоль",
            range(100001, 10**50): "помидор",
        }

    async def client_ready(self):
        # Initialize database
        try:
            self._db = {
                "people": self.pointer("people", {"enabled": True, "count": 0, "queue": 0, "max": 0}),
                "bonus": self.pointer("bonus", {"enabled": True, "last_claim": None}),
                "fuel": self.pointer("fuel", {"enabled": True, "current": 0, "max": 0}),
                "greenhouse": self.pointer("greenhouse", {
                    "enabled": True, "xp": 0, "water": 0, "max_water": 0, "crop": "",
                    "stock": {"картошка": 0, "морковь": 0, "рис": 0, "свекла": 0, "огурец": 0, "фасоль": 0, "помидор": 0}
                }),
                "wasteland": self.pointer("wasteland", {
                    "enabled": True, "time": "0 час. 0 мин.", "health": 100, "stimulators": 0, "weapons": 0,
                    "caps": 0, "rating": 0, "death_date": None
                }),
                "garden": self.pointer("garden", {
                    "enabled": True, "level": 1, "status": "Пустует",
                    "stock": {"яблоко": 0, "черешня": 0, "персик": 0, "мандарин": 0}
                }),
                "mine": self.pointer("mine", {
                    "enabled": True, "pickaxe": "Нет кирки", "durability": 0, "depth": 0,
                    "stock": {"песок": 0, "уголь": 0, "железо": 0, "медь": 0, "серебро": 0, "алмаз": 0, "уран": 0}
                }),
                "guild": self.pointer("guild", {
                    "enabled": True, "auto_banks": False, "auto_bottles": False,
                    "auto_guild_attack": False, "auto_boss_attack": False, "auto_purchase": False
                })
            }
            await self.client.send_message("me", "Database initialized successfully")
        except Exception as e:
            await self.client.send_message("me", f"Failed to initialize database: {str(e)}")

        # Set up channel
        try:
            self._Shadow_Ultimat_channel, _ = await utils.asset_channel(
                self._client,
                "Shadow_Ultimat_bfgb - чат",
                "Этот чат предназначен для модуля Shadow_Ultimat от @familiarrrrrr",
                silent=True,
                archive=False,
                _folder="heroku",
            )
            await self.client(functions.channels.InviteToChannelRequest(self._Shadow_Ultimat_channel, [self._bot]))
            await self.client(functions.channels.EditAdminRequest(
                channel=self._Shadow_Ultimat_channel,
                user_id=self._bot,
                admin_rights=ChatAdminRights(ban_users=True, post_messages=True, edit_messages=True),
                rank="BFGBshadow",
            ))
            await self.client.send_message(self._Shadow_Ultimat_channel, "Shadow_Ultimat initialized")
        except Exception as e:
            await self.client.send_message("me", f"Failed to initialize channel: {str(e)}")

        # Start auto-farm loop manually
        try:
            asyncio.create_task(self.auto_farm_loop())
            await self.client.send_message(self._Shadow_Ultimat_channel, "Auto-farm loop started")
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Failed to start auto-farm loop: {str(e)}")

    async def auto_farm_loop(self):
        """Manual loop for auto-farming"""
        while True:
            await self._auto_farm()
            await asyncio.sleep(60)

    async def _update_status_message_text(self, section: str = None) -> str:
        """Helper to generate status message text without sending"""
        status = f"📓  | Shadow_Ultimat | ~ [ v777 ]\n"
        status += "╔═╣════════════════╗\n"
        status += "║  🔻СТАТУС |💣| BFGB🔻\n"
        status += "╠══════════════════╣\n"

        if section in [None, "people"]:
            status += f"║~$ 👫 Люди: {self.strings['status_on'] if self._db['people']['enabled'] else self.strings['status_off']}\n"
        if section in [None, "bonus"]:
            status += f"║~$ 🎁 Бонус: {self.strings['status_on'] if self._db['bonus']['enabled'] else self.strings['status_off']}\n"
        if section in [None, "fuel"]:
            status += f"║~$ 🛢 Бензин: {self.strings['status_on'] if self._db['fuel']['enabled'] else self.strings['status_off']}\n"
        if section in [None, "greenhouse"]:
            status += f"║~$ 🌱 Теплица: {self.strings['status_on'] if self._db['greenhouse']['enabled'] else self.strings['status_off']}\n"
            if section == "greenhouse":
                status += f"║~# ( {self._db['greenhouse']['crop'].capitalize()} | {self._db['greenhouse']['xp']} xp | {self._db['greenhouse']['water']} 💧 )\n"
                status += "╠══════════════════╣\n"
                status += "║~$ 📦 Склад:\n"
                for crop, amount in self._db['greenhouse']['stock'].items():
                    emoji = {"картошка": "🥔", "морковь": "🥕", "рис": "🍚", "свекла": "🍠", "огурец": "🥒", "фасоль": "🫘", "помидор": "🍅"}[crop]
                    status += f"║~#    {emoji} {crop.capitalize()} - {amount}/шт.\n"
        if section in [None, "wasteland"]:
            status += f"║~$ 🏜 Пустошь: {self.strings['status_on'] if self._db['wasteland']['enabled'] else self.strings['status_off']}\n"
            if section == "wasteland":
                if self._db['wasteland']['death_date']:
                    status += f"║~# ( 💉: {self._db['wasteland']['stimulators']} ) | ( 🔫: {self._db['wasteland']['weapons']} )\n"
                    status += "╠══════════════════╣\n"
                    status += f"║~$ ⚰ Умер: {self._db['wasteland']['death_date']}\n"
                else:
                    status += f"║~# ( 💉: {self._db['wasteland']['stimulators']} ) | ( 🔫: {self._db['wasteland']['weapons']} )\n"
                    status += "╠══════════════════╣\n"
                    status += f"║~$ ⏳ Время: {self._db['wasteland']['time']}\n"
                    status += f"║~$ ❤️ Здоровье: {self._db['wasteland']['health']}%\n"
                    status += f"║~$ 💉 Стимуляторов: {self._db['wasteland']['stimulators']} шт.\n"
                    status += f"║~$ 🔫 Оружия: {self._db['wasteland']['weapons']} ед.\n"
                    status += "╠══════════════════╣\n"
                    status += f"║~$ 💰 Крышек: {self._db['wasteland']['caps']} шт.\n"
                    status += f"║~$ 🏆 Рейтинга: {self._db['wasteland']['rating']}\n"
        if section in [None, "garden"]:
            status += f"║~$ 🌳 Сад: {self.strings['status_on'] if self._db['garden']['enabled'] else self.strings['status_off']}\n"
            if section == "garden":
                status += f"║~$ ✨ Рост: ( {self._db['garden']['status']} )\n"
                status += "╠══════════════════╣\n"
                status += "║~$ 📦 Склад:\n"
                for fruit, amount in self._db['garden']['stock'].items():
                    emoji = {"яблоко": "🍏", "черешня": "🍒", "персик": "🍑", "мандарин": "🍊"}[fruit]
                    status += f"║~#    {emoji} {fruit.capitalize()} - {amount}/шт.\n"
        if section in [None, "mine"]:
            status += f"║~$ ⛏ Шахта: {self.strings['status_on'] if self._db['mine']['enabled'] else self.strings['status_off']}\n"
            if section == "mine":
                pickaxe_level = {"Нет кирки": 1, "Каменная кирка": 1, "Железная кирка": 2, "Алмазная кирка": 3}.get(self._db['mine']['pickaxe'], 1)
                status += f"║~$ ⛏ ( {pickaxe_level} | 2 | 3 )\n"
                status += f"║~$ ✨ КД: {self.config['MineCooldown']} минут\n"
                status += f"║~$ ⚙️ Прочность: {self._db['mine']['durability']}\n"
                status += f"║~$ 📉 Высота: {self._db['mine']['depth']} м.\n"
                status += "╠══════════════════╣\n"
                status += "║~$ 📦 Склад:\n"
                for resource, amount in self._db['mine']['stock'].items():
                    emoji = {"песок": "🏜️", "уголь": "◾️", "железо": "🚂", "медь": "🟠", "серебро": "🥈", "алмаз": "💎", "уран": "☢️"}[resource]
                    status += f"║~#    {emoji} {resource.capitalize()} - {amount}/кг.\n"
        if section in [None, "guild"]:
            status += f"║~$ 🏛 Гильдия: {self.strings['status_on'] if self._db['guild']['enabled'] else self.strings['status_off']}\n"
            if section == "guild":
                status += f"║~$ ⚙ Авто-банки: {'✔️' if self._db['guild']['auto_banks'] else '✖️'}\n"
                status += f"║~$ ⚙ Авто-бутылки: {'✔️' if self._db['guild']['auto_bottles'] else '✖️'}\n"
                status += f"║~$ ⚙ Авто-атака-ги: {'✔️' if self._db['guild']['auto_guild_attack'] else '✖️'}\n"
                status += f"║~$ ⚙ Авто-атака-босса: {'✔️' if self._db['guild']['auto_boss_attack'] else '✖️'}\n"
                status += f"║~$ ⚙ Авто-закуп: {'✔️' if self._db['guild']['auto_purchase'] else '✖️'}\n"

        status += "╠══════════════════╣\n"
        status += "║👁‍🗨 Команды:\n"
        if section in [None, "people"]:
            status += f"╠═╣<code>.люди</code> - вкл/выкл\n"
        if section in [None, "bonus"]:
            status += f"╠═╣<code>.бонус</code> - вкл/выкл\n"
        if section in [None, "fuel"]:
            status += f"╠═╣<code>.бензин</code> - вкл/выкл\n"
        if section in [None, "greenhouse"]:
            status += f"╠═╣<code>.2теплица</code> - вкл/выкл\n"
        if section in [None, "wasteland"]:
            status += f"╠═╣<code>.2пустошь</code> - вкл/выкл\n"
        if section in [None, "garden"]:
            status += f"╠═╣<code>.2сад</code> - вкл/выкл\n"
        if section in [None, "mine"]:
            status += f"╠═╣<code>.2шахта</code> - вкл/выкл\n"
        if section in [None, "guild"]:
            status += f"╠═╣<code>.2гильдия</code> - вкл/выкл\n"
        status += "╚═══════════════════"
        return status

    async def _update_status_message(self, message: Message, section: str = None):
        # Buttons: 3 in first row, 2 in second row
        buttons = [
            [
                {"text": "Теплица", "data": b"greenhouse"},
                {"text": "Пустошь", "data": b"wasteland"},
                {"text": "Сад", "data": b"garden"}
            ],
            [
                {"text": "Шахта", "data": b"mine"},
                {"text": "Гильдия", "data": b"guild"}
            ]
        ] if section is None else [[{"text": "Назад", "data": b"back"}]]

        try:
            await utils.answer(message, await self._update_status_message_text(section), reply_markup=buttons)
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Status message updated for section: {section or 'main'}")
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Failed to update status message: {str(e)}")

    @loader.command(ru_doc="Показывает основной список авто-фарма")
    async def shcmd(self, message: Message):
        """Show main auto-farming status"""
        await self._update_status_message(message)

    @loader.command(ru_doc="Вкл/выкл авто-фарм людей")
    async def людиcmd(self, message: Message):
        """Toggle people auto-farming"""
        self._db['people']['enabled'] = not self._db['people']['enabled']
        await utils.answer(message, f"Авто-фарм людей {'включен' if self._db['people']['enabled'] else 'выключен'}")
        await self._update_status_message(message)

    @loader.command(ru_doc="Вкл/выкл ежедневный бонус")
    async def бонусcmd(self, message: Message):
        """Toggle daily bonus collection"""
        self._db['bonus']['enabled'] = not self._db['bonus']['enabled']
        await utils.answer(message, f"Ежедневный бонус {'включен' if self._db['bonus']['enabled'] else 'выключен'}")
        await self._update_status_message(message)

    @loader.command(ru_doc="Вкл/выкл авто-фарм бензина")
    async def бензинcmd(self, message: Message):
        """Toggle fuel auto-farming"""
        self._db['fuel']['enabled'] = not self._db['fuel']['enabled']
        await utils.answer(message, f"Авто-фарм бензина {'включен' if self._db['fuel']['enabled'] else 'выключен'}")
        await self._update_status_message(message)

    @loader.command(ru_doc="Вкл/выкл авто-фарм теплицы")
    async def теплицаcmd(self, message: Message):
        """Toggle greenhouse auto-farming"""
        self._db['greenhouse']['enabled'] = not self._db['greenhouse']['enabled']
        await utils.answer(message, f"Авто-фарм теплицы {'включен' if self._db['greenhouse']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "greenhouse")

    @loader.command(ru_doc="Вкл/выкл авто-фарм пустоши")
    async def пустошьcmd(self, message: Message):
        """Toggle wasteland auto-farming"""
        self._db['wasteland']['enabled'] = not self._db['wasteland']['enabled']
        await utils.answer(message, f"Авто-фарм пустоши {'включен' if self._db['wasteland']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "wasteland")

    @loader.command(ru_doc="Вкл/выкл авто-фарм сада")
    async def садcmd(self, message: Message):
        """Toggle garden auto-farming"""
        self._db['garden']['enabled'] = not self._db['garden']['enabled']
        await utils.answer(message, f"Авто-фарм сада {'включен' if self._db['garden']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "garden")

    @loader.command(ru_doc="Вкл/выкл авто-фарм шахты")
    async def шахтаcmd(self, message: Message):
        """Toggle mine auto-farming"""
        self._db['mine']['enabled'] = not self._db['mine']['enabled']
        await utils.answer(message, f"Авто-фарм шахты {'включен' if self._db['mine']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "mine")

    @loader.command(ru_doc="Вкл/выкл авто-фарм гильдии")
    async def гильдияcmd(self, message: Message):
        """Toggle guild auto-farming"""
        self._db['guild']['enabled'] = not self._db['guild']['enabled']
        await utils.answer(message, f"Авто-фарм гильдии {'включен' if self._db['guild']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "guild")

    @loader.command(ru_doc="Запустить автофарм вручную")
    async def startfarmcmd(self, message: Message):
        """Start auto-farm manually"""
        try:
            await self._auto_farm()
            await utils.answer(message, "Автофарм запущен вручную")
            await self.client.send_message(self._Shadow_Ultimat_channel, "Manual auto-farm started")
        except Exception as e:
            await utils.answer(message, f"Ошибка при запуске автофарма: {str(e)}")
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Manual auto-farm error: {str(e)}")

    @loader.watcher()
    async def callback_watcher(self, message: Message):
        try:
            if not message.reply_markup:
                await self.client.send_message(self._Shadow_Ultimat_channel, "Watcher: No reply_markup")
                return
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Watcher triggered: {message.reply_markup}")
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if hasattr(button, 'data') and button.data in [b"greenhouse", b"wasteland", b"garden", b"mine", b"guild", b"back"]:
                        await self.client.send_message(self._Shadow_Ultimat_channel, f"Processing button: {button.data.decode()}")
                        try:
                            async with self._lock:
                                if button.data == b"greenhouse":
                                    async with self._client.conversation(self._bot) as conv:
                                        await conv.send_message("Моя теплица")
                                        response = await conv.get_response()
                                        await self._parse_greenhouse(response)
                                    await utils.answer(message, await self._update_status_message_text("greenhouse"), reply_markup=[[{"text": "Назад", "data": b"back"}]])
                                elif button.data == b"wasteland":
                                    async with self._client.conversation(self._bot) as conv:
                                        await conv.send_message("Пустошь")
                                        response = await conv.get_response()
                                        await self._parse_wasteland(response)
                                    await utils.answer(message, await self._update_status_message_text("wasteland"), reply_markup=[[{"text": "Назад", "data": b"back"}]])
                                elif button.data == b"garden":
                                    async with self._client.conversation(self._bot) as conv:
                                        await conv.send_message("/garden")
                                        response = await conv.get_response()
                                        await self._parse_garden(response)
                                    await utils.answer(message, await self._update_status_message_text("garden"), reply_markup=[[{"text": "Назад", "data": b"back"}]])
                                elif button.data == b"mine":
                                    async with self._client.conversation(self._bot) as conv:
                                        await conv.send_message("/mine")
                                        response = await conv.get_response()
                                        await self._parse_mine(response)
                                    await utils.answer(message, await self._update_status_message_text("mine"), reply_markup=[[{"text": "Назад", "data": b"back"}]])
                                elif button.data == b"guild":
                                    await utils.answer(message, await self._update_status_message_text("guild"), reply_markup=[[{"text": "Назад", "data": b"back"}]])
                                elif button.data == b"back":
                                    await utils.answer(message, await self._update_status_message_text(), reply_markup=[
                                        [
                                            {"text": "Теплица", "data": b"greenhouse"},
                                            {"text": "Пустошь", "data": b"wasteland"},
                                            {"text": "Сад", "data": b"garden"}
                                        ],
                                        [
                                            {"text": "Шахта", "data": b"mine"},
                                            {"text": "Гильдия", "data": b"guild"}
                                        ]
                                    ])
                            await self.client.send_message(self._Shadow_Ultimat_channel, f"Button {button.data.decode()} processed successfully")
                        except Exception as e:
                            await self.client.send_message(self._Shadow_Ultimat_channel, f"Callback error for button {button.data.decode()}: {str(e)}")
                        break
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Watcher error: {str(e)}")

    async def _parse_people(self, message: Message):
        try:
            text = message.raw_text
            people_match = re.search(r"Людей в бункере: (\d+)", text)
            queue_match = re.search(r"Людей в очереди в бункер: (\d+)/(\d+)", text)
            max_match = re.search(r"Макс\. вместимость людей: (\d+)", text)
            if people_match and queue_match and max_match:
                self._db['people']['count'] = int(people_match.group(1))
                self._db['people']['queue'] = int(queue_match.group(1))
                self._db['people']['max'] = int(max_match.group(1))
                if self._db['people']['enabled'] and self._db['people']['queue'] > 0:
                    async with self._lock:
                        async with self._client.conversation(self._bot) as conv:
                            await conv.send_message(f"Впустить {self._db['people']['max'] - self._db['people']['count']}")
                            await conv.get_response()
            await self.client.send_message(self._Shadow_Ultimat_channel, "Parsed people data")
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Error parsing people: {str(e)}")
            raise

    async def _parse_bonus(self, message: Message):
        try:
            if "ежедневный бонус" in message.raw_text:
                self._db['bonus']['last_claim'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await self.client.send_message(self._Shadow_Ultimat_channel, "Bonus claimed")
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Error parsing bonus: {str(e)}")
            raise

    async def _parse_fuel(self, message: Message):
        try:
            text = message.raw_text
            fuel_match = re.search(r"Твой текущий запас бензина: (\d+)/(\d+) л\.", text)
            if fuel_match:
                self._db['fuel']['current'] = int(fuel_match.group(1))
                self._db['fuel']['max'] = int(fuel_match.group(2))
                if message.reply_markup and self._db['fuel']['enabled']:
                    for row in message.reply_markup.rows:
                        for button in row.buttons:
                            if hasattr(button, 'data') and button.data.startswith(b"buy_fuell_"):
                                await message.click(data=button.data)
                                await self.client.send_message(self._Shadow_Ultimat_channel, "Clicked fuel buy button")
                                break
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Error parsing fuel: {str(e)}")
            raise

    async def _parse_greenhouse(self, message: Message):
        try:
            text = message.raw_text
            xp_match = re.search(r"Опыт: (\d+)", text)
            water_match = re.search(r"Вода: (\d+)/(\d+) л\.", text)
            crop_match = re.search(r"Тебе доступна: (\S+)", text)
            stock_match = re.search(r"Твой склад:([\s\S]*?)(?=\n\n|$)", text)
            if xp_match and water_match and crop_match:
                self._db['greenhouse']['xp'] = int(xp_match.group(1))
                self._db['greenhouse']['water'] = int(water_match.group(1))
                self._db['greenhouse']['max_water'] = int(water_match.group(2))
                self._db['greenhouse']['crop'] = crop_match.group(1)
                if self._db['greenhouse']['enabled'] and self._db['greenhouse']['water'] > 0:
                    for xp_range, crop in self._resources_map.items():
                        if self._db['greenhouse']['xp'] in xp_range and crop == self._db['greenhouse']['crop'].lower():
                            async with self._lock:
                                async with self._client.conversation(self._bot) as conv:
                                    await conv.send_message(f"Вырастить {crop}")
                                    response = await conv.get_response()
                                    if "вырастил" in response.raw_text.lower():
                                        self._db['greenhouse']['stock'][crop] += 1
                                        self._db['greenhouse']['water'] -= 1
                                        await self.client.send_message(self._Shadow_Ultimat_channel, f"Grew {crop}")
                            break
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Error parsing greenhouse: {str(e)}")
            raise

    async def _parse_wasteland(self, message: Message):
        try:
            text = message.raw_text
            if "буря закончится" in text:
                self._db['wasteland']['death_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await self.client.send_message(self._Shadow_Ultimat_channel, "Wasteland death detected")
            elif "Время в пустоши" in text:
                time_match = re.search(r"Время в пустоши: ([\d\sчас\.мин\.]+)", text)
                health_match = re.search(r"Здоровье: (\d+)%", text)
                stimulators_match = re.search(r"Стимуляторов: (\d+) шт\.", text)
                weapons_match = re.search(r"Оружия: (\d+) ед\.", text)
                caps_match = re.search(r"Найдено крышек: (\d+) шт\.", text)
                rating_match = re.search(r"Получено рейтинга: (\d+)", text)
                if time_match and health_match and stimulators_match and weapons_match and caps_match and rating_match:
                    self._db['wasteland']['time'] = time_match.group(1)
                    self._db['wasteland']['health'] = int(health_match.group(1))
                    self._db['wasteland']['stimulators'] = int(stimulators_match.group(1))
                    self._db['wasteland']['weapons'] = int(weapons_match.group(1))
                    self._db['wasteland']['caps'] = int(caps_match.group(1))
                    self._db['wasteland']['rating'] = int(rating_match.group(1))
                    self._db['wasteland']['death_date'] = None
                    if self._db['wasteland']['health'] < 20 and message.reply_markup:
                        for row in message.reply_markup.rows:
                            for button in row.buttons:
                                if hasattr(button, 'data') and button.data.startswith(b"end_research_"):
                                    await message.click(data=button.data)
                                    await self.client.send_message(self._Shadow_Ultimat_channel, "Ended wasteland exploration")
                                    break
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Error parsing wasteland: {str(e)}")
            raise

    async def _parse_garden(self, message: Message):
        try:
            text = message.raw_text
            level_match = re.search(r"Уровень: (\d+)", text)
            status_match = re.search(r"Статус сада:\s*([\s\S]*?)(?=\n\n|$)", text)
            stock_match = re.search(r"Твой склад:([\s\S]*?)(?=\n\n|$)", text)
            if level_match and status_match:
                self._db['garden']['level'] = int(level_match.group(1))
                self._db['garden']['status'] = status_match.group(1).strip()
                if stock_match:
                    stock_text = stock_match.group(1).strip()
                    for fruit in self._db['garden']['stock']:
                        amount = re.search(rf"{fruit.capitalize()} - (\d+) шт\.", stock_text)
                        self._db['garden']['stock'][fruit] = int(amount.group(1)) if amount else 0
                await self.client.send_message(self._Shadow_Ultimat_channel, "Parsed garden data")
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Error parsing garden: {str(e)}")
            raise

    async def _parse_mine(self, message: Message):
        try:
            text = message.raw_text
            pickaxe_match = re.search(r"Кирка: ([^\n]+)", text)
            durability_match = re.search(r"Прочность: (\d+)", text)
            depth_match = re.search(r"Уровень погружения: (\d+) м\.", text)
            stock_match = re.search(r"Твой склад:([\s\S]*?)(?=\n\n|$)", text)
            if pickaxe_match and durability_match and depth_match:
                self._db['mine']['pickaxe'] = pickaxe_match.group(1)
                self._db['mine']['durability'] = int(durability_match.group(1))
                self._db['mine']['depth'] = int(depth_match.group(1))
                if stock_match:
                    stock_text = stock_match.group(1).strip()
                    for resource in self._db['mine']['stock']:
                        amount = re.search(rf"{resource.capitalize()} - (\d+) кг\.", stock_text)
                        self._db['mine']['stock'][resource] = int(amount.group(1)) if amount else 0
                if self._db['mine']['enabled'] and self._db['mine']['durability'] == 0:
                    async with self._lock:
                        async with self._client.conversation(self._bot) as conv:
                            await conv.send_message("Б")
                            m = await conv.get_response()
                            balance = int("".join(s for s in m.raw_text.split("Баланс:")[1].split('/')[0].strip() if s.isdigit()))
                            if balance >= 1000000:
                                await conv.send_message("Купить алмазную кирку")
                            elif balance >= 200000:
                                await conv.send_message("Купить железную кирку")
                            elif balance >= 30000:
                                await conv.send_message("Купить каменную кирку")
                            await conv.get_response()
                            await self.client.send_message(self._Shadow_Ultimat_channel, "Bought pickaxe")
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Error parsing mine: {str(e)}")
            raise

    async def _mine(self):
        try:
            async with self._lock:
                async with self._client.conversation(self._bot) as conv:
                    await asyncio.sleep(2)
                    await conv.send_message("копать")
                    m = await conv.get_response()
                    if "у тебя нет кирки" in m.raw_text:
                        await asyncio.sleep(2)
                        await conv.send_message("Б")
                        m = await conv.get_response()
                        balance = int("".join(s for s in m.raw_text.split("Баланс:")[1].split('/')[0].strip() if s.isdigit()))
                        if balance < 30000:
                            await self.client.send_message(self._Shadow_Ultimat_channel, "Insufficient balance for pickaxe")
                            return
                        await asyncio.sleep(2)
                        if balance >= 1000000:
                            await conv.send_message("Купить алмазную кирку")
                        elif balance >= 200000:
                            await conv.send_message("Купить железную кирку")
                        else:
                            await conv.send_message("Купить каменную кирку")
                        await conv.get_response()
                        await asyncio.sleep(2)
                        await conv.send_message("копать")
                        m = await conv.get_response()

                    if 'отдохнёт' in m.raw_text:
                        await self.client.send_message(self._Shadow_Ultimat_channel, "Mining cooldown active")
                        return

                    resources_result = m.raw_text.split("ты нашёл")
                    resources = 'Воздух'
                    if len(resources_result) > 1:
                        resources_text = resources_result[1].split(' ')[1:]
                        resources = ' '.join(resources_text).split('.')[0]

                    probability_result = m.raw_text.split("вероятностью")
                    probability = 0
                    if len(probability_result) > 1:
                        probability_text = probability_result[1]
                        probability = int("".join(s for s in probability_text.split('%')[0].strip() if s.isdigit()))

                    if self.config["MineDiamond"] and ("ты нашёл 💎 Алмаз." in m.message or probability == 100):
                        await asyncio.sleep(2)
                        await m.click(0)
                        m = await conv.get_edit()
                        if "Прочность твоей кирки уменьшена" in m.text:
                            await self.client.send_message(self._Shadow_Ultimat_channel, "Прочность кирки уменьшена\n#Прочность")
                        else:
                            await self.client.send_message(self._Shadow_Ultimat_channel, f"Ты добыл {resources} с шансом {probability}%\n#Добыча")
                    elif self.config["SkipNonUranium"] and "Уран" not in resources:
                        await asyncio.sleep(2)
                        await m.click(1)
                        await self.client.send_message(self._Shadow_Ultimat_channel, f"Ты пропустил {resources} с шансом {probability}%\n#Пропуск")
                    elif self.config["MineProbability"] and 80 <= probability <= 100:
                        await asyncio.sleep(2)
                        await m.click(0)
                        m = await conv.get_edit()
                        if "Прочность твоей кирки уменьшена" in m.text:
                            await self.client.send_message(self._Shadow_Ultimat_channel, "Прочность кирки уменьшена\n#Прочность")
                        else:
                            await self.client.send_message(self._Shadow_Ultimat_channel, f"Ты добыл {resources} с шансом {probability}%\n#Добыча")
                    else:
                        await asyncio.sleep(2)
                        await m.click(0)
                        m = await conv.get_edit()
                        if "Прочность твоей кирки уменьшена" in m.text:
                            await self.client.send_message(self._Shadow_Ultimat_channel, "Прочность кирки уменьшена\n#Прочность")
                        else:
                            await self.client.send_message(self._Shadow_Ultimat_channel, f"Ты добыл {resources} с шансом {probability}%\n#Добыча")
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Error in mining: {str(e)}")
            raise

    async def _auto_farm(self):
        try:
            await self.client.send_message(self._Shadow_Ultimat_channel, "Auto-farm loop running")
            async with self._lock:
                if self._db['people']['enabled']:
                    async with self._client.conversation(self._bot) as conv:
                        await conv.send_message("/me")
                        response = await conv.get_response()
                        await self._parse_people(response)
                    await asyncio.sleep(2)

                if self._db['bonus']['enabled']:
                    last_claim = self._db['bonus']['last_claim']
                    if last_claim:
                        last_claim = datetime.strptime(last_claim, "%Y-%m-%d %H:%M:%S")
                    if not last_claim or (datetime.now() - last_claim) >= timedelta(hours=24):
                        async with self._client.conversation(self._bot) as conv:
                            await conv.send_message("/bonus")
                            response = await conv.get_response()
                            await self._parse_bonus(response)
                    await asyncio.sleep(2)

                if self._db['fuel']['enabled']:
                    async with self._client.conversation(self._bot) as conv:
                        await conv.send_message("/fuel")
                        response = await conv.get_response()
                        await self._parse_fuel(response)
                    await asyncio.sleep(2)

                if self._db['greenhouse']['enabled']:
                    async with self._client.conversation(self._bot) as conv:
                        await conv.send_message("Моя теплица")
                        response = await conv.get_response()
                        await self._parse_greenhouse(response)
                    await asyncio.sleep(2)

                if self._db['wasteland']['enabled'] and not self._db['wasteland']['death_date']:
                    async with self._client.conversation(self._bot) as conv:
                        if self.config["StimulatorsToBuy"] > 0:
                            await conv.send_message(f"Купить стимуляторы {self.config['StimulatorsToBuy']}")
                            await conv.get_response()
                            await asyncio.sleep(2)
                        if self.config["WeaponsToBuy"] > 0:
                            await conv.send_message(f"Купить оружие {self.config['WeaponsToBuy']}")
                            await conv.get_response()
                            await asyncio.sleep(2)
                        await conv.send_message("Исследовать пустошь")
                        response = await conv.get_response()
                        if "укажи количество стимуляторов" in response.raw_text:
                            stimulators = min(int(re.search(r"У тебя: (\d+)", response.raw_text).group(1)), int(re.search(r"Максимум можешь дать: (\d+)", response.raw_text).group(1)))
                            await conv.send_message(str(stimulators))
                            response = await conv.get_response()
                            await asyncio.sleep(2)
                        if "укажи количество оружия" in response.raw_text:
                            weapons = min(int(re.search(r"У тебя: (\d+)", response.raw_text).group(1)), int(re.search(r"Максимум можешь дать: (\d+)", response.raw_text).group(1)))
                            await conv.send_message(str(weapons))
                            await conv.get_response()
                            await asyncio.sleep(2)
                        await asyncio.sleep(15 * 60)  # Check every 15 minutes
                        await conv.send_message("Пустошь")
                        response = await conv.get_response()
                        await self._parse_wasteland(response)
                    await asyncio.sleep(2)

                if self._db['garden']['enabled']:
                    async with self._client.conversation(self._bot) as conv:
                        await conv.send_message("/garden")
                        response = await conv.get_response()
                        await self._parse_garden(response)
                    await asyncio.sleep(2)

                if self._db['mine']['enabled']:
                    await self._mine()
                    await asyncio.sleep(self.config["MineCooldown"] * 60)

                if self._db['guild']['enabled']:
                    await self.client.send_message(self._Shadow_Ultimat_channel, "Guild auto-farm placeholder")
                    await asyncio.sleep(2)
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Auto-farm error: {str(e)}")
            raise
