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

bot_abuse_tracking = defaultdict(lambda: [0, [], [], 0])
blacklisted_command_count = defaultdict(int)

BOT_ABUSE_REPORT_CHANNEL = None
CLOUDFLARE_REPORT_CHANNEL = None
WHITELIST = { 366774710186278914 }

WARN_MESSAGES_PER_SECOND_RATE = .45
BAN_RATE_MESSAGES_PER_SECOND = .48
MIN_MESSAGES_NEEDED_BEFORE_WARN = 6
MIN_MESSAGES_NEEDED_BEFORE_BAN = 9

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
    if author_id in WHITELIST: return
    bot_abuse_tracking[author_id][0] += 1
    bot_abuse_tracking[author_id][1].append(message.content)
    bot_abuse_tracking[author_id][2].append(datetime.now())
    messages_sent = bot_abuse_tracking[author_id][1]
    if is_hitting_ban_rate(author_id) and bot_abuse_tracking[author_id][3] >= 2: #certain spam and we already warned them
        UserDataProcessing.add_Blacklisted_user(str(author_id), "Automated ban - you spammed the bot. This hurts users everywhere because it slows down the bot for everyone. You can appeal in 1 week to a bot admin or in Bad Wolf's server - to join the server, use the invite code: K937DqM")
        if BOT_ABUSE_REPORT_CHANNEL is not None:
            embed = create_notification_embed(message, messages_sent, ban=True)
            await BOT_ABUSE_REPORT_CHANNEL.send(embed=embed)

        raise TableBotExceptions.BlacklistedUser("blacklisted user")
    if is_hitting_warn_rate(author_id): #potential spam, warn them if we haven't already
        bot_abuse_tracking[author_id][3] += 1
        should_send_abuse_report = bot_abuse_tracking[author_id][3] == 1
        await message.channel.send(f"{message.author.mention} slow down, you're sending too many commands. To avoid getting banned, wait 5 minutes before sending another command.")
        if should_send_abuse_report and BOT_ABUSE_REPORT_CHANNEL:
            embed = create_notification_embed(message, messages_sent, ban=False)
            await BOT_ABUSE_REPORT_CHANNEL.send(embed=embed)

        raise TableBotExceptions.WarnedUser("warned user")

    return True

def create_notification_embed(message: discord.Message, messages_sent, ban):
    send_embed = discord.Embed()
    send_embed.set_author(name=str(message.author) + ' - ' + ('WARNED' if not ban else 'BANNED'), icon_url=message.author.display_avatar.url)
    send_embed.add_field(name='User', value=message.author.mention)
    send_embed.add_field(name='Display Name', value=message.author.display_name)
    send_embed.add_field(name='User ID', value=message.author.id)
    send_embed.add_field(name='Discord Server', value=message.guild)
    send_embed.add_field(name='Server ID', value=message.guild.id)
    send_embed.add_field(name="Trigger Messages", value='\n'.join(messages_sent), inline=False)

    return send_embed

#Raises BlacklistedUser Exception if the author of the message is blacklisted
#Sends a notification once in a while that they are blacklisted
async def blacklisted_user_check(message:discord.Message, notify_threshold=15):
    author_id = message.author.id
    if str(author_id) in UserDataProcessing.blacklisted_Users:
        if blacklisted_command_count[author_id] % notify_threshold == 0:
            await message.channel.send("You have been blacklisted by a bot admin. You are not allowed to use this bot. Reason: " + str(UserDataProcessing.blacklisted_Users[str(author_id)]))
        blacklisted_command_count[author_id] += 1
        raise TableBotExceptions.BlacklistedUser("blacklisted user")
    return True

def set_bot_abuse_report_channel(client):
    global BOT_ABUSE_REPORT_CHANNEL
    global CLOUDFLARE_REPORT_CHANNEL
    BOT_ABUSE_REPORT_CHANNEL = client.get_channel(common.BOT_ABUSE_REPORT_CHANNEL_ID)
    if BOT_ABUSE_REPORT_CHANNEL is None: BOT_ABUSE_REPORT_CHANNEL = client.get_channel(924551533692084264)
    CLOUDFLARE_REPORT_CHANNEL = client.get_channel(common.CLOUD_FLARE_REPORT_CHANNEL_ID)
    
#Every 120 seconds, checks to see if anyone was "spamming" the bot and notifies a private channel in my server
#Of the person(s) who were warned
#Also clears the abuse tracking every 60 seconds
async def check_bot_abuse():
    abuserIDs = set()
    
    for user_id, message_count in bot_abuse_tracking.items():
        if message_count[0] > common.SPAM_THRESHOLD:
            if str(user_id) not in UserDataProcessing.blacklisted_Users:
                abuserIDs.add(str(user_id))
    bot_abuse_tracking.clear()
    