import json
import os
import pathlib
import re
import asyncio
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ShadowUltimatCore:
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self._resources_map = {
            range(0, 500): "картошка",
            range(501, 2000): "морковь",
            range(2001, 10000): "рис",
            range(10001, 25000): "свекла",
            range(25001, 60000): "огурец",
            range(60001, 100000): "фасоль",
            range(100001, 10**50): "помидор",
        }
        self.regexes = {
            "balance": r"💰 Баланс: ([\d,]+/[\d,]+(?:kk)?\s*кр\.)",
            "bottles": r"🍾 Бутылок: (\d+)|🥂 Бутылок: (\d+)",
            "bb_coins": r"🪙 BB-coins: (\d+)|💰 BB-coins: (\d+)",
            "gpoints": r"🍪 GPoints: (\d+)|🧹 GPoints: (\d+)",
            "profit": r"💵 (.+?)(?=\n📅|\n🧍|\Z)",
            "username": r"🙎‍♂️ (.+?)(?=\n|$)",
            "bunker_id": r"🏢 Бункер №(\d+)"
        }
        self.data_file = os.path.join(pathlib.Path.home(), ".hikka", "shadow_ultimat_data.json")
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        self._init_data()

    def _init_data(self):
        """Инициализация JSON-файла с начальными данными"""
        default_data = {
            "greenhouse_active": True,
            "garden_active": False,
            "current_resource": "картошка",
            "warehouse": {
                "potato": 0,
                "carrot": 0,
                "rice": 0,
                "beet": 0,
                "cucumber": 0,
                "bean": 0,
                "tomato": 0,
                "apple": 0,
                "cherry": 0,
                "peach": 0,
                "tangerine": 0
            }
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

    async def _greenhouse(self, client):
        """Автоматический сбор урожая в теплице"""
        while self._get_data("greenhouse_active", True):
            async with client.conversation(self.bot) as conv:
                await asyncio.sleep(2)
                await conv.send_message("Моя теплица")
                try:
                    r = await asyncio.wait_for(conv.get_response(), timeout=5)
                except asyncio.TimeoutError:
                    logger.error("Timeout while fetching greenhouse data")
                    continue

                text = r.raw_text
                green_exp = int("".join(s for s in text.split("Опыт:")[1].split()[0].strip() if s.isdigit()))
                water = int("".join(s for s in text.split("Вода:")[1].split('/')[0].strip() if s.isdigit()))

                resource = next(resource for range_, resource in self._resources_map.items() if green_exp in range_)
                self._set_data("current_resource", resource)

                warehouse = self._get_data("warehouse", {
                    "potato": 0, "carrot": 0, "rice": 0, "beet": 0, "cucumber": 0, "bean": 0, "tomato": 0
                })

                while water > 0:
                    await asyncio.sleep(1.5)
                    await conv.send_message(f"вырастить {resource}")
                    try:
                        r = await asyncio.wait_for(conv.get_response(), timeout=5)
                    except asyncio.TimeoutError:
                        logger.error("Timeout while growing resource")
                        break

                    if "у тебя не хватает" in r.raw_text:
                        break

                    if "успешно вырастил(-а)" in r.raw_text:
                        water -= 1
                        resource_key = {
                            "картошка": "potato",
                            "морковь": "carrot",
                            "рис": "rice",
                            "свекла": "beet",
                            "огурец": "cucumber",
                            "фасоль": "bean",
                            "помидор": "tomato"
                        }.get(resource, "potato")
                        warehouse[resource_key] += 1
                        self._set_data("warehouse", warehouse)

                self.config["experience"] = green_exp
                await asyncio.sleep(5)

        return False

    def extract_profile_data(self, text):
        """Extract profile data from text using regex patterns."""
        data = {}
        for key, pattern in self.regexes.items():
            match = re.search(pattern, text)
            if key in ['bottles', 'bb_coins', 'gpoints']:
                data[key] = match.group(1) if match and match.group(1) else match.group(2) if match else "0"
            else:
                data[key] = match.group(1) if match else "Нет данных"
        return data

    def get_vip_status(self, text, is_premium):
        """Determine VIP status from text."""
        from .ShadowUltimat import ShadowUltimat  # Импорт для доступа к strings
        strings = ShadowUltimat.strings
        if "⭐️⭐️⭐️VIP4⭐️⭐️⭐️" in text:
            return strings["vip4_premium" if is_premium else "vip4"]
        elif "💎💎💎VIP3💎💎💎" in text:
            return strings["vip3_premium" if is_premium else "vip3"]
        elif re.search(r"🔥🔥🔥?VIP2🔥🔥🔥?", text):
            return strings["vip2_premium" if is_premium else "vip2"]
        elif "⚡️VIP1⚡️" in text:
            return strings["vip1_premium" if is_premium else "vip1"]
        return ""

    def get_admin_status(self, text, is_premium):
        """Determine admin status from text."""
        from .ShadowUltimat import ShadowUltimat  # Импорт для доступа к strings
        strings = ShadowUltimat.strings
        if "💻 Тех. Администратор 💻" in text:
            return strings["admin_tech_premium" if is_premium else "admin_tech"]
        elif "😈 Администратор оф.чата 😈" in text:
            return strings["admin_chat_premium" if is_premium else "admin_chat"]
        return ""
