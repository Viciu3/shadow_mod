import asyncio
import logging
import time
import re
from datetime import datetime, timedelta
from telethon import functions, types
from telethon.tl.types import Message, ChatAdminRights
from telethon.tl.types import InlineKeyboardMarkup, InlineKeyboardButton
from .. import loader, utils
import json

logger = logging.getLogger(__name__)

@loader.tds
class ShadowUltimat(loader.Module):
    """Shadow_Ultimat - Auto-farming module for @bfgbunker_bot by @familiarrrrrr"""
    strings = {"name": "ShadowUltimat", "status_on": "🟢", "status_off": "🔴"}
    strings_ru = {"status_on": "🟢", "status_off": "🔴"}

    def __init__(self):
        self._bot = "@bfgbunker_bot"
        self._Shadow_Ultimat_channel = None
        self._lock = asyncio.Lock()
        self._status_message_id = None
        self.config = loader.ModuleConfig(
            loader.ConfigValue("PeopleEnabled", True, "Enable auto-farming for people", validator=loader.validators.Boolean()),
            loader.ConfigValue("BonusEnabled", True, "Enable daily bonus collection", validator=loader.validators.Boolean()),
            loader.ConfigValue("FuelEnabled", True, "Enable auto-farming for fuel", validator=loader.validators.Boolean()),
            loader.ConfigValue("GreenhouseEnabled", True, "Enable auto-farming for greenhouse", validator=loader.validators.Boolean()),
            loader.ConfigValue("WastelandEnabled", True, "Enable auto-farming for wasteland", validator=loader.validators.Boolean()),
            loader.ConfigValue("GardenEnabled", True, "Enable auto-farming for garden", validator=loader.validators.Boolean()),
            loader.ConfigValue("MineEnabled", True, "Enable auto-farming for mine", validator=loader.validators.Boolean()),
            loader.ConfigValue("GuildEnabled", True, "Enable auto-farming for guild", validator=loader.validators.Boolean()),
            loader.ConfigValue("StimulatorsToBuy", 1, "Number of stimulators to buy", validator=loader.validators.Integer(minimum=0)),
            loader.ConfigValue("WeaponsToBuy", 1, "Number of weapons to buy", validator=loader.validators.Integer(minimum=0)),
            loader.ConfigValue("MineCooldown", 6, "Cooldown between mining attempts (minutes)", validator=loader.validators.Integer(minimum=1)),
            loader.ConfigValue("MineDiamond", True, "Mine diamonds automatically", validator=loader.validators.Boolean()),
            loader.ConfigValue("SkipNonUranium", False, "Skip non-uranium resources", validator=loader.validators.Boolean()),
            loader.ConfigValue("MineProbability", True, "Mine based on probability (80-100%)", validator=loader.validators.Boolean()),
            loader.ConfigValue("BottlesTime", 2, "Time between bottle exchanges (seconds)", validator=loader.validators.Float()),
            loader.ConfigValue("MessageCount", 120, "Number of messages before protection pause", validator=loader.validators.Integer()),
            loader.ConfigValue("prefix", ".", "Prefix for commands", validator=loader.validators.String())
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
        try:
            self._db = {
                "people": {"enabled": True, "count": 0, "queue": 0, "max": 0},
                "bonus": {"enabled": True, "last_claim": None},
                "fuel": {"enabled": True, "current": 0, "max": 0},
                "greenhouse": {
                    "enabled": True, "xp": 0, "water": 0, "max_water": 0, "crop": "",
                    "stock": {"картошка": 0, "морковь": 0, "рис": 0, "свекла": 0, "огурец": 0, "фасоль": 0, "помидор": 0}
                },
                "wasteland": {
                    "enabled": True, "time": "0 час. 0 мин.", "health": 100, "stimulators": 0, "weapons": 0,
                    "caps": 0, "rating": 0, "death_date": None
                },
                "garden": {
                    "enabled": True, "level": 1, "status": "Пустует",
                    "stock": {"яблоко": 0, "черешня": 0, "персик": 0, "мандарин": 0}
                },
                "mine": {
                    "enabled": True, "pickaxe": "Нет кирки", "durability": 0, "depth": 0,
                    "stock": {"песок": 0, "уголь": 0, "железо": 0, "медь": 0, "серебро": 0, "алмаз": 0, "уран": 0}
                },
                "guild": {
                    "enabled": True, "auto_banks": False, "auto_bottles": False,
                    "auto_guild_attack": False, "auto_boss_attack": False, "auto_purchase": False
                },
                "bottles": 0,
                "max_balance": 0
            }
            self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
            if not self.db.get(self.__class__.__name__, "prefix"):
                self.db.set(self.__class__.__name__, "prefix", self.config["prefix"])
            await self.client.send_message("me", "Database initialized successfully")
        except Exception as e:
            await self.client.send_message("me", f"Failed to initialize database: {str(e)}")

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

        try:
            asyncio.create_task(self.main_loop())
            await self.client.send_message(self._Shadow_Ultimat_channel, "Auto-farm loop started")
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Failed to start auto-farm loop: {str(e)}")

    async def main_loop(self):
        """Main loop for auto-farming, inspired by BFGBunkerMod"""
        while True:
            try:
                if self.config["PeopleEnabled"] and (not self.db.get(self.__class__.__name__, "people_time") or (time.time() - self.db.get(self.__class__.__name__, "people_time")) >= 1805):
                    await self._parse_people()
                    self.db.set(self.__class__.__name__, "people_time", int(time.time()))

                if self.config["BonusEnabled"] and (not self.db.get(self.__class__.__name__, "bonus_time") or (time.time() - self.db.get(self.__class__.__name__, "bonus_time")) >= 24 * 3600):
                    await self._parse_bonus()
                    self.db.set(self.__class__.__name__, "bonus_time", int(time.time()))

                if self.config["FuelEnabled"] and (not self.db.get(self.__class__.__name__, "fuel_time") or (time.time() - self.db.get(self.__class__.__name__, "fuel_time")) >= 3629):
                    await self._parse_fuel()
                    self.db.set(self.__class__.__name__, "fuel_time", int(time.time()))

                if self.config["GreenhouseEnabled"] and (not self.db.get(self.__class__.__name__, "greenhouse_time") or (time.time() - self.db.get(self.__class__.__name__, "greenhouse_time")) >= 1212):
                    await self._parse_greenhouse()
                    self.db.set(self.__class__.__name__, "greenhouse_time", int(time.time()))

                if self.config["WastelandEnabled"] and (not self.db.get(self.__class__.__name__, "wasteland_time") or (time.time() - self.db.get(self.__class__.__name__, "wasteland_time")) >= 15 * 60):
                    await self._parse_wasteland()
                    self.db.set(self.__class__.__name__, "wasteland_time", int(time.time()))

                if self.config["GardenEnabled"] and (not self.db.get(self.__class__.__name__, "garden_time") or (time.time() - self.db.get(self.__class__.__name__, "garden_time")) >= 1212):
                    await self._parse_garden()
                    self.db.set(self.__class__.__name__, "garden_time", int(time.time()))

                if self.config["MineEnabled"] and (not self.db.get(self.__class__.__name__, "mine_time") or (time.time() - self.db.get(self.__class__.__name__, "mine_time")) >= self.config["MineCooldown"] * 60):
                    await self._mine()
                    self.db.set(self.__class__.__name__, "mine_time", int(time.time()))

                if self.config["GuildEnabled"]:
                    await self.client.send_message(self._Shadow_Ultimat_channel, "Guild auto-farm placeholder")
            except Exception as e:
                await self.client.send_message(self._Shadow_Ultimat_channel, f"Auto-farm error: {str(e)}")
            await asyncio.sleep(60)

    async def _update_status_message_text(self, section: str = None) -> str:
        """Helper to generate status message text"""
        prefix = self.config["prefix"]
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
            status += f"╠═╣<code>{prefix}люди</code> - вкл/выкл\n"
        if section in [None, "bonus"]:
            status += f"╠═╣<code>{prefix}бонус</code> - вкл/выкл\n"
        if section in [None, "fuel"]:
            status += f"╠═╣<code>{prefix}бензин</code> - вкл/выкл\n"
        if section in [None, "greenhouse"]:
            status += f"╠═╣<code>{prefix}теплица</code> - вкл/выкл\n"
        if section in [None, "wasteland"]:
            status += f"╠═╣<code>{prefix}пустошь</code> - вкл/выкл\n"
        if section in [None, "garden"]:
            status += f"╠═╣<code>{prefix}сад</code> - вкл/выкл\n"
        if section in [None, "mine"]:
            status += f"╠═╣<code>{prefix}шахта</code> - вкл/выкл\n"
        if section in [None, "guild"]:
            status += f"╠═╣<code>{prefix}гильдия</code> - вкл/выкл\n"
        if section in [None, "bottles"]:
            status += f"╠═╣<code>{prefix}bottles</code> - вкл/выкл обмен бутылок\n"
        status += f"╠═╣<code>{prefix}prefixcmd [префикс]</code> - установить префикс\n"
        status += "╚═══════════════════"
        return status

    async def _update_status_message(self, message: Message, section: str = None):
        buttons = [
            [
                InlineKeyboardButton(text="Теплица", callback_data="greenhouse"),
                InlineKeyboardButton(text="Пустошь", callback_data="wasteland"),
                InlineKeyboardButton(text="Сад", callback_data="garden")
            ],
            [
                InlineKeyboardButton(text="Шахта", callback_data="mine"),
                InlineKeyboardButton(text="Гильдия", callback_data="guild")
            ]
        ] if section is None else [[InlineKeyboardButton(text="Назад", callback_data="back")]]

        try:
            chat = await message.get_chat()
            new_message = await self.client.send_message(
                chat,
                await self._update_status_message_text(section),
                reply_to=message.id,
                buttons=buttons
            )
            self._status_message_id = getattr(new_message, 'id', None)
            if not self._status_message_id:
                await self.client.send_message(self._Shadow_Ultimat_channel, f"Warning: Could not retrieve message ID for section: {section or 'main'}")
            else:
                await self.client.send_message(self._Shadow_Ultimat_channel, f"Status message updated for section: {section or 'main'}, ID: {self._status_message_id}")
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
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await utils.answer(message, f"Авто-фарм людей {'включен' if self._db['people']['enabled'] else 'выключен'}")
        await self._update_status_message(message)

    @loader.command(ru_doc="Вкл/выкл ежедневный бонус")
    async def бонусcmd(self, message: Message):
        """Toggle daily bonus collection"""
        self._db['bonus']['enabled'] = not self._db['bonus']['enabled']
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await utils.answer(message, f"Ежедневный бонус {'включен' if self._db['bonus']['enabled'] else 'выключен'}")
        await self._update_status_message(message)

    @loader.command(ru_doc="Вкл/выкл авто-фарм бензина")
    async def бензинcmd(self, message: Message):
        """Toggle fuel auto-farming"""
        self._db['fuel']['enabled'] = not self._db['fuel']['enabled']
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await utils.answer(message, f"Авто-фарм бензина {'включен' if self._db['fuel']['enabled'] else 'выключен'}")
        await self._update_status_message(message)

    @loader.command(ru_doc="Вкл/выкл авто-фарм теплицы")
    async def теплицаcmd(self, message: Message):
        """Toggle greenhouse auto-farming"""
        self._db['greenhouse']['enabled'] = not self._db['greenhouse']['enabled']
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await utils.answer(message, f"Авто-фарм теплицы {'включен' if self._db['greenhouse']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "greenhouse")

    @loader.command(ru_doc="Вкл/выкл авто-фарм пустоши")
    async def пустошьcmd(self, message: Message):
        """Toggle wasteland auto-farming"""
        self._db['wasteland']['enabled'] = not self._db['wasteland']['enabled']
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await utils.answer(message, f"Авто-фарм пустоши {'включен' if self._db['wasteland']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "wasteland")

    @loader.command(ru_doc="Вкл/выкл авто-фарм сада")
    async def садcmd(self, message: Message):
        """Toggle garden auto-farming"""
        self._db['garden']['enabled'] = not self._db['garden']['enabled']
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await utils.answer(message, f"Авто-фарм сада {'включен' if self._db['garden']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "garden")

    @loader.command(ru_doc="Вкл/выкл авто-фарм шахты")
    async def шахтаcmd(self, message: Message):
        """Toggle mine auto-farming"""
        self._db['mine']['enabled'] = not self._db['mine']['enabled']
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await utils.answer(message, f"Авто-фарм шахты {'включен' if self._db['mine']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "mine")

    @loader.command(ru_doc="Вкл/выкл авто-фарм гильдии")
    async def гильдияcmd(self, message: Message):
        """Toggle guild auto-farming"""
        self._db['guild']['enabled'] = not self._db['guild']['enabled']
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await utils.answer(message, f"Авто-фарм гильдии {'включен' if self._db['guild']['enabled'] else 'выключен'}")
        await self._update_status_message(message, "guild")

    @loader.command(ru_doc="Установить префикс для команд (по умолчанию '.')")
    async def prefixcmd(self, message: Message):
        """Set command prefix (default '.')"""
        args = utils.get_args_raw(message).strip()
        if not args:
            await utils.answer(message, f"Текущий префикс: <code>{self.config['prefix']}</code>")
            return
        if len(args) > 10:
            await utils.answer(message, "Префикс слишком длинный (макс. 10 символов)")
            return
        self.config["prefix"] = args
        self.db.set(self.__class__.__name__, "prefix", args)
        await utils.answer(message, f"Префикс установлен: <code>{args}</code>")
        await self._update_status_message(message)

    @loader.command(ru_doc="Запустить автофарм вручную")
    async def startfarmcmd(self, message: Message):
        """Start auto-farm manually"""
        try:
            await self._run_farm_tasks()
            await utils.answer(message, "Автофарм запущен вручную")
            await self.client.send_message(self._Shadow_Ultimat_channel, "Manual auto-farm started")
        except Exception as e:
            await utils.answer(message, f"Ошибка при запуске автофарма: {str(e)}")
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Manual auto-farm error: {str(e)}")

    @loader.command(ru_doc="Автоматический обмен бутылок")
    async def bottlescmd(self, message: Message):
        """Toggle automatic bottle exchange"""
        if self.db.get(self.__class__.__name__, '_bottles_status', False):
            self.db.set(self.__class__.__name__, '_bottles_status', False)
            await utils.answer(message, "<b>Обмен бутылок остановлен!</b>")
        else:
            self.db.set(self.__class__.__name__, '_bottles_status', True)
            await utils.answer(message, "<b>Обмен бутылок запущен!</b>")
            asyncio.create_task(self._bottle_loop(message))

    @loader.watcher()
    async def callback_watcher(self, message: Message):
        try:
            if not message.reply_markup or message.id != self._status_message_id:
                return  # Тихо игнорируем сообщения без кнопок или с неверным ID

            valid_buttons = {b"greenhouse", b"wasteland", b"garden", b"mine", b"guild", b"back"}
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if hasattr(button, 'data') and button.data in valid_buttons:
                        await self.client.send_message(self._Shadow_Ultimat_channel, f"Processing button: {button.data.decode()}")
                        async with self._lock:
                            if button.data == b"greenhouse":
                                await self._parse_greenhouse()
                                await self._update_status_message(message, "greenhouse")
                            elif button.data == b"wasteland":
                                await self._parse_wasteland()
                                await self._update_status_message(message, "wasteland")
                            elif button.data == b"garden":
                                await self._parse_garden()
                                await self._update_status_message(message, "garden")
                            elif button.data == b"mine":
                                await self._parse_mine()
                                await self._update_status_message(message, "mine")
                            elif button.data == b"guild":
                                await self._update_status_message(message, "guild")
                            elif button.data == b"back":
                                await self._update_status_message(message)
                            await self.client.send_message(self._Shadow_Ultimat_channel, f"Button {button.data.decode()} processed successfully")
                        return
        except Exception as e:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Watcher error: {str(e)}")

    async def _parse_people(self):
        async with self._lock:
            async with self._client.conversation(self._bot) as conv:
                await asyncio.sleep(2)
                await conv.send_message("/me")
                response = await conv.get_response()
                text = response.raw_text
                people_match = re.search(r"Людей в бункере: (\d+)", text)
                queue_match = re.search(r"Людей в очереди в бункер: (\d+)/(\d+)", text)
                max_match = re.search(r"Макс\. вместимость людей: (\d+)", text)
                if people_match and queue_match and max_match:
                    self._db['people']['count'] = int(people_match.group(1))
                    self._db['people']['queue'] = int(queue_match.group(1))
                    self._db['people']['max'] = int(max_match.group(1))
                    if self._db['people']['enabled'] and self._db['people']['queue'] > 0:
                        await asyncio.sleep(2)
                        await conv.send_message(f"Впустить {self._db['people']['max'] - self._db['people']['count']}")
                        await conv.get_response()
                    self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
                await self.client.send_message(self._Shadow_Ultimat_channel, "Parsed people data")

    async def _parse_bonus(self):
        async with self._lock:
            async with self._client.conversation(self._bot) as conv:
                await asyncio.sleep(2)
                await conv.send_message("/bonus")
                response = await conv.get_response()
                if "ежедневный бонус" in response.raw_text:
                    self._db['bonus']['last_claim'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
                    await self.client.send_message(self._Shadow_Ultimat_channel, "Bonus claimed")

    async def _parse_fuel(self):
        async with self._lock:
            async with self._client.conversation(self._bot) as conv:
                await asyncio.sleep(2)
                await conv.send_message("/fuel")
                response = await conv.get_response()
                text = response.raw_text
                fuel_match = re.search(r"Твой текущий запас бензина: (\d+)/(\d+) л\.", text)
                if fuel_match:
                    self._db['fuel']['current'] = int(fuel_match.group(1))
                    self._db['fuel']['max'] = int(fuel_match.group(2))
                    if self._db['fuel']['enabled'] and response.reply_markup:
                        await asyncio.sleep(2)
                        for row in response.reply_markup.rows:
                            for button in row.buttons:
                                if hasattr(button, 'data') and button.data.startswith(b"buy_fuell_"):
                                    await response.click(data=button.data)
                                    await self.client.send_message(self._Shadow_Ultimat_channel, f"Clicked fuel buy button: {button.data.decode()}")
                                    break
                        await conv.get_response()
                    self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
                    await self.client.send_message(self._Shadow_Ultimat_channel, "Parsed fuel data")

    async def _parse_greenhouse(self):
        async with self._lock:
            async with self._client.conversation(self._bot) as conv:
                await asyncio.sleep(2)
                await conv.send_message("Моя теплица")
                response = await conv.get_response()
                text = response.raw_text
                xp_match = re.search(r"Опыт: (\d+)", text)
                water_match = re.search(r"Вода: (\d+)/(\d+) л\.", text)
                crop_match = re.search(r"Тебе доступна: (\S+)", text)
                stock_match = re.search(r"Твой склад:([\ Nivel de usuario: (\d+)/(\d+)
  if level_match:
    self._db['user']['level'] = int(level_match.group(1))
    self._db['user']['max_level'] = int(level_match.group(2))
  self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
  await self.client.send_message(self._Shadow_Ultimat_channel, "Parsed user data")

async def _parse_wasteland(self):
  async with self._lock:
    async with self._client.conversation(self._bot) as conv:
      if self.config["StimulatorsToBuy"] > 0:
        await asyncio.sleep(2)
        await conv.send_message(f"Купить стимуляторы {self.config['StimulatorsToBuy']}")
        await conv.get_response()
      if self.config["WeaponsToBuy"] > 0:
        await asyncio.sleep(2)
        await conv.send_message(f"Купить оружие {self.config['WeaponsToBuy']}")
        await conv.get_response()
      await asyncio.sleep(2)
      await conv.send_message("Исследовать пустошь")
      response = await conv.get_response()
      if "укажи количество стимуляторов" in response.raw_text:
        stimulators = min(int(re.search(r"У тебя: (\d+)", response.raw_text).group(1)), int(re.search(r"Максимум можешь дать: (\d+)", response.raw_text).group(1)))
        await asyncio.sleep(2)
        await conv.send_message(str(stimulators))
        response = await conv.get_response()
      if "укажи количество оружия" in response.raw_text:
        weapons = min(int(re.search(r"У тебя: (\d+)", response.raw_text).group(1)), int(re.search(r"Максимум можешь дать: (\d+)", response.raw_text).group(1)))
        await asyncio.sleep(2)
        await conv.send_message(str(weapons))
        response = await conv.get_response()
      await asyncio.sleep(15 * 60)
      await conv.send_message("Пустошь")
      response = await conv.get_response()
      text = response.raw_text
      if "буря закончится" in text:
        self._db['wasteland']['death_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
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
          if self._db['wasteland']['enabled'] and self._db['wasteland']['health'] < 20 and response.reply_markup:
            await asyncio.sleep(2)
            for row in response.reply_markup.rows:
              for button in row.buttons:
                if hasattr(button, 'data') and button.data.startswith(b"end_research_"):
                  await response.click(data=button.data)
                  await self.client.send_message(self._Shadow_Ultimat_channel, f"Clicked wasteland end button: {button.data.decode()}")
                  break
            await conv.get_response()
          self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await self.client.send_message(self._Shadow_Ultimat_channel, "Parsed wasteland data")

async def _parse_garden(self):
  async with self._lock:
    async with self._client.conversation(self._bot) as conv:
      await asyncio.sleep(2)
      await conv.send_message("/garden")
      response = await conv.get_response()
      text = response.raw_text
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
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await self.client.send_message(self._Shadow_Ultimat_channel, "Parsed garden data")

async def _parse_mine(self):
  async with self._lock:
    async with self._client.conversation(self._bot) as conv:
      await asyncio.sleep(2)
      await conv.send_message("/mine")
      response = await conv.get_response()
      text = response.raw_text
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
          await asyncio.sleep(2)
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
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
        await self.client.send_message(self._Shadow_Ultimat_channel, "Parsed mine data")

async def _mine(self):
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

      if self._db['mine']['enabled'] and m.reply_markup:
        await asyncio.sleep(2)
        if self.config["MineDiamond"] and ("ты нашёл 💎 Алмаз." in m.raw_text or probability == 100):
          await m.click(0)
          m = await conv.get_edit()
          if "Прочность твоей кирки уменьшена" in m.text:
            await self.client.send_message(self._Shadow_Ultimat_channel, "Прочность кирки уменьшена\n#Прочность")
          else:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Ты добыл {resources} с шансом {probability}%\n#Добыча")
        elif self.config["SkipNonUranium"] and "Уран" not in resources:
          await m.click(1)
          await self.client.send_message(self._Shadow_Ultimat_channel, f"Ты пропустил {resources} с шансом {probability}%\n#Пропуск")
        elif self.config["MineProbability"] and 80 <= probability <= 100:
          await m.click(0)
          m = await conv.get_edit()
          if "Прочность твоей кирки уменьшена" in m.text:
            await self.client.send_message(self._Shadow_Ultimat_channel, "Прочность кирки уменьшена\n#Прочность")
          else:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Ты добыл {resources} с шансом {probability}%\n#Добыча")
        else:
          await m.click(0)
          m = await conv.get_edit()
          if "Прочность твоей кирки уменьшена" in m.text:
            await self.client.send_message(self._Shadow_Ultimat_channel, "Прочность кирки уменьшена\n#Прочность")
          else:
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Ты добыл {resources} с шансом {probability}%\n#Добыча")
        self.db.set(self.__class__.__name__, "db", json.dumps(self._db))

async def _bottle_loop(self, message: Message):
  bottle_check_interval = 30 * 60
  last_bottle_check = 0
  message_count = 0
  while self.db.get(self.__class__.__name__, '_bottles_status', False):
    try:
      current_time = time.time()
      async with self._lock:
        if current_time - last_bottle_check >= bottle_check_interval:
          async with self._client.conversation(self._bot) as conv:
            await asyncio.sleep(2)
            await conv.send_message("Б")
            response = await conv.get_response()
            bottles = int("".join(filter(str.isdigit, response.raw_text.split("Бутылок:")[1].split()[0].strip())))
            self._db['bottles'] = bottles
            max_balance = int("".join(filter(str.isdigit, response.raw_text.split("Баланс:")[1].split("/")[1].strip())))
            self._db['max_balance'] = max_balance
            self.db.set(self.__class__.__name__, "db", json.dumps(self._db))
            await self.client.send_message(self._Shadow_Ultimat_channel, f"Checked bottles: {bottles}, max balance: {max_balance}")
            last_bottle_check = current_time

        await asyncio.sleep(2)
        async with self._client.conversation(self._bot) as conv:
          await conv.send_message("пополнить бутылки максимум")
          message_count += 1
          await asyncio.sleep(self.config["BottlesTime"])

        if self._db['bottles'] <= 0:
          self.db.set(self.__class__.__name__, '_bottles_status', False)
          await utils.answer(message, "<b>Обмен бутылок остановлен из-за недостатка бутылок!</b>")
          return

        if message_count >= self.config['MessageCount']:
          await self.client.send_message(self._Shadow_Ultimat_channel, "Protection pause: stopping for 2 minutes")
          await asyncio.sleep(120)
          message_count = 0
    except Exception as e:
      await self.client.send_message(self._Shadow_Ultimat_channel, f"Bottle loop error: {str(e)}")
  await utils.answer(message, "<b>Обмен бутылок остановлен!</b>")

async def _run_farm_tasks(self):
  """Run all farm tasks manually"""
  async with self._lock:
    if self._db['people']['enabled']:
      await self._parse_people()
      await asyncio.sleep(2)
    if self._db['bonus']['enabled']:
      last_claim = self._db['bonus']['last_claim']
      if last_claim:
        last_claim = datetime.strptime(last_claim, "%Y-%m-%d %H:%M:%S")
      if not last_claim or (datetime.now() - last_claim) >= timedelta(hours=24):
        await self._parse_bonus()
        await asyncio.sleep(2)
    if self._db['fuel']['enabled']:
      await self._parse_fuel()
      await asyncio.sleep(2)
    if self._db['greenhouse']['enabled']:
      await self._parse_greenhouse()
      await asyncio.sleep(2)
    if self._db['wasteland']['enabled'] and not self._db['wasteland']['death_date']:
      await self._parse_wasteland()
      await asyncio.sleep(2)
    if self._db['garden']['enabled']:
      await self._parse_garden()
      await asyncio.sleep(2)
    if self._db['mine']['enabled']:
      await self._mine()
      await asyncio.sleep(2)
    if self._db['guild']['enabled']:
      await self.client.send_message(self._Shadow_Ultimat_channel, "Guild auto-farm placeholder")
      await asyncio.sleep(2)
