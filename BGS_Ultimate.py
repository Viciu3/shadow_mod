__version__ = (8, 1, 2)
# meta developer: @Shadow_red1, @dream23041
# change-log: Добавлена проверка обновлений через GitHub

from .. import loader, utils
import asyncio
import random
import aiohttp
import io
import inspect
from telethon.tl.types import Message

class BGS_Ultimate(loader.Module):
    """🚀 Полный автомат для BGS бота с рефералами, казино и гонками"""
    
    strings = {
        "name": "BGS Ultimate",
        "start_info": """
🎮 <b>BGS Bot Control Panel</b>

<u>Основные команды:</u>
<code>.bgs start</code> - автопостинг видео
<code>.bgs work</code> - авторабота
<code>.bgs bonus</code> - ежедневный бонус
<code>.bgs stop</code> - остановка всех процессов
<code>.bgs update</code> - проверка обновлений

<u>Новые функции:</u>
<code>.bgs ref</code> - реферальная система
<code>.bgs casino [ставка]</code> - игра в казино
<code>.bgs race [ставка]</code> - участие в гонках
<code>.bgs hate [@user]</code> - отправка хейтеров

<u>Статистика:</u>
<code>.bgs profile</code> - полный профиль
<code>.bgs balance</code> - баланс и статистика
""",
        "work_started": "🔄 Авто-работа запущена",
        "work_stopped": "⏹ Авто-работа остановлена",
        "video_started": "🎥 Автопостинг видео запущен (тип: {})",
        "video_stopped": "⏹ Автопостинг остановлен",
        "casino_win": "🎉 Выигрыш: {}💰 (x{})",
        "casino_lose": "💸 Проигрыш: {}💰",
        "ref_info": "📊 Рефералов: {}\n💰 Заработано: {}",
        "error": "❌ Ошибка: {}",
        "fetch_failed": "❌ Не удалось получить данные с GitHub",
        "actual_version": "✅ У вас актуальная версия: {version}",
        "old_version": "🔔 Доступна новая версия!\nТекущая версия: {version}\nНовая версия: {new_version}\n",
        "update_whats_new": "📝 Что нового: {whats_new}\n",
        "update_command": "🔄 Для обновления используйте: <code>{update_command}</code>"
    }

    def __init__(self):
        self._bot = "@bgs2_bot"
        self._running = False
        self._work_loop = False
        self._video_loop = False
        self._bonus_loop = False
        self._current_conv = None
        self._ref_link = None
        self._ref_count = 0

        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "button_index",
                0,
                "Тип видео: 0-Игры 1-Эдит 2-Фильмы 3-Реакции 4-Нарезки 5-Мемы",
                validator=loader.validators.Integer(minimum=0, maximum=5)
            ),
            loader.ConfigValue(
                "hire_editor",
                1,
                "Уровень монтажера (0-9)",
                validator=loader.validators.Integer(minimum=0, maximum=9)
            ),
            loader.ConfigValue(
                "buy_computer",
                1,
                "Уровень компьютера (0-4)",
                validator=loader.validators.Integer(minimum=0, maximum=4)
            ),
            loader.ConfigValue(
                "subscribe_plan",
                1,
                "Тарифный план (0-6)",
                validator=loader.validators.Integer(minimum=0, maximum=6)
            ),
            loader.ConfigValue(
                "message_value",
                1000,
                "Бюджет на видео (1-30000)",
                validator=loader.validators.Integer(minimum=1, maximum=30000)
            ),
            loader.ConfigValue(
                "repeat_count",
                30,
                "Минут на монтаж (1-120)",
                validator=loader.validators.Integer(minimum=1, maximum=120)
            ),
            loader.ConfigValue(
                "auto_work_enabled",
                True,
                "Автоматическая работа",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "buy_adrenaline",
                1,
                "Количество адреналина",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "buy_coffee",
                1,
                "Количество кофе",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "daily_bonus_enabled",
                True,
                "Ежедневный бонус",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "auto_ref",
                True,
                "Авто-реферальная система",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "casino_strategy",
                "conservative",
                "Стратегия казино: conservative/aggressive",
                validator=loader.validators.Choice(["conservative", "aggressive"])
            ),
            loader.ConfigValue(
                "race_bet",
                5000,
                "Стандартная ставка на гонки",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "max_hate",
                10,
                "Макс. хейтеров за раз",
                validator=loader.validators.Integer(minimum=1, maximum=100)
            )
        )

    async def client_ready(self, client, db):
        self._client = client
        if self.config["auto_ref"]:
            async with self._client.conversation(self._bot, exclusive=False) as conv:
                await conv.send_message("Мои рефералы")
                response = await conv.get_response()
                if "Реферальная ссылка:" in response.text:
                    self._ref_link = response.text.split("Реферальная ссылка:")[1].strip()
                    self._ref_count = int(response.text.split("Рефералов:")[1].split()[0])

    async def _safe_send(self, conv, text, delay=2):
        try:
            await conv.send_message(text)
            await asyncio.sleep(delay)
            return True
        except Exception as e:
            print(f"[BGS] Ошибка отправки: {e}")
            return False

    async def _edit_or_reply(self, message: Message, text: str):
        try:
            await message.edit(text)
        except:
            await message.reply(text)

    async def bgsupdatecmd(self, message: Message):
        """Проверка обновлений модуля BGS Ultimate"""
        module_name = "BGS_Ultimate"
        module = self.lookup(module_name)
        if not module:
            await self._edit_or_reply(message, self.strings["error"].format("Модуль не найден"))
            return

        sys_module = inspect.getmodule(module)
        local_file = io.BytesIO(sys_module.__loader__.data)
        local_file.name = f"{module_name}.py"
        local_file.seek(0)
        local_first_line = local_file.readline().strip().decode("utf-8")

        correct_version = sys_module.__version__
        correct_version_str = ".".join(map(str, correct_version))

        async with aiohttp.ClientSession() as session:
            async with session.get("https://raw.githubusercontent.com/Viciu3/shadow_mod/refs/heads/main/BGS_Ultimate.py") as response:
                if response.status == 200:
                    remote_content = await response.text()
                    remote_lines = remote_content.splitlines()
                    new_version = remote_lines[0].split("=", 1)[1].strip().strip("() Gandalf").replace(",", "").replace(" ", ".")
                    what_new = remote_lines[2].split(":", 1)[1].strip() if len(remote_lines) > 2 and remote_lines[2].startswith("# change-log:") else ""
                else:
                    await self._edit_or_reply(message, self.strings["fetch_failed"])
                    return

        if local_first_line.replace(" ", "") == remote_lines[0].strip().replace(" ", ""):
            await self._edit_or_reply(message, self.strings["actual_version"].format(version=correct_version_str))
        else:
            update_message = self.strings["old_version"].format(version=correct_version_str, new_version=new_version)
            if what_new:
                update_message += self.strings["update_whats_new"].format(whats_new=what_new)
            update_message += self.strings["update_command"].format facility: .format(update_command=f"{self.get_prefix()}dlm https://raw.githubusercontent.com/Viciu3/shadow_mod/refs/heads/main/BGS_Ultimate.py")
            await self._edit_or_reply(message, update_message)

    async def bgscmd(self, message: Message):
        """главное меню управления BGS ботом"""
        args = utils.get_args_raw(message)
        
        if not args:
            await self._edit_or_reply(message, self.strings["start_info"])
            return

        if args == "start":
            await self._start_video(message)
        elif args == "work":
            await self._start_work(message)
        elif args == "stop":
            await self._stop_all(message)
        elif args == "ref":
            await self._show_ref(message)
        elif args.startswith("casino"):
            await self._play_casino(message)
        elif args.startswith("race"):
            await self._start_race(message)
        elif args.startswith("hate"):
            await self._send_hate(message)
        elif args == "profile":
            await self._show_profile(message)
        elif args == "balance":
            await self._show_balance(message)
        elif args == "bonus":
            await self._get_bonus(message)
        elif args == "update":
            await self.bgsupdatecmd(message)

    async def _start_video(self, message: Message):
        if self._video_loop:
            await self._edit_or_reply(message, "⚠️ Автопостинг уже запущен")
            return

        self._video_loop = True
        button_names = ["Игры", "Эдит", "Фильмы", "Реакции", "Нарезки", "Мемы"]
        
        try:
            async with self._client.conversation(self._bot, exclusive=False) as conv:
                self._current_conv = conv
                
                await self._edit_or_reply(
                    message,
                    self.strings["video_started"].format(button_names[self.config["button_index"]])
                )

                while self._video_loop:
                    if self.config["hire_editor"] > 0:
                        if not await self._safe_send(conv, f"Нанять монтажера {self.config['hire_editor']}", 3):
                            break
                    
                    if self.config["subscribe_plan"] > 0:
                        if not await self._safe_send(conv, f"Оформить тариф {self.config['subscribe_plan']}", 3):
                            break
                    
                    if self.config["buy_computer"] > 0:
                        if not await self._safe_send(conv, f"Купить компьютер {self.config['buy_computer']}", 3):
                            break

                    if not await self._safe_send(conv, "Опубликовать видео", 3):
                        break
                        
                    try:
                        response = await conv.get_response()
                        await response.click(self.config["button_index"])
                    except Exception as e:
                        await self._edit_or_reply(message, f"❌ Ошибка клика: {e}")
                        break

                    if not await self._safe_send(conv, str(self.config["message_value"]), 3):
                        break
                        
                    for _ in range(3):
                        if not await self._safe_send(conv, str(self.config["repeat_count"]), 3):
                            break

                    await asyncio.sleep(420)

        except Exception as e:
            await self._edit_or_reply(message, self.strings["error"].format(str(e)))
        finally:
            self._video_loop = False
            if self._current_conv:
                await self._current_conv.cancel()
            self._current_conv = None
            await self._edit_or_reply(message, self.strings["video_stopped"])

    async def _start_work(self, message: Message):
        if not self.config["auto_work_enabled"]:
            await self._edit_or_reply(message, "🚫 Авто-работа отключена в настройках")
            return

        if self._work_loop:
            await self._edit_or_reply(message, "⚠️ Авто-работа уже запущена")
            return

        self._work_loop = True
        await self._edit_or_reply(message, self.strings["work_started"])

        try:
            async with self._client.conversation(self._bot, exclusive=False) as conv:
                self._current_conv = conv
                
                if self.config["buy_coffee"] > 0:
                    if not await self._safe_send(conv, f"Купить кофе {self.config['buy_coffee']}"):
                        return
                
                if self.config["buy_adrenaline"] > 0:
                    if not await self._safe_send(conv, f"Купить адреналин {self.config['buy_adrenaline']}"):
                        return

                if not await self._safe_send(conv, "Пойти на работу"):
                    return
                
                await conv.get_response()

                while self._work_loop:
                    if not await self._safe_send(conv, "Моя работа"):
                        break
                    
                    response = await conv.get_response()
                    work_info = response.raw_text

                    if "😴Усталость:" in work_info:
                        try:
                            fatigue = int(work_info.split("😴Усталость:")[1].split("%")[0].strip())
                            if fatigue >= 80:
                                await self._edit_or_reply(message, f"😴 Усталость {fatigue}%, прекращаю работу")
                                await response.click(0)
                                break
                        except:
                            pass

                    await asyncio.sleep(300)

        except Exception as e:
            await self._edit_or_reply(message, self.strings["error"].format(str(e)))
        finally:
            self._work_loop = False
            if self._current_conv:
                await self._current_conv.cancel()
            self._current_conv = None
            await self._edit_or_reply(message, self.strings["work_stopped"])

    async def _stop_all(self, message: Message):
        self._running = False
        self._work_loop = False
        self._video_loop = False
        self._bonus_loop = False
        
        if self._current_conv:
            try:
                await self._current_conv.cancel()
            except:
                pass
            self._current_conv = None
            
        await self._edit_or_reply(message, "🛑 Все процессы остановлены")

    async def _show_ref(self, message: Message):
        if not self._ref_link:
            await self._edit_or_reply(message, "Реферальная ссылка не найдена")
            return

        earned = self._ref_count * 12000
        await self._edit_or_reply(
            message,
            f"🔗 Ваша реферальная ссылка:\n{self._ref_link}\n\n" + 
            self.strings["ref_info"].format(self._ref_count, earned)
        )

    async def _play_casino(self, message: Message):
        args = utils.get_args_raw(message).replace("casino", "").strip()
        if not args:
            await self._edit_or_reply(message, "Укажите ставку (например: .bgs casino 1000)")
            return

        try:
            bet = int(args) if args != "all" else None
            async with self._client.conversation(self._bot, exclusive=False) as conv:
                if bet is None:
                    await conv.send_message("б")
                    balance = await conv.get_response()
                    bet = int(balance.text.split("Деньги:")[1].split("💰")[0].strip())

                await conv.send_message(f"Казино {bet}")
                response = await conv.get_response()
                
                if "выиграл" in response.text:
                    multiplier = float(response.text.split("x")[1].split()[0])
                    won = int(bet * multiplier)
                    await self._edit_or_reply(message, self.strings["casino_win"].format(won, multiplier))
                else:
                    await self._edit_or_reply(message, self.strings["casino_lose"].format(bet))

        except Exception as e:
            await self._edit_or_reply(message, self.strings["error"].format(str(e)))

    async def _start_race(self, message: Message):
        args = utils.get_args_raw(message).replace("race", "").strip()
        bet = int(args) if args else self.config["race_bet"]

        try:
            async with self._client.conversation(self._bot, exclusive=False) as conv:
                await conv.send_message(f"Участвовать в гонке {bet}")
                response = await conv.get_response()
                await self._edit_or_reply(message, f"🏎️ Результат гонки:\n{response.text}")

        except Exception as e:
            await self._edit_or_reply(message, self.strings["error"].format(str(e)))

    async def _send_hate(self, message: Message):
        args = utils.get_args_raw(message).replace("hate", "").strip()
        if not args:
            await self._edit_or_reply(message, "Укажите пользователя (например: .bgs hate @username)")
            return

        try:
            count = min(self.config["max_hate"], 10)
            async with self._client.conversation(self._bot, exclusive=False) as conv:
                await conv.send_message(f"Захейтить {args} {count}")
                response = await conv.get_response()
                await self._edit_or_reply(message, f"💢 Результат:\n{response.text}")

        except Exception as e:
            await self._edit_or_reply(message, self.strings["error"].format(str(e)))

    async def _show_profile(self, message: Message):
        try:
            async with self._client.conversation(self._bot, exclusive=False) as conv:
                await conv.send_message("Профиль")
                response = await conv.get_response()
                await self._edit_or_reply(message, f"📄 <b>Ваш профиль:</b>\n{response.text}")

        except Exception as e:
            await self._edit_or_reply(message, self.strings["error"].format(str(e)))

    async def _show_balance(self, message: Message):
        try:
            async with self._client.conversation(self._bot, exclusive=False) as conv:
                await conv.send_message("б")
                response = await conv.get_response()
                await self._edit_or_reply(message, f"💰 <b>Баланс:</b>\n{response.text}")

        except Exception as e:
            await self._edit_or_reply(message, self.strings["error"].format(str(e)))

    async def _get_bonus(self, message: Message):
        if not self.config["daily_bonus_enabled"]:
            await self._edit_or_reply(message, "🚫 Ежедневный бонус отключен")
            return

        try:
            async with self._client.conversation(self._bot, exclusive=False) as conv:
                await conv.send_message("Ежедневный бонус")
                response = await conv.get_response()
                await self._edit_or_reply(message, f"🎁 <b>Бонус:</b>\n{response.text}")

        except Exception as e:
            await self._edit_or_reply(message, self.strings["error"].format(str(e)))
