import json
import os
import pathlib
import re
import asyncio
from hikkatl.types import Message

class ShadowUltimatCore:
    def __init__(self, bot, config, strings, lock):
        self.bot = bot
        self.config = config
        self.strings = strings
        self._lock = lock
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
        self._mine_resources_map = {
            "Уголь": "coal",
            "Железо": "iron",
            "Уран": "uranium",
            "Алмаз": "diamond"
        }
        self.regexes = {
            "balance": r"💰\s*Баланс:\s*(?:<b>)?([\d,]+(?:/[,\dkk]+)?)(?:</b>)?\s*кр\.",
            "bottles": r"(?:🍾|🥂)\s*Бутылок:\s*(?:<b>)?(\d+)(?:</b>)?",
            "bb_coins": r"(?:🪙|💰)\s*BB-coins:\s*(?:<b>)?(\d+)(?:</b>)?",
            "gpoints": r"(?:🍪|🧹)\s*GPoints:\s*(?:<b>)?(\d+)(?:</b>)?",
            "profit": r"💵\s*Общая\s*прибыль\s*(?:<b>)?([\d,]+)(?:</b>)?\s*кр\./час",
            "username": r"🙎‍♂️\s*(.+?)(?=\n|$)",
            "bunker_id": r"🏢\s*Бункер\s*№(\d+)"
        }
        self.data_file = os.path.join(pathlib.Path.home(), ".heroku", "shadow_ultimat_data.json")
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        self._init_data()

    def _init_data(self):
        """Инициализация JSON-файла с начальными данными"""
        default_data = {
            "greenhouse_active": True,
            "greenhouse_manual_stop": False,
            "greenhouse_paused": False,
            "mine_active": True,
            "mine_manual_stop": False,
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
            },
            "mine_warehouse": {
                "coal": 0,
                "iron": 0,
                "uranium": 0,
                "diamond": 0
            },
            "message_ids": {}
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
        """Безопасный диалог без обработки флуд-лимитов"""
        async with self._lock:
            try:
                async with client.conversation(self.bot) as conv:
                    await conv.send_message(cmd)
                    response = await asyncio.wait_for(conv.get_response(), timeout=timeout)
                    return response
            except (asyncio.TimeoutError, Exception):
                return None

    async def _greenhouse(self, client):
        """Автофарм теплицы с улучшенной логикой восстановления воды"""
        is_premium = (await client.get_me()).premium
        log_prefix = "<emoji document_id=5449885771420934013>🌱</emoji> " if is_premium else "🌱 "

        while self._get_data("greenhouse_active", True):
            if self._get_data("greenhouse_paused", False):
                await self._pause_event.wait()

            response = await self._safe_conversation(client, "Моя теплица")
            if not response:
                await client.send_message(self._log_channel, f"{log_prefix}🔻 Ошибка при запросе теплицы")
                await asyncio.sleep(5)
                continue

            text = response.raw_text
            green_exp = re.search(r"⭐️\s*Опыт:\s*(?:<b>)?([\d,]+)(?:</b>)?", text)
            water = re.search(r"💧\s*Вода:\s*(?:<b>)?(\d+)/\d+\s*л\.(?:</b>)?", text)
            resource_match = re.search(r"🪴\s*Тебе\s*доступна:\s*.+?\s*(.+?)(?=\n|$)", text)
            warehouse_match = re.search(r"📦\s*Твой\s*склад:([\s\S]*?)(?=\n\n|\Z)", text)

            if not (green_exp and water and resource_match):
                await client.send_message(self._log_channel, f"{log_prefix}🔻 Некорректный ответ от теплицы")
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
                        }.get(item, None)
                        if item_key is not None:
                            warehouse[item_key] = amount

            self._set_data("experience", green_exp)
            self._set_data("water", water)
            self._set_data("current_resource", resource)
            self._set_data("warehouse", warehouse)

            if water == 0:
                self._set_data("greenhouse_active", False)
                await client.send_message(self._log_channel, f"{log_prefix}🔻 Вода закончилась, жду восстановления...")
                await asyncio.sleep(600)  # Ждём 10 минут
                if self._get_data("greenhouse_manual_stop", False):
                    await client.send_message(self._log_channel, f"{log_prefix}🔻 Автофарм теплицы остановлен вручную")
                    break
                water = 1
                self._set_data("water", water)
                self._set_data("greenhouse_active", True)
                await client.send_message(self._log_channel, f"{log_prefix}🔹 Восстановлена 1 капля воды")
                continue

            while water > 0 and self._get_data("greenhouse_active", True):
                command_resource = self._command_map.get(resource, "картошка")
                command = f"вырастить {command_resource}"
                response = await self._safe_conversation(client, command)
                if not response:
                    await client.send_message(self._log_channel, f"{log_prefix}🔻 Ошибка при выращивании {resource}")
                    await asyncio.sleep(1.5)
                    continue

                if "успешно вырастил(-а)" in response.raw_text:
                    water -= 1
                    warehouse[resource_key] += 1
                    self._set_data("warehouse", warehouse)
                    self._set_data("water", water)
                    await client.send_message(self._log_channel, f"{log_prefix}🔹 Успешно выращено {resource}!")
                    # Запускаем задачу для ожидания восстановления воды
                    asyncio.create_task(self._report_water_restore(client))
                elif "у тебя не хватает" in response.raw_text:
                    self._set_data("greenhouse_active", False)
                    await client.send_message(self._log_channel, f"{log_prefix}🔻 Недостаточно ресурсов, жду восстановления...")
                    await asyncio.sleep(600)
                    if self._get_data("greenhouse_manual_stop", False):
                        await client.send_message(self._log_channel, f"{log_prefix}🔻 Автофарм теплицы остановлен вручную")
                        break
                    water = 1
                    self._set_data("water", water)
                    self._set_data("greenhouse_active", True)
                    await client.send_message(self._log_channel, f"{log_prefix}🔹 Восстановлена 1 капля воды")
                    break
                elif "VIP" in response.raw_text:
                    self._set_data("greenhouse_active", False)
                    await client.send_message(self._log_channel, f"{log_prefix}🔻 Требуется VIP-статус для теплицы")
                    break
                else:
                    await client.send_message(self._log_channel, f"{log_prefix}🔻 Неизвестный ответ при выращивании: {response.raw_text}")
                    await asyncio.sleep(1.5)
                    continue

                await asyncio.sleep(1.5)

            await asyncio.sleep(self.config["greenhouse_interval"])

        return False

    async def _report_water_restore(self, client):
        """Отправляет отчёт о восстановлении воды через 10 минут"""
        is_premium = (await client.get_me()).premium
        log_prefix = "<emoji document_id=5449885771420934013>🌱</emoji> " if is_premium else "🌱 "
        await asyncio.sleep(600)  # Ждём 10 минут
        if self._get_data("greenhouse_active", True):
            await client.send_message(self._log_channel, f"{log_prefix}🔹 За 10 минут восстановится 1 капля воды")

    async def _mine(self, client):
        """Автофарм шахты"""
        is_premium = (await client.get_me()).premium
        log_prefix = "<emoji document_id=5413478709875450870>⛏</emoji> " if is_premium else "⛏ "

        while self._get_data("mine_active", True):
            async with self._lock:
                response = await self._safe_conversation(client, "копать")
                if not response:
                    await client.send_message(self._log_channel, f"{log_prefix}🔻 Ошибка при выполнении команды 'копать'")
                    await asyncio.sleep(5)
                    continue

                if "у тебя нет кирки" in response.raw_text:
                    await asyncio.sleep(1.5)
                    response = await self._safe_conversation(client, "Б")
                    if not response:
                        await client.send_message(self._log_channel, f"{log_prefix}🔻 Ошибка при проверке баланса")
                        await asyncio.sleep(5)
                        continue

                    balance = int("".join(s for s in response.raw_text.split("Баланс:")[1].split('/')[0].strip() if s.isdigit()))
                    if balance < 30000:
                        await client.send_message(self._log_channel, f"{log_prefix}🔻 Недостаточно крышек для покупки кирки")
                        await asyncio.sleep(self.config["mine_interval"])
                        continue

                    await asyncio.sleep(1.5)
                    if balance >= 1000000:
                        await self._safe_conversation(client, "Купить алмазную кирку")
                    elif balance >= 200000:
                        await self._safe_conversation(client, "Купить железную кирку")
                    else:
                        await self._safe_conversation(client, "Купить каменную кирку")
                        await asyncio.sleep(self.config["mine_interval"])
                        continue

                    response = await self._safe_conversation(client, "копать")
                    if not response:
                        await client.send_message(self._log_channel, f"{log_prefix}🔻 Ошибка при повторной команде 'копать'")
                        await asyncio.sleep(5)
                        continue

                if 'отдохнёт' in response.raw_text:
                    await client.send_message(self._log_channel, f"{log_prefix}🔻 Кирка отдыхает")
                    await asyncio.sleep(self.config["mine_interval"])
                    continue

                resources_result = response.raw_text.split("ты нашёл")
                if len(resources_result) > 1:
                    resources_text = resources_result[1].split(' ')[1:]
                    resources = ' '.join(resources_text).split('.')[0]
                else:
                    resources = 'Воздух'

                probability_result = response.raw_text.split("вероятностью")
                if len(probability_result) > 1:
                    probability_text = probability_result[1]
                    probability = int("".join(s for s in probability_text.split('%')[0].strip() if s.isdigit()))
                else:
                    probability = 0

                mine_warehouse = self._get_data("mine_warehouse", {
                    "coal": 0, "iron": 0, "uranium": 0, "diamond": 0
                })

                if self.config.get("MineDiamond", False):
                    if "ты нашёл 💎 Алмаз." in response.message or probability == 100:
                        await asyncio.sleep(1.5)
                        await response.click(0)
                        response = await self._safe_conversation(client, response.message_id, timeout=5)
                        if response and "Прочность твоей кирки уменьшена" in response.text:
                            await client.send_message(self._log_channel, f"{log_prefix}🔻 Прочность кирки уменьшена")
                        else:
                            resource_key = self._mine_resources_map.get(resources, None)
                            if resource_key:
                                mine_warehouse[resource_key] += 1
                                self._set_data("mine_warehouse", mine_warehouse)
                            await client.send_message(self._log_channel, f"{log_prefix}🔹 Ты добыл {resources} с шансом {probability}%")
                    else:
                        if self.config.get("SkipNonUranium", True) and "Уран" not in resources:
                            await asyncio.sleep(1.5)
                            await response.click(1)
                            await client.send_message(self._log_channel, f"{log_prefix}🔸 Ты пропустил {resources} с шансом {probability}%")
                        else:
                            await asyncio.sleep(1.5)
                            await response.click(0)
                            resource_key = self._mine_resources_map.get(resources, None)
                            if resource_key:
                                mine_warehouse[resource_key] += 1
                                self._set_data("mine_warehouse", mine_warehouse)
                            await client.send_message(self._log_channel, f"{log_prefix}🔹 Ты добыл {resources} с шансом {probability}%")
                else:
                    await asyncio.sleep(1.5)
                    await response.click(0)
                    response = await self._safe_conversation(client, response.message_id, timeout=5)
                    if response and "Прочность твоей кирки уменьшена" in response.text:
                        await client.send_message(self._log_channel, f"{log_prefix}🔻 Прочность кирки уменьшена")
                    else:
                        resource_key = self._mine_resources_map.get(resources, None)
                        if resource_key:
                            mine_warehouse[resource_key] += 1
                            self._set_data("mine_warehouse", mine_warehouse)
                        if self.config.get("SkipNonUranium", True) and "Уран" not in resources:
                            await client.send_message(self._log_channel, f"{log_prefix}🔸 Ты пропустил {resources} с шансом {probability}%")
                        else:
                            await client.send_message(self._log_channel, f"{log_prefix}🔹 Ты добыл {resources} с шансом {probability}%")
                    await asyncio.sleep(self.config["mine_interval"])
                    continue

                if self.config.get("MineProbability", False):
                    if 80 <= probability <= 100:
                        await asyncio.sleep(1.5)
                        await response.click(0)
                        response = await self._safe_conversation(client, response.message_id, timeout=5)
                        if response and "Прочность твоей кирки уменьшена" in response.text:
                            await client.send_message(self._log_channel, f"{log_prefix}🔻 Прочность кирки уменьшена")
                        else:
                            resource_key = self._mine_resources_map.get(resources, None)
                            if resource_key:
                                mine_warehouse[resource_key] += 1
                                self._set_data("mine_warehouse", mine_warehouse)
                            await client.send_message(self._log_channel, f"{log_prefix}🔹 Ты добыл {resources} с шансом {probability}%")
                    else:
                        await asyncio.sleep(1.5)
                        await response.click(1)
                        await client.send_message(self._log_channel, f"{log_prefix}🔸 Ты пропустил {resources} с шансом {probability}%")
                else:
                    await asyncio.sleep(1.5)
                    await response.click(0)
                    response = await self._safe_conversation(client, response.message_id, timeout=5)
                    if response and "Прочность твоей кирки уменьшена" in response.text:
                        await client.send_message(self._log_channel, f"{log_prefix}🔻 Прочность кирки уменьшена")
                    else:
                        resource_key = self._mine_resources_map.get(resources, None)
                        if resource_key:
                            mine_warehouse[resource_key] += 1
                            self._set_data("mine_warehouse", mine_warehouse)
                        await client.send_message(self._log_channel, f"{log_prefix}🔹 Ты добыл {resources} с шансом {probability}%")

                await asyncio.sleep(self.config["mine_interval"])

        return False

    def extract_profile_data(self, text):
        """Извлечение данных профиля"""
        def convert_balance(match):
            balance = match.group(1)
            parts = balance.split('/')
            result = []

            for part in parts:
                k_match = re.search(r'(\d+[,\d]*)(k+)', part, re.IGNORECASE)
                if k_match:
                    num_str = k_match.group(1).replace(',', '.')
                    k_count = len(k_match.group(2))
                    try:
                        num = float(num_str) * (10 ** (3 * k_count))
                        formatted_num = f"{int(num):,}".replace(',', ' ')
                    except ValueError:
                        formatted_num = part
                else:
                    formatted_num = part.replace(',', ' ')
                result.append(formatted_num)

            return '/'.join(result)

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
                if key == "balance":
                    data[key] = convert_balance(match)
                else:
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
        admin_status = ""
        if "💻 Тех. Администратор 💻" in text:
            admin_status += self.strings["admin_tech_premium" if is_premium else "admin_tech"]
        if "😈 Администратор оф.чата 😈" in text:
            admin_status += self.strings["admin_chat_premium" if is_premium else "admin_chat"]
        return admin_status
