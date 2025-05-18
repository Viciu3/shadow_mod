__version__ = (7, 7, 7)
# meta developer: @shadow_mod777
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

import asyncio
import re
from hikkatl.types import Message
from .. import loader, utils
from telethon import events
from telethon.tl import types
from datetime import datetime, timedelta

@loader.tds
class ShadowMute(loader.Module):
    """Временно ограничивает пользователя в чате."""
    strings = {
        "name": "ShadowMute",
        "add_chat": "✅ | Этот чат добавлен в список разрешенных для мута.",
        "remove_chat": "🗑️ | Этот чат удален из списка разрешенных для мута.",
        "current_chats": "⚙️ | Текущие разрешенные чаты для мута: {}",
        "args_required_mute": "🚫 | Укажите пользователя и период мута.",
        "user_not_found": "🚫 | Пользователь не найден.",
        "time_format_error": "🚫 | Неверный формат времени. Используйте: <число>[s/m/h/d].",
        "real_muted": "🔇 | Пользователь {} заблокирован на {}.",
        "not_in_allowed_chat": "🚫 | Эта команда доступна только в разрешенных чатах.",
        "already_muted": "⚠️ | Пользователь {} уже заблокирован до {}.",
        "unmuted": "🔓 | Пользователь {} разблокирован.",
        "admin_error": "🚫 | У меня недостаточно прав для блокировки пользователя.",
    }

    def __init__(self):
        self.allowed_chats = set()
        self.muted_users = {}  # {chat_id: {user_id: until_datetime}}

    @loader.command(ru_doc="Добавить/удалить текущий чат из списка разрешенных для мута.")
    async def shaddchat(self, message: Message):
        """Добавить/удалить текущий чат из списка разрешенных для мута."""
        chat_id = message.chat_id
        if chat_id not in self.allowed_chats:
            self.allowed_chats.add(chat_id)
            await utils.answer(message, self.strings("add_chat"))
        else:
            self.allowed_chats.discard(chat_id)
            await utils.answer(message, self.strings("remove_chat"))

    @loader.command(ru_doc="Показать список разрешенных чатов для мута.")
    async def shlistchats(self, message: Message):
        """Показать список разрешенных чатов для мута."""
        chats = "\n".join(map(str, self.allowed_chats)) if self.allowed_chats else "Нет разрешенных чатов."
        await utils.answer(message, self.strings("current_chats").format(chats))

    def parse_time(self, time_str: str):
        """Парсит строку времени в timedelta."""
        match = re.match(r"(\d+)([smhd])", time_str.lower())
        if not match:
            raise ValueError("Неверный формат времени")
        value = int(match.group(1))
        unit = match.group(2)
        if unit == 's':
            return timedelta(seconds=value)
        elif unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        raise ValueError("Неверная единица времени")

    @loader.command(
        ru_doc="<@пользователь> <время> - Временно блокирует пользователя.",
        args="<@пользователь> <время>"
    )
    async def shsmute(self, message: Message):
        """Временно заблокировать пользователя."""
        if message.chat_id not in self.allowed_chats:
            await utils.answer(message, self.strings("not_in_allowed_chat"))
            return

        args = utils.get_args(message)
        if len(args) < 2:
            await utils.answer(message, self.strings("args_required_mute"))
            return

        user_arg = args[0]
        time_arg = args[1]

        user = None
        try:
            user = await self._client.get_entity(user_arg)
        except ValueError:
            pass  
        if not user:
            await utils.answer(message, self.strings("user_not_found"))
            return

        chat_id = message.chat_id
        user_id = user.id

        try:
            mute_duration = self.parse_time(time_arg)
            until = datetime.now() + mute_duration
            until_timestamp = int(until.timestamp())
        except ValueError:
            await utils.answer(message, self.strings("time_format_error"))
            return

        if chat_id not in self.muted_users:
            self.muted_users[chat_id] = {}

        if user_id in self.muted_users[chat_id] and self.muted_users[chat_id][user_id] > datetime.now():
            await utils.answer(message, self.strings("already_muted").format(utils.escape_html(user.first_name) if user.first_name else utils.escape_html(user.username) if user.username else user.id, self.muted_users[chat_id][user_id].strftime("%Y-%m-%d %H:%M:%S")))
            return

        try:
            await self._client.edit_permissions(
                chat_id,
                user_id,
                until_date=until_timestamp,
                send_messages=False
            )
            self.muted_users[chat_id][user_id] = until
            await utils.answer(message, self.strings("real_muted").format(utils.escape_html(user.first_name) if user.first_name else utils.escape_html(user.username) if user.username else user.id, self.format_timedelta(mute_duration)))
        except Exception as e:
            await utils.answer(message, self.strings("admin_error"))
            logging.error(f"Ошибка при блокировке пользователя: {e}")

    def format_timedelta(self, delta: timedelta):
        """Форматирует timedelta в удобочитаемый вид."""
        parts = []
        if delta.days > 0:
            parts.append(f"{delta.days} д.")
        hours = delta.seconds // 3600
        if hours > 0:
            parts.append(f"{hours} ч.")
        minutes = (delta.seconds % 3600) // 60
        if minutes > 0:
            parts.append(f"{minutes} мин.")
        seconds = delta.seconds % 60
        if seconds > 0 and not parts:
            parts.append(f"{seconds} сек.")
        return " ".join(parts) or "менее секунды"

    @loader.command(ru_doc="<@пользователь> - Снимает временную блокировку с пользователя.")
    async def shunsmute(self, message: Message):
        """Снять временную блокировку с пользователя."""
        if message.chat_id not in self.allowed_chats:
            await utils.answer(message, self.strings("not_in_allowed_chat"))
            return

        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("args_required_mute").split()[0])  # Только пользователь нужен
            return

        user = None
        try:
            user = await self._client.get_entity(args[0])
        except ValueError:
            pass

        if not user:
            await utils.answer(message, self.strings("user_not_found"))
            return

        chat_id = message.chat_id
        user_id = user.id

        if chat_id in self.muted_users and user_id in self.muted_users[chat_id]:
            del self.muted_users[chat_id][user_id]
            try:
                await self._client.edit_permissions(
                    chat_id,
                    user_id,
                    send_messages=True
                )
                await utils.answer(message, self.strings("unmuted").format(utils.escape_html(user.first_name) if user.first_name else utils.escape_html(user.username) if user.username else user.id))
            except Exception as e:
                await utils.answer(message, self.strings("admin_error"))
                logging.error(f"Ошибка при разблокировке пользователя: {e}")
        else:
            await utils.answer(message, f"⚠️ | Пользователь {utils.escape_html(user.first_name) if user.first_name else utils.escape_html(user.username) if user.username else user.id} не заблокирован в этом чате.")
