'''
Created on Aug 5, 2021
@author: willg
'''

import discord
import common
import UserDataProcessing
import UtilityFunctions
import TableBotExceptions
from collections import defaultdict
from datetime import datetime
import math

bot_abuse_tracking = defaultdict(lambda: [0, [], [], 0])
blacklisted_command_count = defaultdict(int)

BOT_ABUSE_REPORT_CHANNEL = None
ABUSE_WHITELIST = {366774710186278914}

WARN_MESSAGES_PER_SECOND_RATE = .48
BAN_RATE_MESSAGES_PER_SECOND = .5
MIN_MESSAGES_NEEDED_BEFORE_WARN = 6
MIN_MESSAGES_NEEDED_BEFORE_BAN = 8

def is_hitting_warn_rate(author_id):
    num_messages_sent = len(bot_abuse_tracking[author_id][1])
    total_message_span = bot_abuse_tracking[author_id][2][-1] - bot_abuse_tracking[author_id][2][0]
    
    if num_messages_sent < MIN_MESSAGES_NEEDED_BEFORE_WARN:
        return False
    
    rate_of_messages = num_messages_sent / total_message_span.total_seconds()
    
    return rate_of_messages > WARN_MESSAGES_PER_SECOND_RATE
        

def is_hitting_ban_rate(author_id):
    num_messages_sent = len(bot_abuse_tracking[author_id][1])
    total_message_span = bot_abuse_tracking[author_id][2][-1] - bot_abuse_tracking[author_id][2][0]
    
    if num_messages_sent < MIN_MESSAGES_NEEDED_BEFORE_BAN:
        return False
    
    rate_of_messages = num_messages_sent / total_message_span.total_seconds()
    return rate_of_messages > BAN_RATE_MESSAGES_PER_SECOND
    

async def abuse_track_check(message:discord.Message):
    author_id = message.author.id
    # if author_id in ABUSE_WHITELIST or (common.is_dev and author_id==common.properties['dev_id']): return False
    bot_abuse_tracking[author_id][0] += 1
    bot_abuse_tracking[author_id][1].append(message.content)
    bot_abuse_tracking[author_id][2].append(datetime.now())
    messages_sent = bot_abuse_tracking[author_id][1]
    warn = False

    if is_hitting_warn_rate(author_id) and bot_abuse_tracking[author_id][3] < 2: #potential spam, warn them if we haven't already
        bot_abuse_tracking[author_id][3] += 1
        warn = True
        should_send_abuse_report = bot_abuse_tracking[author_id][3] == 1
        await message.channel.send(f"{message.author.mention} slow down, you're sending too many commands. To avoid getting banned, wait 1 minute before sending another command.")
        if should_send_abuse_report and BOT_ABUSE_REPORT_CHANNEL:
            embed = create_notification_embed(message, messages_sent, ban=False)
            await BOT_ABUSE_REPORT_CHANNEL.send(embed=embed)

        # raise TableBotExceptions.WarnedUser("warned user")

    if is_hitting_ban_rate(author_id) and bot_abuse_tracking[author_id][3] >= 2: #certain spam and we already warned them
        UserDataProcessing.add_Blacklisted_user(str(author_id), f"Automated ban - you spammed the bot. This hurts users everywhere because it slows down the bot for everyone. You can appeal in 1 week to a bot admin or in Bad Wolf's server - to join the server, use the invite code: {common.TABLEBOT_SERVER_INVITE_CODE}")
        await message.channel.send(f"{message.author.mention}, you've been banned for spamming the bot. You can appeal in 1 week to a bot admin or in Bad Wolf's server - to join the server, use the invite code: {common.TABLEBOT_SERVER_INVITE_CODE}")
        if BOT_ABUSE_REPORT_CHANNEL is not None:
            embed = create_notification_embed(message, messages_sent, ban=True)
            await BOT_ABUSE_REPORT_CHANNEL.send(embed=embed)

        # raise TableBotExceptions.BlacklistedUser("blacklisted user")
        return True

    return warn

def create_notification_embed(message: discord.Message, messages_sent, ban):
    send_embed = discord.Embed()

    try:
        send_embed.set_author(name=str(message.author) + ' - ' + ('WARNED' if not ban else 'BANNED'),
                              icon_url=message.author.display_avatar.url)
    except:
        send_embed.set_author(name=str(message.author) + ' - ' + ('WARNED' if not ban else 'BANNED'),
                              icon_url=message.author.avatar.url)

    send_embed.add_field(name='User', value=message.author.mention)
    send_embed.add_field(name='Display Name', value=message.author.display_name)
    send_embed.add_field(name='User ID', value=message.author.id)
    send_embed.add_field(name='Discord Server', value=message.guild)
    send_embed.add_field(name='Server ID', value=message.guild.id)
    
    #checks to see how many remaining characters are available (embeds have max 6000 characters and fields have 1024 max)
    chars_before_messages = len(f"{message.author} - WARNED{message.author.mention}{message.author.display_name}{message.author.id}{message.guild}{message.guild.id}")+75
    allowed_message_chars = 6000-chars_before_messages
    allowed_iters = math.ceil((allowed_message_chars)/1024)
    last_len = allowed_message_chars-(allowed_iters*1024)
    messages_sent = '\n'.join(messages_sent)

    message_list = list(UtilityFunctions.string_chunks(messages_sent, 1024))
    for ind in range(min(allowed_iters, len(message_list))):
        mes = message_list[ind]
        val = mes[:last_len] if ind == allowed_iters-1 else mes
        send_embed.add_field(name="Trigger Messages" if ind==0 else '\u200b', value=val, inline=False)

    return send_embed

#Raises BlacklistedUser Exception if the author of the message is blacklisted
#Sends a notification once in a while that they are blacklisted
async def blacklisted_user_check(message:discord.Message, notify_threshold=15):
    author_id = message.author.id
    if str(author_id) in UserDataProcessing.blacklisted_users:
        if blacklisted_command_count[author_id] % notify_threshold == 0:
            await message.channel.send("You have been blacklisted by a bot admin. You are not allowed to use this bot. Reason: " + str(UserDataProcessing.blacklisted_users[str(author_id)]))
        blacklisted_command_count[author_id] += 1
        raise TableBotExceptions.BlacklistedUser("blacklisted user")
    return True

def set_bot_abuse_report_channel(client):
    global BOT_ABUSE_REPORT_CHANNEL
    BOT_ABUSE_REPORT_CHANNEL = client.get_channel(common.BOT_ABUSE_REPORT_CHANNEL_ID)
    
#Every 120 seconds, checks to see if anyone was "spamming" the bot and notifies a private channel in my server
#Of the person(s) who were warned
#Also clears the abuse tracking every 60 seconds
async def check_bot_abuse():
    abuserIDs = set()
    
    for user_id, message_count in bot_abuse_tracking.items():
        if message_count[0] > common.SPAM_THRESHOLD:
            if str(user_id) not in UserDataProcessing.blacklisted_users:
                abuserIDs.add(str(user_id))
    bot_abuse_tracking.clear()
    