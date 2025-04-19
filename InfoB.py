__version__ = (7, 7, 7)  # meta developer: @Yaukais

from telethon import functions, types
from telethon.tl.types import Message
from .. import loader, utils
from ..inline.types import InlineCall

import asyncio

class InfoBMod(loader.Module):
    """Статистика баланса игроков из бота @bfgbunker_bot"""
    strings = {"name": "InfoB"}

    def __init__(self):
        super().__init__()
        self.bot = '@bfgbunker_bot'  # Имя или ID вашего бота
        self.custom_color = None
        self.blockquote_enabled = True

    async def binfocmd(self, message: Message):
        """Отправить информацию из бункера"""
        user_id = message.text.split(maxsplit=1)

        if len(user_id) < 2:
            await message.reply("<b><emoji document_id=5253952855185829086>⚙️</emoji> Пожалуйста, укажите ID пользователя.</b>", parse_mode='html')
            return

        user_id = user_id[1].strip()

        async with self._client.conversation(self.bot) as conv:
            await conv.send_message(f"узнать о {user_id}")
            response = await conv.get_response()

            info_text = response.raw_text
            nick_start = info_text.find("🙎‍♂️")
            nick_end = info_text.find("\n", nick_start)
            nick = info_text[nick_start+4:nick_end].strip()
            bottles_text = info_text.split("Бутылок:")[1].split()[0].strip()
            bottles = int("".join(filter(str.isdigit, bottles_text)))
            bottles = "{:,}".format(int(bottles)).replace(",", ".")
            
            money_parts = info_text.split("Баланс:")[1].split()[0].strip().split('/')
            formatted_money = f"{money_parts[0]}/{money_parts[1]}"
            
            people = int("".join(filter(str.isdigit, info_text.split("Людей в бункере:")[1].split('\n')[0].strip())))
            people_in_line = int("".join(filter(str.isdigit, info_text.split("Людей в очереди в бункер:")[1].split('/')[0].strip())))
            max_people = int("".join(filter(str.isdigit, info_text.split("Макс. вместимость людей:")[1].split()[0].strip())))
            
            profit_start = info_text.find("💵")
            profit_end = info_text.find("\n", profit_start)
            profit = info_text[profit_start+1:profit_end].strip()

            # Извлечение информации о VIP
            vip_line = next((line for line in info_text.split('\n') if 'VIP' in line), None)
            if vip_line:
                if "VIP1" in vip_line:
                    vip_status = "⚡️VIP1⚡️"
                    custom_vip_status = "<emoji document_id=5377834924776627189>⚡️</emoji>VIP1<emoji document_id=5377834924776627189>⚡️</emoji>"
                elif "VIP2" in vip_line:
                    vip_status = "🔥🔥VIP2🔥🔥"
                    custom_vip_status = "<emoji document_id=5334725814040674667>🔥</emoji><emoji document_id=5334725814040674667>🔥</emoji>VIP2<emoji document_id=5334725814040674667>🔥</emoji><emoji document_id=5334725814040674667>🔥</emoji>"
                elif "VIP3" in vip_line:
                    vip_status = "💎💎💎VIP3💎💎💎"
                    custom_vip_status = "<emoji document_id=5465283645788937267>💎</emoji><emoji document_id=5465283645788937267>💎</emoji><emoji document_id=5465283645788937267>💎</emoji>VIP3<emoji document_id=5465283645788937267>💎</emoji><emoji document_id=5465283645788937267>💎</emoji><emoji document_id=5465283645788937267>💎</emoji>"
                elif "VIP4" in vip_line:
                    vip_status = "⭐️⭐️⭐️VIP4⭐️⭐️⭐️"
                    custom_vip_status = "<emoji document_id=5469641199348363998>⭐️</emoji><emoji document_id=5469641199348363998>⭐️</emoji><emoji document_id=5469641199348363998>⭐️</emoji>VIP4<emoji document_id=5469641199348363998>⭐️</emoji><emoji document_id=5469641199348363998>⭐️</emoji><emoji document_id=5469641199348363998>⭐️</emoji>"
                else:
                    vip_status = vip_line.strip()
                    custom_vip_status = vip_status
            else:
                vip_status = "Нет VIP"
                custom_vip_status = vip_status

            # Извлечение информации о GPoints
            gpoints_line = next(line for line in info_text.split('\n') if 'GPoints:' in line)
            gpoints = gpoints_line.split("GPoints:")[1].strip()

            # Обычный формат
            normal_info = (
                f"{vip_status}\n\n"
                f"🙎‍♂️ {nick}\n\n"
                f"💰 <b>Баланс:</b> {formatted_money} кр.\n\n"
                f"🍾 <b>Бутылок:</b> {bottles}\n\n"
                f"🍪 <b>GPoints:</b> {gpoints}\n\n"
                f"🧍 <b>Людей в бункере:</b> {people}\n"
                f"      ↳<b>Людей в очереди:</b> {people_in_line}\n\n"
                f"<code>Макс. человек: </code>{max_people}\n\n"
                f"💵 <b>{profit}</b>"
            )

            # Кастомные форматы
            yellow_custom_info = (
                f"<blockquote>\n"
                f"{custom_vip_status}\n\n"
                f"<emoji document_id=5787549086550855683>😎</emoji> {nick}\n\n"
                f"<emoji document_id=5413817400573314183>😼</emoji> Крышек: {formatted_money}\n\n"
                f"<emoji document_id=5330136791808746014>🍸</emoji> <b>Бутылок:</b> {bottles}\n\n"
                f"<emoji document_id=5370783443175086955>🍪</emoji> GPoints: {gpoints}\n\n"
                f"<emoji document_id=5309908719910272612>😀</emoji> <b>Людей в бункере:</b> {people}\n"
                f"         ↳<b>Людей в очереди:</b> {people_in_line}\n\n"
                f"<emoji document_id=5992169656473881872>✨</emoji> <code>Макс. человек: </code>{max_people}\n\n"
                f"<emoji document_id=5463046637842608206>🪙</emoji> <b>{profit}</b></blockquote>"
            )

            gray_custom_info = (
                f"<blockquote>\n"
                f"{custom_vip_status}\n\n"
                f"<emoji document_id=6034968082160552605>😀</emoji> {nick}\n\n"
                f"<emoji document_id=5404874922180748672>💰</emoji> Баланс: {formatted_money} кр.\n\n"
                f"<emoji document_id=5357456894095014661>🍾</emoji> <b>Бутылок:</b> {bottles}\n\n"
                f"<emoji document_id=5845945815549350824>🧹</emoji> GPoints: {gpoints}\n\n"
                f"<emoji document_id=5332782165245583579>👱‍♀️</emoji> Людей в бункере: {people}\n"
                f"      ↳Людей в очереди: {people_in_line}\n\n"
                f"<emoji document_id=5172834782823842584>✨</emoji> Макс. человек: {max_people}\n\n"
                f"<emoji document_id=5255713220546538619>💳</emoji> <b>{profit}</b></blockquote>"
            )

            violet_custom_info = (
                f"<blockquote>\n"
                f"{custom_vip_status}\n\n"
                f"<emoji document_id=5267351405097657400>🥷</emoji> {nick}\n\n"
                f"<emoji document_id=5363788917134862211>🤑</emoji> Крышек: {formatted_money}\n\n"
                f"<emoji document_id=5852583696095251740>🍸</emoji> <b>Бутылок:</b> {bottles}\n\n"
                f"<emoji document_id=5370783443175086955>🍪</emoji> GPoints: {gpoints}\n\n"
                f"<emoji document_id=5361977209735094094>😀</emoji> <b>Людей в бункере:</b> {people}\n"
                f"      ↳<b>Людей в очереди:</b> {people_in_line}\n\n"
                f"<emoji document_id=5247171621516491876>✨</emoji> <code>Макс. человек: </code>{max_people}\n\n"
                f"<emoji document_id=5226973403935690497>💵</emoji> <b>{profit}</b></blockquote>"
            )
            
            red_custom_info = (
                f"<blockquote>\n"
                f"{custom_vip_status}\n\n"
                f"<emoji document_id=5271778107630569737>😏</emoji> {nick}\n\n"
                f"<emoji document_id=5271984575298422225>🔑</emoji> Крышек: {formatted_money}\n\n"
                f"<emoji document_id=5273841027667477153>🥫</emoji> <b>Бутылок:</b> {bottles}\n\n"
                f"<emoji document_id=5274244758888267856>🍫</emoji> GPoints: {gpoints}\n\n"
                f"<emoji document_id=5273948161331707563>👅</emoji> <b>Людей в бункере:</b> {people}\n"
                f"      ↳<b>Людей в очереди:</b> {people_in_line}\n\n"
                f"<emoji document_id=5273984118797909024>🩸</emoji> <code>Макс. человек: </code>{max_people}\n\n"
                f"<emoji document_id=5274174145330955103>🐟</emoji> <b>{profit}</b></blockquote>"
            )
            
            green_custom_info = (
                f"<blockquote>\n"
                f"{custom_vip_status}\n\n"
                f"<emoji document_id=5850239498650128930>💚</emoji> {nick}\n\n"
                f"<emoji document_id=5224257782013769471>💰</emoji> Крышек: {formatted_money}\n\n"
                f"<emoji document_id=5850292730474796305>💚</emoji> <b>Бутылок:</b> {bottles}\n\n"
                f"<emoji document_id=5850465263606043373>💚</emoji> GPoints: {gpoints}\n\n"
                f"<emoji document_id=5850605322489565364>💚</emoji> <b>Людей в бункере:</b> {people}\n"
                f"      ↳<b>Людей в очереди:</b> {people_in_line}\n\n"
                f"<emoji document_id=5850531079684886777>💚</emoji> <code>Макс. человек: </code>{max_people}\n\n"
                f"<emoji document_id=5391347832487680986>💵</emoji> <b>{profit}</b></blockquote>"
            )
            
            blue_custom_info = (
                f"<blockquote>\n"
                f"{custom_vip_status}\n\n"
                f"<emoji document_id=5380102710458588262>😠</emoji> {nick}\n\n"
                f"<emoji document_id=5379795555872415861>🧂</emoji> Крышек: {formatted_money}\n\n"
                f"<emoji document_id=5377445293933469655>🥂</emoji>  <b>Бутылок:</b> {bottles}\n\n"
                f"<emoji document_id=5377585924047643521>🍭</emoji> GPoints: {gpoints}\n\n"
                f"<emoji document_id=5379964283662638975>😶</emoji> <b>Людей в бункере:</b> {people}\n"
                f"      ↳<b>Людей в очереди:</b> {people_in_line}\n\n"
                f"<emoji document_id=5379694495291940508>✨</emoji> <code>Макс. человек: </code>{max_people}\n\n"
                f"<emoji document_id=5800709991627232190>💳</emoji> <b>{profit}</b></blockquote>"
            )

            # Определение кастомного формата
            if self.custom_color == 'фиолетовый':
                custom_info = violet_custom_info
            elif self.custom_color == 'жёлтый':
                custom_info = yellow_custom_info
            elif self.custom_color == 'серый':
                custom_info = gray_custom_info
            elif self.custom_color == 'красный':
                custom_info = red_custom_info
            elif self.custom_color == 'зелёный':
                custom_info = green_custom_info
            elif self.custom_color == 'синий':
                custom_info = blue_custom_info    
            elif self.custom_color == 'стандартный':
                custom_info = normal_info    
            elif self.blockquote_enabled:
                custom_info = normal_info
            else:
                custom_info = normal_info

            await message.edit(custom_info, parse_mode='html')

    async def custommodcmd(self, message: Message):
        """Установить кастомный цвет"""
        color = message.text.split(maxsplit=1)

        if len(color) < 2:
            await message.reply("<emoji document_id=5253952855185829086>⚙️</emoji> Пожалуйста, укажите цвет: <code>синий</code>, <code>фиолетовый</code>, <code>красный</code>, <code>зелёный</code>, <code>серый</code>, <code>жёлтый</code>, <code>стандартный</code>.", parse_mode='html')
            return

        color = color[1].strip().lower()

        valid_colors = ['синий', 'фиолетовый', 'красный', 'зелёный', 'серый', 'жёлтый', 'стандартный']
        if color not in valid_colors:
            await message.reply("<emoji document_id=5388785832956016892>❌</emoji> Некорректный цвет. Доступные цвета: <code>синий</code>, <code>фиолетовый</code>, <code>красный</code>, <code>зелёный</code>, <code>серый</code>, <code>жёлтый</code>, <code>стандартный</code>.", parse_mode='html')
            return

        self.custom_color = color
        await message.reply(f"<emoji document_id=5256182535917940722>⤵️</emoji> Кастомный цвет установлен на: <code>{color}</code>", parse_mode='html')

    async def toggleblockquotecmd(self, message: Message):
        """Включить/отключить блоки с форматированием"""
        self.blockquote_enabled = not self.blockquote_enabled
        status = "<emoji document_id=5256182535917940722>⤵️</emoji> включен" if self.blockquote_enabled else "<emoji document_id=5388785832956016892>❌</emoji> отключен"
        await message.reply(f"Блоки с форматированием теперь {status}.", parse_mode='html')