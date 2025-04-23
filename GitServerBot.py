#      ███████╗  █████╗   ██████╗  ███╗   ███╗
#      ██╔════╝ ██╔══██╗ ██╔═══██╗ ████╗ ████║
#      ███████╗ ███████║ ██║   ██║ ██╔████╔██║
#      ╚════██║ ██╔══██║ ██║▄▄ ██║ ██║╚██╔╝██║
#      ███████║ ██║  ██║  ██████╔╝ ██║ ╚═╝ ██║

# meta developer: @Yaukais,@Shadow_red1

import asyncio
import os
import subprocess
import time
import shutil
from .. import loader, utils
from hikkatl.types import Message

@loader.tds
class GitServerBot(loader.Module):
    """Модуль для запуска ботов через GitHub!"""
    strings = {
        "name": "GitServerBot",
        "loader_Repo": "URL репозитория GitHub."
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "repo",
                "None",
                lambda: self.strings["loader_Repo"],
                validator=loader.validators.String(),
            ),
        )
        self.processes = {}

    async def pythoncmd(self, message: Message):
        """Запускает файл бота"""
        try:
            bot_file = message.text.strip().split(" ", 1)[1]
            repo_url = self.config.get("repo")

            if repo_url == "None":
                await message.reply("Репозиторий не указан в конфигурации.")
                return

            if not shutil.which("git"):
                await message.reply("Git не установлен.")
                return

            if not shutil.which("python3"):
                await message.reply("Python3 не установлен.")
                return

            if not os.path.exists("bot_repo"):
                process = await asyncio.create_subprocess_exec(
                    "git", "clone", repo_url, "bot_repo",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    await message.reply(f"Ошибка клонирования репозитория: {stderr.decode()}")
                    return

            bot_path = os.path.join("bot_repo", bot_file)

            if os.path.exists(bot_path):
                process = await asyncio.create_subprocess_exec(
                    "python3", bot_path,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                self.processes[bot_file] = process
                await message.reply(f"Бот {bot_file} запущен.")
            else:
                await message.reply("Файл бота не найден.")

        except Exception as e:
            await message.reply(f"Произошла ошибка: {e}")

    async def of_bcmd(self, message: Message):
        """Отключает файл бота"""
        try:
            bot_file = message.text.strip().split(" ", 1)[1]

            if bot_file in self.processes:
                process = self.processes[bot_file]
                if process.returncode is None:  # Проверяем, запущен ли процесс
                    process.terminate()
                    await process.wait()  # Ждем завершения процесса
                    del self.processes[bot_file]
                    await message.reply(f"Бот {bot_file} остановлен.")
                else:
                    await message.reply("Бот уже остановлен.")
            else:
                await message.reply("Бот не запущен.")

        except Exception as e:
            await message.reply(f"Произошла ошибка: {e}")

    async def restart_bcmd(self, message: Message):
        """Перезапускает файл бота"""
        try:
            bot_file = message.text.strip().split(" ", 1)[1]

            if bot_file in self.processes:
                process = self.processes[bot_file]
                if process.returncode is None:
                    process.terminate()
                    await process.wait()
                    del self.processes[bot_file]

            await self.pythoncmd(message)

        except Exception as e:
            await message.reply(f"Произошла ошибка: {e}")

    async def bot_pingcmd(self, message: Message):
        """Показывает задержку бота"""
        try:
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                "python3", "-c", "import time; time.sleep(0.1)",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            await process.communicate()
            ping = (time.time() - start_time) * 1000
            await message.reply(f"Задержка бота: {ping:.2f} мс.")

        except Exception as e:
            await message.reply(f"Произошла ошибка: {e}")

    async def clear_datacmd(self, message: Message):
        """Удаляет все данные с сервера"""
        try:
            if os.path.exists("bot_repo"):
                shutil.rmtree("bot_repo")
                await message.reply("Все данные успешно удалены.")
            else:
                await message.reply("Данные не найдены.")

        except Exception as e:
            await message.reply(f"Произошла ошибка: {e}")