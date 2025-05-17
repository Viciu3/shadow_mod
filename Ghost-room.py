__version__ = (7, 8, 0)
# meta developer: @Shadow_red1, @familiarrrrrr
#         ╭══• ೋ•✧๑♡๑✧•ೋ •══╮
#                  @Yaukais
#               ╔══╗╔╗ ♡ ♡ ♡
#               ╚╗╔╝║║╔═╦╦╦╔╗
#               ╔╝╚╗║║╔═╦╦╦╔╗
#               ╚══╝╚═╩═╩═╩═╝
#                   ╔═══╗♪
#                   ║███║ ♫
#                   ║(●)║♫
#                   ╚═══╝ ♪
#              ஜ۞ஜ YOU ஜ۞ஜ
#              ➺𒋨M𝙀Ƭ𝙄ӨR𒆙➤
#         ╰══• ೋ•✧๑♡๑✧•ೋ •══╯

from telethon import events
from .. import loader, utils
import asyncio

@loader.tds
class Ghostroom(loader.Module):
    """Автокомнаты от Тени! @familiarrrrrr | настройка в кфг."""

    strings = {"name": "Ghost-room"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "button_row_index",
                0,
                "Индекс строки кнопки (0 - первая строка, 1 - вторая)",
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "button_column_index",
                0,
                "Индекс кнопки в строке (0 - первая кнопка, 1 - вторая)",
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "target_chat_id",
                5813222348,
                "ID чата, в который будет отправляться сообщение 'Починить бункер'.",
                validator=loader.validators.Integer(),
            ),
        )
        self.clicker_active = asyncio.Event()

    async def ghostoncmd(self, message):
        """Используйте .ghoston <задержка_кнопки> <задержка_сообщения> для раздельной настройки задержек.
        Если указано одно значение, оно будет использовано для обеих задержек."""
        if not message.is_reply:
            await message.edit('<b>Нету реплая.</b>')
            return

        args = utils.get_args_raw(message).split()
        if len(args) == 1:
            try:
                delay = float(args[0])
                button_interval = delay
                message_interval = delay
            except ValueError:
                await message.edit('<b>⚠️ Неправильный формат задержки. Укажите одно или два числа.</b>')
                return
        elif len(args) == 2:
            try:
                button_interval = float(args[0])
                message_interval = float(args[1])
            except ValueError:
                await message.edit('<b>⚠️ Неправильный формат задержек. Укажите два числа через пробел.</b>')
                return
        else:
            await message.edit('<b>⚠️ Неправильное количество аргументов. Укажите одну или две задержки.</b>')
            return

        self.clicker_active.set()
        await message.edit(f'<b><blockquote><emoji document_id=5873127366485610469>😈</emoji> Ghost-room включён.<emoji document_id=5444900804743939405>🤩</emoji>\n\n<emoji document_id=5215484787325676090>🕐</emoji> КД кнопки: {button_interval} секунд.\n<emoji document_id=5215484787325676090>🕐</emoji> КД сообщения: {message_interval} секунд.</blockquote></b>')

        while self.clicker_active.is_set():
            reply = await message.get_reply_message()
            if reply and reply.buttons:
                row_index = self.config["button_row_index"]
                column_index = self.config["button_column_index"]

                if row_index < len(reply.buttons) and column_index < len(reply.buttons[row_index]):
                    button = reply.buttons[row_index][column_index]
                    await button.click()
                    await asyncio.sleep(button_interval)

                    target_chat_id = self.config["target_chat_id"]
                    await self.client.send_message(target_chat_id, "Починить бункер")
                    await asyncio.sleep(message_interval)
                else:
                    await message.edit('<b>⚠️ В сообщении нет инлайн кнопок для нажатия.</b>')
                    self.clicker_active.clear()
                    break
            else:
                await message.edit('<b>В сообщении нет инлайн кнопок для нажатия.</b>')
                self.clicker_active.clear()
                break

        await message.edit(f'<b><blockquote><emoji document_id=5873127366485610469>😈</emoji> Ghost-room выключен.<emoji document_id=5444900804743939405>🤩</emoji></blockquote></b>')

    async def ghostoffcmd(self, message):
        """Используйте .ghostoff для остановки кликера."""
        self.clicker_active.clear()
        await message.edit('<b><blockquote><emoji document_id=5873127366485610469>😈</emoji> Ghost-room выключен.<emoji document_id=5444900804743939405>🤩</emoji></blockquote></b>')

    async def ghostinfocmd(self, message):
        """Используйте .ghostinfo для получения информации о режимах и комбинациях нажатия."""
        info_message = (
            "[row] [column] кфг настройка!\n"
            "[ 0 ] [ 0 ] это режим за кр.\n"
            "[ 0 ] [ 1 ] это режим за бут.\n"
            "[ 1 ] [ 0 ] это +1 интервал 1.5s\n"
            "[ 1 ] [ 1 ] это +5 интервал 1.5s\n"
            "[ 2 ] [ 0 ] это +20 интервал 60s\n"
            "[ 2 ] [ 1 ] это +100 интервал 120s\n"
            "[ 3 ] [ 0 ] это +1000 интервал 180s\n"
            "[ 4 ] [ 0 ] это +5000 интервал 180s\n\n"
            "Кд для клик и смс в сикундах:\n"
            "• Клик - 1.5s; 60s; 120s; 180s.\n"
            "• Смс - 1.5s; 60s; 120s; 180s.\n\n"
            "Как правильно запустить прокачку:\n"
            "• Теперь доступно 2 вида ввода:\n"
            "1 .ghoston 60 ( кд клик 60s, кд смс 60s)\n"
            "2 .ghoston 120 180 (кд клик 120s кд смс 180s\n"
            "Таким образом можно теперь запускать прокачку"
        )
        await message.edit(info_message)
