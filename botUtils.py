import common
import TableBot
import discord


def createEmptyTableBot(server_id=None, channel_id=None):
    return TableBot.ChannelBot(server_id=server_id, channel_id=channel_id)

def log_command_sent(message: discord.Message, extra_text=""):
    common.log_text(f"Server: {message.guild} - Channel: {message.channel} - User: {message.author} - Command: {message.content} {extra_text}")
    return common.full_command_log(message, extra_text) 

async def send_lounge_locked_message(message: discord.Message, this_bot: TableBot.ChannelBot):
    to_send = "The bot is locked to players in this room only: **"
    if this_bot.getRoom() is not None:
        if not this_bot.getRoom().is_freed:
            room_lounge_names = this_bot.getRoom().get_loungenames_can_modify_table()
            to_send += ", ".join(room_lounge_names)
            to_send += "**."
        if this_bot.loungeFinishTime is None:
            await message.channel.send(f"{to_send} Wait until they are finished.")  
        else:
            await message.channel.send(f"{to_send} {this_bot.getBotunlockedInStr()}")

def commandIsAllowed(isLoungeServer: bool, message_author: discord.Member, this_bot: TableBot.ChannelBot, command: str):
    if not isLoungeServer:
        return True

    if common.author_is_table_bot_support_plus(message_author):
        return True

    if this_bot is not None and this_bot.getWar() is not None and (this_bot.prev_command_sw or this_bot.manualWarSetUp):
        return this_bot.getRoom().canModifyTable(message_author.id) #Fixed! Check ALL people who can modify table, not just the person who started it!

    if command not in common.needPermissionCommands:
        return True

    if this_bot is None or not this_bot.is_table_loaded() or this_bot.getRoom().is_freed:
        return True

    #At this point, we know the command's server is Lounge, it's not staff, and a room has been loaded
    return this_bot.getRoom().canModifyTable(message_author.id)