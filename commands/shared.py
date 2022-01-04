import discord

import TableBotExceptions
import UserDataProcessing
import common


async def mkwx_check(message, error_message):
    if common.is_bad_wolf(message.author):
        return True

    if common.DISABLE_MKWX_COMMANDS:
        raise TableBotExceptions.CommandDisabled(error_message)
    if common.LIMIT_MKWX_COMMANDS:
        if common.LIMITED_SERVER_IDS is not None and message.guild.id in common.LIMITED_SERVER_IDS:
            return True
        if common.LIMITED_CHANNEL_IDS is not None and message.channel.id in common.LIMITED_CHANNEL_IDS:
            return True
        raise TableBotExceptions.CommandDisabled(error_message)


async def sendRoomWarNotLoaded(message: discord.Message, serverPrefix: str, is_lounge=False):
    if is_lounge:
        return await message.channel.send(
            f"Room is not loaded! Use the command `{serverPrefix}sw mogiformat numberOfTeams` to load a room."
        )
    else:
        return await message.channel.send(
            f"Room is not loaded! Use the command `{serverPrefix}sw warformat numberOfTeams (LoungeName/rxx/FC) (gps=numberOfGPs) (psb=on/off) (miis=yes/no)` to start a war."
        )


async def updateData(id_lounge, fc_id):
    UserDataProcessing.smartUpdate(id_lounge, fc_id)
