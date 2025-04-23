__version__ = (7, 7, 7)         
# meta developer:@Yaukais, @Shadow_red1, @familiarrrrrr
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
#              ➺𒋨M𝙀Ƭ𝙄ӨR𒆙➤
#         ╰══• ೋ•✧๑♡๑✧•ೋ •══╯

import asyncio
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils
from telethon import functions, types
from ..inline.types import InlineCall

class ClanTreasuryMod(loader.Module):
    """Модуль для управления казной клана в боте @bforgame_bot. Помошь по модулю тут https://t.me/szadow_mod777"""
    strings = {"name": "ClanTreasury_Ghost"}

    _bot = "@bforgame_bot"

    async def казнаcmd(self, message: Message):
        """Получить информацию о казне клана."""
        async with self._client.conversation(self._bot) as conv:
            await conv.send_message("Мой клан")
            response = await conv.get_response(timeout=5)
            if response is None:
                await conv.send_message("Мой клан")
                response = await conv.get_response(timeout=5)
                if response is None:
                    await message.edit("Не удалось получить информацию о клане.")
                    return

            info_text = response.raw_text
            members_count = int(info_text.split(" Участников: ")[1].split("\n")[0])
            treasury = info_text.split(" В казне клана: ")[1].split("\n")[0]

            # Находим инлайн кнопку с коллбеком clanMembers
            for row in response.reply_markup.rows:
                for button in row.buttons:
                    if hasattr(button, 'data') and button.data.decode() == 'clanMembers':
                        await response.click(data=button.data)
                        break
                else:
                    continue
                break
            else:
                await message.edit("Кнопка 'Участники клана' не найдена.")
                return

            members_response = await conv.get_response(timeout=5)
            if members_response is None:
                await message.edit("Не удалось получить информацию об участниках клана.")
                return

            members_info = members_response.raw_text.split("\n")[1:]
            members = []
            for member in members_info:
                name = member.split("] | [")[1].split(" (")[0]
                member_id = member.split("(")[1].split(")")[0]
                members.append({"name": name, "id": member_id, "today_contribution": 0})

            self.members = members
            self.treasury = treasury
            self.total_contribution = 0

            await self.show_treasury(message)

    async def show_treasury(self, message: Message):
        """Отобразить информацию о казне клана."""
        members_list = "\n".join(
            [f" | {i + 1}№ - {member['today_contribution']} "
             for i, member in enumerate(self.members)])

        treasury_message = f"""  Казна клана !!!
••••••••••••••••••••••••••••••••
⛵️Всё участники клана:

{members_list}

•••••••••••••••••••••••••••
⛵️В казне в общем:
 | {self.total_contribution}  /  {self.treasury}

"""
        await self.inline.form(
            text=treasury_message,
            message=message,
            reply_markup=[[{"text": "  Топ по вкладу ", "callback": self.show_top}]]
        )

    async def show_top(self, call: InlineCall):
        """Отобразить топ участников по вкладу."""
        sorted_members = sorted(self.members, key=lambda x: x["today_contribution"], reverse=True)
        top_list = "\n".join(
            [f" | {i + 1}№ - {member['today_contribution']} "
             for i, member in enumerate(sorted_members)])

        top_message = f"""  Казна клана !!!
•••••••••••••••••••••••••••••••••••••••••••••••
⛵️ | Топ участники клана по казне:

{top_list}

•••••••••••••••••••••••••••
⛵️В казне в общем:
 | {self.total_contribution}  /  {self.treasury}

"""
        await call.edit(
            text=top_message,
            reply_markup=[[{"text": "⬅️ Назад", "callback": self.show_treasury}]]
        )