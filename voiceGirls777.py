# meta developer: @Shadow_red1
from telethon.tl.functions.channels import JoinChannelRequest
from .. import loader

@loader.tds
class voiceGirls777(loader.Module):
    """Голосовые сообщения девушек"""

    strings = {"name": "voiceGirls777"}

    async def яматаcmd(self, message):
        """| Ямата"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/gchost_voiceMod/4",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def чтотытамcmd(self, message):
        """| Что ты там?"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/gchost_voiceMod/5",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def интересноcmd(self, message):
        """| Интересно"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/gchost_voiceMod/6",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def токпишешьcmd(self, message):
        """| Ток пишешь?"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/gchost_voiceMod/7",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def несудьбаcmd(self, message):
        """| Не судьба?"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/gchost_voiceMod/8",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return

    async def идинахуйcmd(self, message):
        """| Иди нахуй"""

        reply = await message.get_reply_message()
        await message.delete()
        await message.client.send_file(
            message.to_id,
            "https://t.me/gchost_voiceMod/10",
            voice_note=True,
            reply_to=reply.id if reply else None,
        )
        return