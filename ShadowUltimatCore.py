import json
import os
import pathlib
import re
import asyncio
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class ShadowUltimatCore:
    def __init__(self, bot, config, strings, lock):
        self.bot = bot
        self.config = config
        self.strings = strings
        self._lock = lock  # Глобальная блокировка для диалогов
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._resources_map = {
            range(0, 500): "картошка",
            range(501, 2000): "морковь",
            range(2001, 10000): "рис",
            range(10001, 25000): "свекла",
            range(25001, 60000): "огурец",
            range(60001, 100000): "фасоль",
            range(100001, 10**50): "помидор",
        }
        self._command_map = {
            "картошка": "картошка",
            "морковь": "морковь",
            "рис": "рис",
            "свекла": "свекла",
            "огурец": "огурец",
            "фасоль": "фасоль",
            "помидор": "помидор",
        }
        self.regexes = {
            "balance": r"💰\s*Баланс:\s*([\d,]+/[\d,]+)\s*кр\.",
            "bottles": r"(?:🍾|🥂)\s*Бутылок:\s*(\d+)",
            "bb_coins": r"(?:🪙|💰)\s*BB-coins:\s*(\d+)",
            "gpoints": r"(?:🍪|🧹)\s*GPoints:\s*(\d+)",
            "profit": r"💵\s*Общая\s*прибыль\s*([\d,]+)\s*кр\./час",
            "username": r"🙎‍♂️\s*(.+?)(?=\n|$)",
            "bunker_id": r"🏢\s*Бункер\s*№(\d+)"
        }
        self.data_file = os.path.join(pathlib.Path.home(), ".hikka", "shadow_ultimat_data.json")
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        self._init_data()

    def _init_data(self):
        """Инициализация JSON-файла с начальными данными"""
        default_data = {
            "greenhouse_active": True,
            "greenhouse_manual_stop": False,
            "greenhouse_paused": False,
            "experience": 0,
            "water": 0,
            "current_resource": "картошка",
            "warehouse": {
                "potato": 0,
                "carrot": 0,
                "rice": 0,
                "beet": 0,
                "cucumber": 0,
                "bean": 0,
                "tomato": 0
            }
        }
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4)

    def _load_data(self):
        """Загрузка данных из JSON"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._init_data()
            return self._load_data()

    def _save_data(self, data):
        """Сохранение данных в JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def _get_data(self, key, default):
        """Получение значения из JSON"""
        data = self._load_data()
        return data.get(key, default)

    def _set_data(self, key, value):
        """Установка значения в JSON"""
        data = self._load_data()
        data[key] = value
        self._save_data(data)

    async def _safe_conversation(self, client, cmd, timeout=5):
        """Безопасный диалог без обработки флуд-вейта"""
        async with self._lock:
            try:
                async with client.conversation(self.bot) as conv:
                    logger.debug(f"Отправка команды: {cmd}")
                    await conv.send_message(cmd)
                    response = await asyncio.wait_for(conv.get_response(), timeout=timeout)
                    logger.debug(f"Ответ на '{cmd}': {response.raw_text}")
                    return response
            except asyncio.TimeoutError:
                logger.error(f"Таймаут при выполнении команды {cmd}")
                return None
            except Exception as e:
                logger.error(f"Ошибка при выполнении команды {cmd}: {e}")
                return None

    async def _greenhouse(self, client):
        """Автофарм теплицы с задержкой 1.5 сек между командами 'вырастить'"""
        while self._get_data("greenhouse_active", True):
            if self._get_data("greenhouse_paused", False):
                logger.debug("Автофарм приостановлен, ожидаем возобновления")
                await self._pause_event.wait()

            response = await self._safe_conversation(client, "Моя теплица")
            if not response:
                logger.warning("Нет ответа на 'Моя теплица', повтор через 5 сек")
                await asyncio.sleep(5)
                continue

            text = response.raw_text
            green_exp = re.search(r"⭐️\s*Опыт:\s*([\d,]+)", text)
            water = re.search(r"💧\s*Вода:\s*(\d+)/\d+\s*л\.", text)
            resource_match = re.search(r"🪴\s*Тебе\s*доступна:\s*.+?\s*(.+?)(?=\n|$)", text)
            warehouse_match = re.search(r"📦\s*Твой\s*склад:([\s\S]*?)(?=\n\n|\Z)", text)

            if not (green_exp and water and resource_match):
                logger.error(f"Не удалось разобрать данные теплицы: {text}")
                await asyncio.sleep(5)
                continue

            green_exp = int(green_exp.group(1).replace(",", ""))
            water = int(water.group(1))
            resource = resource_match.group(1).strip()
            resource_key = {
                "🥔 Картошка": "potato",
                "🥕 Морковь": "carrot",
                "🍚 Рис": "rice",
                "🍠 Свекла": "beet",
                "🥒 Огурец": "cucumber",
                "🫘 Фасоль": "bean",
                "🍅 Помидор": "tomato"
            }.get(resource, "potato")

            for exp_range, res in self._resources_map.items():
                if green_exp in exp_range:
                    resource = res
                    resource_key = {
                        "картошка": "potato",
                        "морковь": "carrot",
                        "рис": "rice",
                        "свекла": "beet",
                        "огурец": "cucumber",
                        "фасоль": "bean",
                        "помидор": "tomato"
                    }.get(resource, "potato")
                    break

            warehouse = self._get_data("warehouse", {
                "potato": 0,
                "carrot": 0,
                "rice": 0,
                "beet": 0,
                "cucumber": 0,
                "bean": 0,
                "tomato": 0
            })

            if warehouse_match:
                warehouse_lines = warehouse_match.group(1).strip().split("\n")
                for line in warehouse_lines:
                    match = re.match(r"\s*(.+?)\s*-\s*(\d+)\s*шт\.", line)
                    if match:
                        item = match.group(1).strip()
                        amount = int(match.group(2))
                        item_key = {
                            "🥔 Картошка": "potato",
                            "🥕 Морковь": "carrot",
                            "🍚 Рис": "rice",
                            "🍠 Свекла": "beet",
                            "🥒 Огурец": "cucumber",
                            "🫘 Фасоль": "bean",
                            "🍅 Помидор": "tomato"
                        }.get(item)
                        if item_key:
                            warehouse[item_key] = amount

            self._set_data("experience", green_exp)
            self._set_data("water", water)
            self._set_data("current_resource", resource)
            self._set_data("warehouse", warehouse)

            if water == 0:
                logger.info("Вода закончилась, ожидание 10 минут")
                self._set_data("greenhouse_active", False)
                await asyncio.sleep(600)
                if self._get_data("greenhouse_manual_stop", False):
                    logger.info("Автофарм остаётся выключенным из-за ручного управления")
                    break
                water += 1
                self._set_data("water", water)
                self._set_data("greenhouse_active", True)
                logger.info(f"Вода обновлена: {water}, автофарм возобновлён")
                continue

            while water > 0 and self._get_data("greenhouse_active", True):
                command_resource = self._command_map.get(resource, "картошка")
                command = f"вырастить {command_resource}"
                response = await self._safe_conversation(client, command)
                if not response:
                    logger.warning(f"Нет ответа на '{command}', повтор через 1.5 сек")
                    await asyncio.sleep(1.5)
                    continue

                if "успешно вырастил(-а)" in response.raw_text:
                    water -= 1
                    warehouse[resource_key] += 1
                    self._set_data("warehouse", warehouse)
                    self._set_data("water", water)
                    logger.info(f"Выращена {resource}, вода: {water}, склад: {warehouse[resource_key]}")
                elif "у тебя не хватает" in response.raw_text:
                    logger.info("Недостаточно воды, ожидание 10 минут")
                    self._set_data("greenhouse_active", False)
                    await asyncio.sleep(600)
                    if self._get_data("greenhouse_manual_stop", False):
                        logger.info("Автофарм остаётся выключенным из-за ручного управления")
                        break
                    water += 1
                    self._set_data("water", water)
                    self._set_data("greenhouse_active", True)
                    logger.info(f"Вода обновлена: {water}, автофарм возобновлён")
                    break
                elif "VIP" in response.raw_text:
                    logger.error(f"Требуется VIP-статус для выращивания: {response.raw_text}")
                    self._set_data("greenhouse_active", False)
                    break
                else:
                    logger.warning(f"Неожиданный ответ на '{command}': {response.raw_text}")
                    await asyncio.sleep(1.5)
                    continue

                await asyncio.sleep(1.5)

            await asyncio.sleep(5)

        return False

    def extract_profile_data(self, text):
        """Извлечение данных профиля"""
        data = {
            "balance": "0/0 кр.",
            "bottles": "0",
            "bb_coins": "0",
            "gpoints": "0",
            "profit": "0 кр./час",
            "username": "Неизвестно",
            "bunker_id": "0"
        }
        for key, pattern in self.regexes.items():
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                data[key] = match.group(1)
                logger.debug(f"Извлечено {key}: {data[key]}")
            else:
                logger.warning(f"Не удалось извлечь {key} из текста: {text}")
        return data

    def get_vip_status(self, text, is_premium):
        """Определение VIP-статуса"""
        if "⭐️⭐️⭐️VIP4⭐️⭐️⭐️" in text:
            return self.strings["vip4_premium" if is_premium else "vip4"]
        elif "💎💎💎VIP3💎💎💎" in text:
            return self.strings["vip3_premium" if is_premium else "vip3"]
        elif re.search(r"🔥🔥🔥?VIP2🔥🔥🔥?", text):
            return self.strings["vip2_premium" if is_premium else "vip2"]
        elif "⚡️VIP1⚡️" in text:
            return self.strings["vip1_premium" if is_premium else "vip1"]
        return ""

    def get_admin_status(self, text, is_premium):
        """Определение статуса админа"""
        if "💻 Тех. Администратор 💻" in text:
            return self.strings["admin_tech_premium" if is_premium else "admin_tech"]
        elif "😈 Администратор оф.чата 😈" in text:
            return self.strings["admin_chat_premium" if is_premium else "admin_chat"]
        return ""    logger.warning(f"Неожиданный ответ на '{command}': {response.raw_text}")
                    await asyncio.sleep(1.5)
                    continue

                await asyncio.sleep(1.5)

            await asyncio.sleep(5)

        return False

    def extract_profile_data(self, text):
        """Извлечение данных профиля"""
        data = {
            "balance": "0/0 кр.",
            "bottles": "0",
            "bb_coins": "0",
            "gpoints": "0",
            "profit": "0 кр./час",
            "username": "Неизвестно",
            "bunker_id": "0"
        }
        for key, pattern in self.regexes.items():
            match = re.search(pattern, text)
            if match:
                data[key] = match.group(1)
        return data

    def get_vip_status(self, text, is_premium):
        """Определение VIP-статуса"""
        if "⭐️⭐️⭐️VIP4⭐️⭐️⭐️" in text:
            return self.strings["vip4_premium" if is_premium else "vip4"]
        elif "💎💎💎VIP3💎💎💎" in text:
            return self.strings["vip3_premium" if is_premium else "vip3"]
        elif re.search(r"🔥🔥🔥?VIP2🔥🔥🔥?", text):
            return self.strings["vip2_premium" if is_premium else "vip2"]
        elif "⚡️VIP1⚡️" in text:
            return self.strings["vip1_premium" if is_premium else "vip1"]
        return ""

    def get_admin_status(self, text, is_premium):
        """Определение статуса админа"""
        if "💻 Тех. Администратор 💻" in text:
            return self.strings["admin_tech_premium" if is_premium else "admin_tech"]
        elif "😈 Администратор оф.чата 😈" in text:
            return self.strings["admin_chat_premium" if is_premium else "admin_chat"]
        return ""
