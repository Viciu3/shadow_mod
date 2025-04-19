__version__ = (7, 7, 9)         
# meta developer: @Shadow_red1, @familiarrrrrr
#         ╭══• ೋ•✧๑♡๑✧•ೋ •══╮
#                  @Yaukais
#               ╔══╗╔╗ ♡ ♡ ♡  
#               ╚╗╔╝║║╔═╦╦╦╔╗
#               ╔╝╚╗║╚╣║║║║╔╣  
#               ╚══╝╚═╩═╩═╩═╝     
#                   ╔═══╗♪
#                   ║███║ ♫
#                   ║(●)║♫
#                   ╚═══╝ ♪
#              ஜ۞ஜ YOU ஜ۞ஜ
#              ➺𒋨M𝙀Ƭ𝙄Ө𝙍𒆙➤
#         ╰══• ೋ•✧๑♡๑✧•ೋ •══╯

from telethon import events
from .. import loader, utils
import asyncio

@loader.tds
class Room_ghost(loader.Module):
    """Автокомнаты от Тени! @familiarrrrrr | настройка в кфг.)"""

    strings = {"name": "Ghost-room"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "button_row_index",
                0,
                "Индекс строки кнопок (0 - первая строка, 1 - вторая)",
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "button_column_index",
                0,
                "Индекс кнопки в строке (0 - первая кнопка, 1 - вторая)",
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "BFGB_name",
                None,
                "Игровое имя в боте @bfgbunker_bot",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "target_chat_id",
                5813222348,
                "ID чата, в который будут отправляться сообщения о починке бункера.",
                validator=loader.validators.Integer(),
            ),
        )
        self.trigger_active = False

    async def ghostoncmd(self, message):
        """Используйте .ghoston <интервал в секундах> для начала кликов."""
        if not message.is_reply:
            await message.edit('<b>Нету реплая.</b>')
            return

        args = utils.get_args_raw(message)
        try:
            interval = float(args)
        except ValueError:
            interval = 1.5
        
        self.clicker = True
        await message.edit(f'<b><blockquote><emoji document_id=5873127366485610469>😈</emoji> Ghost-room <emoji document_id=5444900804743939405>🤩</emoji> включён.<emoji document_id=5785243749969825324>👻</emoji>\n\n<emoji document_id=5215484787325676090>🕐</emoji> Интервал: {interval} секунд.<emoji document_id=5341649649214182916>🥰</emoji></blockquote></b>')
        
        while self.clicker:
            reply = await message.get_reply_message()
            if reply and reply.buttons:
                row_index = self.config["button_row_index"]
                column_index = self.config["button_column_index"]

                if row_index < len(reply.buttons) and column_index < len(reply.buttons[row_index]):
                    button = reply.buttons[row_index][column_index]
                    await button.click()
                    await asyncio.sleep(interval)
                else:
                    await message.edit('<b>Указанный индекс кнопки вне диапазона.</b>')
                    self.clicker = False
                    break
            else:
                await message.edit('<b>В сообщении нет инлайн кнопок для нажатия.</b>')
                self.clicker = False
                break

    async def ghostoffcmd(self, message):
        """Используйте .ghostoff для остановки кликера."""
        self.clicker = False
        await message.edit('<b><blockquote><emoji document_id=5873127366485610469>😈</emoji> Ghost-room <emoji document_id=5444900804743939405>🤩</emoji> выключен.<emoji document_id=5785243749969825324>👻</emoji></blockquote></b>')

    async def ghostinfocmd(self, message):
        """Используйте .ghostinfo для получения информации о режимах и интервалах также комбинацыи нажатия."""
        info_message = (
            "[row] [column] кфг настройка!\n"
            "[ 0 ] [ 0 ] это режим за кр.\n"
            "[ 0 ] [ 1 ] это режим за бут.\n"
            "[ 1 ] [ 0 ] это +1 интервал 1s\n"
            "[ 1 ] [ 1 ] это +5 интервал 1s\n"
            "[ 2 ] [ 0 ] это +20 интервал 60s\n"
            "[ 2 ] [ 1 ] это +100 интервал 120s\n"
            "[ 3 ] [ 0 ] это +1000 интервал 180s\n"
            "[ 4 ] [ 0 ] это +5000 интервал 180s"
        )
        await message.edit(info_message)

    async def client_ready(self, client, db):
        self.db = db
        self.client = client

        @self.client.on(events.NewMessage(from_users='@bfgbunker_bot'))
        async def trigger_handler(event):
            bfgb_name = self.config["BFGB_name"]
            
            if not bfgb_name:
                # Отправляем сообщение в указанный чат
                target_chat_id = self.config["target_chat_id"]
                await self.client.send_message(target_chat_id, "Параметр 'Игровое имя' не настроен. Пожалуйста, настройте его перед запуском.")
                return

            if f"{bfgb_name}, в бункере произошёл пожар" in event.raw_text or f"{bfgb_name}, в бункере произошёл потоп" in event.raw_text:
                if not self.trigger_active:
                    self.trigger_active = True
                    
                    # Отправляем сообщение в указанный чат
                    target_chat_id = self.config["target_chat_id"]
                    await self.client.send_message(target_chat_id, "Починить бункер")

                    for _ in range(3):
                        await asyncio.sleep(3)

                    response = await self.client.wait_for(
                        events.NewMessage(from_users='@bfgbunker_bot'),
                        timeout=30
                    )
                    if f"{bfgb_name}, ты успешно исправил(-а) происшествие" in response.raw_text:
                        self.trigger_active = False