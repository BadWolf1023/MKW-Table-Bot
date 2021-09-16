'''
Created on Jun 12, 2021

@author: willg
'''
import os
from datetime import datetime, timedelta
import numpy as np
import aiohttp
import TableBotExceptions
from collections import namedtuple
import discord
from pathlib import Path

version = "11.3.0"

MIIS_DISABLED = True

default_prefix = "?"
MAX_PREFIX_LENGTH = 3


#Main loop constants
in_testing_server = True
running_beta = False

DISABLE_MKWX_COMMANDS = True

#RT T5, RT T4, RT T3, RT T2, RT T1, CT T4, CT T2, CT T1, 503 server, BW's server TB1, BW's server TB2, testing channel, Beta Testing 1, Beta testing 2, Beta Testing 3
LIMITED_CHANNEL_IDS = {747290182096650332, 747290167391551509, 747290151016857622, 747290132675166330, 747289647003992078, 747290436275535913, 747290383297282156, 747290363433320539, 776031312048947230, 739851885665845272, 739734249329918083, 826962131592544306, 860645585143857213, 860645644804292608, 863242314461085716}
LIMITED_SERVER_IDS = None

current_notification = f"Command cooldowns have increased, and miis have been disabled to ensure Table Bot doesn't access the website too much. **Accessing mkwx is experimental at this time.** Additionally, Table Bot only works in {len(LIMITED_CHANNEL_IDS) - 5} selected channels, 8 of which are in Lounge, and 2 in Bad Wolf's server. Thanks for understanding."


#TableBot variables, for ChannelBots
inactivity_time_period = timedelta(hours=2, minutes=30)
lounge_inactivity_time_period = timedelta(minutes=8)
inactivity_unlock = timedelta(minutes=30)
wp_cooldown_seconds = 60
rl_cooldown_seconds = 60

#Mii folder location information
MII_TABLE_PICTURE_PREFIX = "table_"

#Mii for footer constants
DEFAULT_FOOTER_COLOR = np.array([23, 22, 18], dtype=np.uint8)
#Size of mii pictures on table
MII_SIZE_FOR_TABLE = 81

#Other variables
LORENZI_FLAG_PAGE_URL = "https://gb.hlorenzi.com/help/flags"
LORENZI_FLAG_PAGE_URL_NO_PREVIEW = f"<{LORENZI_FLAG_PAGE_URL}>"

#Various folder paths
SERVER_SETTINGS_PATH = "discord_server_settings/"
FLAG_IMAGES_PATH = "flag_images/"
FONT_PATH = "fonts/"
HELP_PATH = "help/"
TABLING_HELP_PATH = f"{HELP_PATH}tabling/"
MIIS_PATH = "miis/"
TABLE_HEADERS_PATH = "table_headers/"
DATA_PATH = "tablebot_data/"
LOGGING_PATH = "logging/"

LOUNGE_ID_COUNTER_FILE = f"{DATA_PATH}lounge_counter.pkl"
LOUNGE_TABLE_UPDATES_FILE = f"{DATA_PATH}lounge_table_update_ids.pkl"
BAD_WOLF_FACT_FILE = f"{DATA_PATH}bad_wolf_facts.pkl"
CTGP_REGION_FILE = f"{DATA_PATH}CTGP_Region_File.pkl"
BADWOLF_PICTURE_FILE = f'{DATA_PATH}BadWolf.jpg'

BLACKLISTED_USERS_FILE = f"{DATA_PATH}blacklisted_users.txt"
FC_DISCORD_ID_FILE = f"{DATA_PATH}discord_id_FCS.txt"
DISCORD_ID_LOUNGES_FILE = f"{DATA_PATH}discord_id_lounges.txt"
DISCORD_ID_FLAGS_FILE = f"{DATA_PATH}discord_id_flags.txt"
FLAG_CODES_FILE = f"{DATA_PATH}flag_codes.txt"
FLAG_EXCEPTION_FILE = f"{DATA_PATH}flag_exceptions.txt"

PRIVATE_INFO_FILE = f'{DATA_PATH}private.txt'
STATS_FILE = f"{DATA_PATH}stats.txt"

TABLE_BOT_PKL_FILE = f'{DATA_PATH}tablebots.pkl'
VR_IS_ON_FILE = f"{DATA_PATH}vr_is_on.pkl"

BLACKLISTED_WORDS_FILE = f"{DATA_PATH}blacklisted_words.txt"
BOT_ADMINS_FILE = f"{DATA_PATH}bot_admins.txt"


ERROR_LOGS_FILE = f"{LOGGING_PATH}error_logs.txt"

FEEDBACK_LOGS_FILE = f"{LOGGING_PATH}feedback_logs.txt"

#To be clear (and you can check the main loop that this is true), table bot does not log all messages
#It only logs commands that are sent to it
MESSAGE_LOGGING_FILE = f"{LOGGING_PATH}messages_logging.txt"

FULL_LOGGING_FILE_NAME = "full_logging"
FULL_MESSAGE_LOGGING_FILE = f"{LOGGING_PATH}/{FULL_LOGGING_FILE_NAME}.txt"

WHO_IS_LIMIT = 100


DEFAULT_LARGE_TIME_FILE = f"{SERVER_SETTINGS_PATH}server_large_time_defaults.txt"
DEFAULT_PREFIX_FILE = f"{SERVER_SETTINGS_PATH}server_prefixes.txt"
DEFAULT_TABLE_THEME_FILE_NAME = f"{SERVER_SETTINGS_PATH}server_table_themes.txt"
DEFAULT_GRAPH_FILE = f"{SERVER_SETTINGS_PATH}server_graphs.txt"
DEFAULT_MII_FILE = f"{SERVER_SETTINGS_PATH}server_mii_defaults.txt"

ERROR_LOGGING_TYPE = "error"
MESSAGE_LOGGING_TYPE = "messagelogging"
FEEDBACK_LOGGING_TYPE = "feedback"
FULL_MESSAGE_LOGGING_TYPE = "fullmessagelogging"

ALL_PATHS = {LOGGING_PATH, SERVER_SETTINGS_PATH, DATA_PATH}

FILES_TO_BACKUP = {ERROR_LOGS_FILE,
                   FEEDBACK_LOGS_FILE,
                   MESSAGE_LOGGING_FILE,
                   FULL_MESSAGE_LOGGING_FILE,
                   DEFAULT_LARGE_TIME_FILE,
                   DEFAULT_PREFIX_FILE,
                   DEFAULT_TABLE_THEME_FILE_NAME,
                   DEFAULT_GRAPH_FILE,
                   DEFAULT_MII_FILE,
                   BAD_WOLF_FACT_FILE,
                   BLACKLISTED_USERS_FILE,
                   BLACKLISTED_WORDS_FILE,
                   BOT_ADMINS_FILE,
                   CTGP_REGION_FILE,
                   FC_DISCORD_ID_FILE,
                   DISCORD_ID_FLAGS_FILE,
                   DISCORD_ID_LOUNGES_FILE,
                   FLAG_EXCEPTION_FILE,
                   LOUNGE_ID_COUNTER_FILE,
                   LOUNGE_TABLE_UPDATES_FILE,
                   STATS_FILE,
                   TABLE_BOT_PKL_FILE,
                   VR_IS_ON_FILE
                   }

LEFT_ARROW_EMOTE = '\u25c0'
RIGHT_ARROW_EMOTE = '\u25b6'
embed_page_time = timedelta(minutes=2)

base_url_lorenzi = "https://gb.hlorenzi.com/table.png?data="
base_url_edit_table_lorenzi = "https://gb.hlorenzi.com/table?data="

BAD_WOLF_ID = 706120725882470460



#Lounge stuff
MKW_LOUNGE_RT_UPDATE_PREVIEW_LINK = "https://www.mkwlounge.gg/ladder/tabler.php?ladder_id=1&event_data="
MKW_LOUNGE_CT_UPDATE_PREVIEW_LINK = "https://www.mkwlounge.gg/ladder/tabler.php?ladder_id=2&event_data="
MKW_LOUNGE_RT_UPDATER_LINK = MKW_LOUNGE_RT_UPDATE_PREVIEW_LINK
MKW_LOUNGE_CT_UPDATER_LINK = MKW_LOUNGE_CT_UPDATE_PREVIEW_LINK
MKW_LOUNGE_RT_UPDATER_CHANNEL = 758161201682841610
MKW_LOUNGE_CT_UPDATER_CHANNEL = 758161224202059847
MKW_LOUNGE_SERVER_ID = 387347467332485122

BAD_WOLF_SERVER_ID = 739733336871665696
BAD_WOLF_SERVER_TESTER_ID = 740575809713995776
BAD_WOLF_SERVER_ADMIN_ID = 740659173695553667
BAD_WOLF_SERVER_EVERYONE_ROLE_ID = 739733336871665696
BAD_WOLF_SERVER_BETA_TESTING_ONE_CHANNEL_ID = 860645585143857213
BAD_WOLF_SERVER_BETA_TESTING_TWO_CHANNEL_ID = 860645644804292608
BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID = 863242314461085716
BAD_WOLF_SERVER_STAFF_ROLES = set([BAD_WOLF_SERVER_TESTER_ID, BAD_WOLF_SERVER_ADMIN_ID])
BAD_WOLF_SERVER_NORMAL_TESTING_ONE_CHANNEL_ID = 861453709305315349
BAD_WOLF_SERVER_NORMAL_TESTING_TWO_CHANNEL_ID = 863234379718721546
BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID = 863238405269749760

#Rather than using the builtin set declaration {}, I did an iterable because BadWolfBot.py kept giving an error in Eclipse, even though everything ran fine - this seems to have suppressed the error which was giving me major OCD
mkw_lounge_staff_roles = set([387347888935534593, #Boss
                              792805904047276032, #CT Admin
                              399382503825211393, #HT RT Arb
                              399384750923579392, #LT RT Arb
                              521149807994208295, #HT CT Arb
                              792891432301625364, #LT CT Arb
                              521154917675827221, #Developer Access
                              740659173695553667]) #Admin in test server

reporter_plus_roles = set([393600567781621761, #RT Updater
                              520808645252874240, #CT Updater
                              389252697284542465, #RT Reporter
                              520808674411937792 #CT Reporter
                              ]) | mkw_lounge_staff_roles

table_bot_support_plus_roles = reporter_plus_roles | set([748367398905708634])
                              



#Bot Admin information
blacklistedWordsFileIsOpen = False
blackListedWords = set()
botAdminsFileIsOpen = False
botAdmins = set()

#Abuse tracking
BOT_ABUSE_REPORT_CHANNEL_ID = 766272946091851776
SPAM_THRESHOLD = 13
WARN_THRESHOLD = 13
AUTO_BAN_THRESHOLD = 18


COMMAND_TRIGGER_CHARS = set(c for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")



def author_has_id_in(message_author, role_ids):
    for role in message_author.roles:
        if role.id in role_ids:
            return True
    return False

def author_is_lounge_staff(message_author):
    return author_has_id_in(message_author, mkw_lounge_staff_roles)

def author_is_reporter_plus(message_author):
    return author_has_id_in(message_author, reporter_plus_roles)

def author_is_table_bot_support_plus(message_author):
    return author_has_id_in(message_author, table_bot_support_plus_roles)

def main_lounge_can_report_table(message_author):
    return author_is_reporter_plus(message_author) or message_author.id == BAD_WOLF_ID


LoungeUpdateChannels = namedtuple('LoungeUpdateChannels', ['updater_channel_id_primary', 'updater_link_primary', 'preview_link_primary', 'type_text_primary',
                                                         'updater_channel_id_secondary', 'updater_link_secondary', 'preview_link_secondary', 'type_text_secondary'])

TESTING_SERVER_LOUNGE_UPDATES = LoungeUpdateChannels(
    updater_channel_id_primary=BAD_WOLF_SERVER_NORMAL_TESTING_TWO_CHANNEL_ID,
    updater_link_primary=MKW_LOUNGE_RT_UPDATER_LINK,
    preview_link_primary=MKW_LOUNGE_RT_UPDATE_PREVIEW_LINK,
    type_text_primary="RT",
    updater_channel_id_secondary=BAD_WOLF_SERVER_NORMAL_TESTING_TWO_CHANNEL_ID,
    updater_link_secondary=MKW_LOUNGE_CT_UPDATER_LINK,
    preview_link_secondary=MKW_LOUNGE_CT_UPDATE_PREVIEW_LINK,
    type_text_secondary="CT")

lounge_channel_mappings = {MKW_LOUNGE_SERVER_ID:LoungeUpdateChannels(
    updater_channel_id_primary=MKW_LOUNGE_RT_UPDATER_CHANNEL,
    updater_link_primary=MKW_LOUNGE_RT_UPDATER_LINK,
    preview_link_primary=MKW_LOUNGE_RT_UPDATE_PREVIEW_LINK,
    type_text_primary="RT",
    updater_channel_id_secondary=MKW_LOUNGE_CT_UPDATER_CHANNEL,
    updater_link_secondary=MKW_LOUNGE_CT_UPDATER_LINK,
    preview_link_secondary=MKW_LOUNGE_CT_UPDATE_PREVIEW_LINK,
    type_text_secondary="CT"),
    
    BAD_WOLF_SERVER_ID:LoungeUpdateChannels(
    updater_channel_id_primary=BAD_WOLF_SERVER_BETA_TESTING_TWO_CHANNEL_ID,
    updater_link_primary=MKW_LOUNGE_RT_UPDATER_LINK,
    preview_link_primary=MKW_LOUNGE_RT_UPDATE_PREVIEW_LINK,
    type_text_primary="RT",
    updater_channel_id_secondary=BAD_WOLF_SERVER_BETA_TESTING_TWO_CHANNEL_ID,
    updater_link_secondary=MKW_LOUNGE_CT_UPDATER_LINK,
    preview_link_secondary=MKW_LOUNGE_CT_UPDATE_PREVIEW_LINK,
    type_text_secondary="CT")
    }



def is_bad_wolf(author):
    return author.id == BAD_WOLF_ID

def is_bot_admin(author):
    return str(author.id) in botAdmins or is_bad_wolf(author)

def throw_if_not_lounge(guild):
    if guild.id != MKW_LOUNGE_SERVER_ID:
        raise TableBotExceptions.NotLoungeServer()
    return True

def check_create(file_name):
    if not os.path.isfile(file_name):
        f = open(file_name, "w")
        f.close()

    
def full_command_log(message, extra_text=""):
    to_log = f"Server Name: {message.guild} ({len(message.guild.members)} members)- Server ID: {message.guild.id} - Channel: {message.channel} - Channel ID: {message.channel.id} - User: {message.author} - User ID: {message.author.id} - User Name: {message.author.display_name} - Command: {message.content} {extra_text}"
    return log_text(to_log, FULL_MESSAGE_LOGGING_TYPE)
    
def log_text(text, logging_type=MESSAGE_LOGGING_TYPE):
    logging_file = MESSAGE_LOGGING_FILE
    if logging_type == ERROR_LOGGING_TYPE:
        logging_file = ERROR_LOGS_FILE
    if logging_type == FEEDBACK_LOGGING_TYPE:
        logging_file = FEEDBACK_LOGS_FILE
    if logging_type == MESSAGE_LOGGING_TYPE:
        logging_file = MESSAGE_LOGGING_FILE
    if logging_type == FULL_MESSAGE_LOGGING_TYPE:
        logging_file = FULL_MESSAGE_LOGGING_FILE
        
    check_create(logging_file)
    with open(logging_file, "a+") as f:
        f.write(f"\n{str(datetime.now())}: ")
        try:
            f.write(text)
        except:
            pass
    return text
        
async def download_image(image_url, image_path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    with open(image_path, mode='wb+') as f:
                        f.write(await resp.read())
                        return True
    except:
        pass
    return False






async def safe_send_missing_permissions(message:discord.Message, delete_after=None):
    try:
        await message.channel.send("I'm missing permissions. Contact your admins.", delete_after=delete_after)
    except discord.errors.Forbidden: #We can't send messages
        pass
    
async def safe_send_file(message:discord.Message, content):
    file_name = str(message.id) + ".txt"
    Path('./attachments').mkdir(parents=True, exist_ok=True)
    file_path = "./attachments/" + file_name
    with open(file_path, "w") as f:
        f.write(content)
        
    txt_file = discord.File(file_path, filename=file_name)
    try:
        await message.channel.send(content="My message was too long, so I've attached it as a txt file instead.", file=txt_file)
    except discord.errors.Forbidden:
        safe_send_missing_permissions(message)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


#Won't throw exceptions if we're missing permissions, it's "safe"
async def safe_send(message:discord.Message, content=None, embed=None, delete_after=None):
    if content is not None and len(content) > 1998:
        await safe_send_file(message, content)
        return

    try:
        await message.channel.send(content=content, embed=embed, delete_after=delete_after)
    except discord.errors.Forbidden: #Missing permissions
        await safe_send_missing_permissions(message, delete_after=10)

  
#Function only for testing purposes. Do not use this in the main program code.
def run_async_function_no_loop(function_to_call):
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(function_to_call)
    
async def safe_delete(message):
    try:
        await message.delete()
    except discord.errors.NotFound:
        pass
    