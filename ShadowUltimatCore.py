import json
import os
import pathlib
import re
import asyncio
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class ShadowUltimatCore:
    def __init__(self, bot, config, strings):
        self.bot = bot
        self.config = config
        self.strings = strings  # Получаем strings из ShadowUltimat
        self._pause_event = asyncio.Event()  # Событие для паузы автофарма
        self._pause_event.set()  # Изначально автофарм не приостановлен
        self._resources_map = {
            range(0, 501): "картошка",
            range(501, 2001): "морковь",
            range(2001, 10001): "рис",
            range(10001, 25001): "свекла",
            range(25001, 60001): "огурец",
            range(60001, 100001): "фасоль",
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
            "greenhouse_manual_stop": False,  # Флаг ручного выключения
            "greenhouse_paused": False,  # Флаг паузы для команд
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

    async def _greenhouse(self, client):
        """Автофарм теплицы с ожиданием воды и автоматическим включением"""
        while self._get_data("greenhouse_active", True):
            # Проверяем, приостановлен ли автофарм
            if self._get_data("greenhouse_paused", False):
                logger.debug("Автофарм приостановлен, ожидаем возобновления")
                await self._pause_event.wait()

            async with client.conversation(self.bot) as conv:
                # Проверяем состояние теплицы
                await conv.send_message("Моя теплица")
                try:
                    response = await asyncio.wait_for(conv.get_response(), timeout=5)
                except asyncio.TimeoutError:
                    logger.error("Таймаут при получении данных теплицы")
                    continue
                except Exception as e:
                    logger.error(f"Ошибка при получении ответа теплицы: {e}")
                    continue

                text = response.raw_text
                # Парсим данные: опыт, вода, доступная культура, склад
                green_exp = re.search(r"Опыт: (\d+)", text)  # Опыт теплицы
                water = re.search(r"Вода: (\d+)/\d+ л\.", text)  # Текущая вода
                resource_match = re.search(r"🪴 Тебе доступна: (.+?)(?=\n|$)", text)  # Доступная культура
                warehouse_match = re.search(r"📦 Твой склад:([\s\S]*?)(?=\n\n|\Z)", text)  # Склад

                if not (green_exp and water and resource_match):
                    logger.error(f"Не удалось разобрать данные теплицы: {text}")
                    continue

                green_exp = int(green_exp.group(1))
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

                # Проверка соответствия культуры опыту
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

                # Парсинг склада
                if warehouse_match:
                    warehouse_lines = warehouse_match.group(1).strip().split("\n")
                    for line in warehouse_lines:
                        match = re.match(r"\s*(.+?) - (\d+) шт\.", line)
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

                # Обновляем JSON
                self._set_data("experience", green_exp)
                self._set_data("water", water)
                self._set_data("current_resource", resource)
                self._set_data("warehouse", warehouse)

                # Если воды 0, ждём 10 минут и проверяем ручное выключение
                if water == 0:
                    logger.info("Вода закончилась, ожидание 10 минут для накопления 1 капли")
                    self._set_data("greenhouse_active", False)  # Временно отключаем
                    await asyncio.sleep(600)  # 10 минут = 600 секунд
                    if self._get_data("greenhouse_manual_stop", False):
                        logger.info("Автофарм остаётся выключенным из-за ручного управления")
                        break
                    water += 1  # Предполагаем, что 1 капля накопилась
                    self._set_data("water", water)
                    self._set_data("greenhouse_active", True)  # Автоматически включаем
                    logger.info(f"Вода обновлена: {water}, автофарм возобновлён")
                    continue

                # Выращиваем культуру (без эмодзи)
                await asyncio.sleep(1.5)
                await conv.send_message(f"вырастить {resource}")
                try:
                    response = await asyncio.wait_for(conv.get_response(), timeout=5)
                except asyncio.TimeoutError:
                    logger.error("Таймаут при выращивании культуры")
                    continue
                except Exception as e:
                    logger.error(f"Ошибка при выращивании культуры: {e}")
                    continue

                if "успешно вырастил(-а)" in response.raw_text:
                    water -= 1
                    warehouse[resource_key] += 1
                    self._set_data("warehouse", warehouse)
                    self._set_data("water", water)
                    logger.info(f"Выращена {resource}, вода: {water}, склад: {warehouse[resource_key]}")
                elif "у тебя не хватает" in response.raw_text:
                    logger.info("Недостаточно воды или ресурсов, ожидание 10 минут для накопления 1 капли")
                    self._set_data("greenhouse_active", False)  # Временно отключаем
                    await asyncio.sleep(600)  # 10 минут = 600 секунд
                    if self._get_data("greenhouse_manual_stop", False):
                        logger.info("Автофарм остаётся выключенным из-за ручного управления")
                        break
                    water += 1  # Предполагаем, что 1 капля накопилась
                    self._set_data("water", water)
                    self._set_data("greenhouse_active", True)  # Автоматически включаем
                    logger.info(f"Вода обновлена: {water}, автофарм возобновлён")
                    continue

                await asyncio.sleep(2)  # Задержка между циклами

        return False

    def extract_profile_data(self, text):
        """Извлечение данных профиля"""
        data = {}
        for key, pattern in self.regexes.items():
            match = re.search(pattern, text)
            if key in ['bottles', 'bb_coins', 'gpoints']:
                data[key] = match.group(1) if match and match.group(1) else match.group(2) if match else "0"
            else:
                data[key] = match.group(1) if match else "Нет данных"
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
