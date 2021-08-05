'''
Created on Aug 5, 2021

@author: willg
'''
import discord
import common
import UserDataProcessing
import UtilityFunctions
import TableBotExceptions

async def abuse_track_check(message:discord.Message):
    await blacklisted_user_check(message)
    
    author_id = message.author.id
    common.bot_abuse_tracking[author_id][0] += 1
    common.bot_abuse_tracking[author_id][1].append(message.content)
    number_of_messages_sent = common.bot_abuse_tracking[author_id][0]
    messages_sent = common.bot_abuse_tracking[author_id][1]
    if number_of_messages_sent == common.WARN_THRESHOLD:
        await message.channel.send(f"{message.author.mention} slow down, you're sending too many commands. To avoid getting banned, wait 5 minutes before sending another command.")
    elif number_of_messages_sent == common.AUTO_BAN_THRESHOLD: #certain spam
        UserDataProcessing.add_Blacklisted_user(str(author_id), "Automated ban - you spammed the bot. This hurts users everywhere because it slows down the bot for everyone. You can appeal in 1 week to a bot admin or in Bad Wolf's server.")
        if common.BOT_ABUSE_REPORT_CHANNEL is not None:
            to_send = f"Automatic ban for spamming bot:\nDiscord: {str(message.author)}\nDiscord ID: {author_id}\nDisplay name: {message.author.display_name}\nDiscord Server: {message.guild}\nDiscord Server ID: {message.guild.id}\nMessages Sent:"
            messages_to_send_back = UtilityFunctions.chunk_join([to_send] + messages_sent)
            for message_to_send in messages_to_send_back:
                common.BOT_ABUSE_REPORT_CHANNEL.send(message_to_send)
        raise TableBotExceptions.BlacklistedUser("blacklisted user")
    return True

#Raises BlacklistedUser Exception if the author of the message is blacklisted
#Sends a notification once in a while that they are blacklisted
async def blacklisted_user_check(message:discord.Message, notify_threshold=15):
    author_id = message.author.id
    if str(author_id) in UserDataProcessing.blacklisted_Users and author_id != common.BAD_WOLF_ID:
        if common.blacklisted_command_count[author_id] % notify_threshold == 0:
            await message.channel.send("You have been blacklisted by a bot admin. You are not allowed to use this bot. Reason: " + str(UserDataProcessing.blacklisted_Users[str(author_id)]), delete_after=10)
        common.blacklisted_command_count[author_id] += 1
        raise TableBotExceptions.BlacklistedUser("blacklisted user")
    return True