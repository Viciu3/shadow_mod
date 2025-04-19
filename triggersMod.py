__version__ = (7, 7, 7)
# meta developer: @Yaukais, @Shadow_red1
from .. import loader, utils
from telethon import events
import asyncio

class triggersMod(loader.Module):
    """Настроить триггеры в кфг для автоматических ответов!"""
    strings = {"name": "triggersMod"}

    def __init__(self):
        super().__init__()
        self.config = loader.ModuleConfig(
            *[loader.ConfigValue(
                f"trigger_{i}",
                None,
                doc=lambda: f"Введите сообщение триггера. По умолчанию None."
            ) for i in range(1, 5)] +
            [loader.ConfigValue(
                f"text_{i}",
                None,
                doc=lambda: f"Введите ответ на сообщение триггера. По умолчанию None."
            ) for i in range(1, 5)] +
            [loader.ConfigValue(
                f"chat_{i}",
                None,
                doc=lambda: f"Введите ID чата или @username бота для триггера. По умолчанию None."
            ) for i in range(1, 5)] +
            [loader.ConfigValue(
                f"count_{i}",
                1,
                doc=lambda: f"Введите количество отправляемых сообщений для триггера. По умолчанию 1."
            ) for i in range(1, 5)] +
            [loader.ConfigValue(
                "enabled",
                True,
                doc=lambda: "Включить или отключить триггеры. По умолчанию True.",
            )]
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.client.add_event_handler(self.handler, events.NewMessage())

    async def handler(self, event):
        """Обработчик новых сообщений"""
        if not self.config["enabled"]:
            return

        for i in range(1, 5):
            trigger = self.config[f"trigger_{i}"]
            response = self.config[f"text_{i}"]
            chat_id = self.config[f"chat_{i}"]
            count = self.config[f"count_{i}"]

            if event.raw_text == trigger and chat_id and response:
                # Отправка сообщений с задержкой
                for _ in range(count):
                    await self.client.send_message(chat_id, response)
                    await asyncio.sleep(1.5)  # Задержка 1.5 секунды между сообщениями
                break  # Прекратить цикл после отправки сообщений

    @loader.command()
    async def enabletriggercmd(self, message):
        """Включить триггеры"""
        self.config["enabled"] = True
        await message.edit("<emoji document_id=6325687241536440125>✅</emoji> Триггеры включены.")

    @loader.command()
    async def disabletriggercmd(self, message):
        """Выключить триггеры"""
        self.config["enabled"] = False
        await message.edit("<emoji document_id=5032973497861669622>❌</emoji> Триггеры выключены.")