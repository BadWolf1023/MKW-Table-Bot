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

MIIS_DISABLED = False

default_prefix = "?"

current_notification = "Help documentation has been changed so you find what you're looking for quickly. Check it out by running `?help_documentation`. Server administrators have more table bot defaults they can set for their server."

#Main loop constants
in_testing_server = True

#TableBot variables, for ChannelBots
inactivity_time_period = timedelta(hours=2, minutes=30)
lounge_inactivity_time_period = timedelta(minutes=8)
inactivity_unlock = timedelta(minutes=30)
wp_cooldown_seconds = 15
rl_cooldown_seconds = 10

#Mii folder location information
MII_TABLE_PICTURE_PREFIX = "table_"

#Mii for footer constants
DEFAULT_FOOTER_COLOR = np.array([23, 22, 18], dtype=np.uint8)
#Size of mii pictures on table
MII_SIZE_FOR_TABLE = 81

#Other variables
LORENZI_FLAG_PAGE_URL = "https://gb.hlorenzi.com/help_documentation/flags"
LORENZI_FLAG_PAGE_URL_NO_PREVIEW = f"<{LORENZI_FLAG_PAGE_URL}>"

#Various folder paths
SERVER_SETTINGS_PATH = "discord_server_settings/"
FLAG_IMAGES_PATH = "flag_images/"
FONT_PATH = "fonts/"
HELP_PATH = "help_documentation/"
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


DEFAULT_LARGE_TIME_FILE = f"{SERVER_SETTINGS_PATH}server_large_time_defaults.txt"
DEFAULT_PREFIX_FILE = f"{SERVER_SETTINGS_PATH}server_prefixes.txt"
DEFAULT_TABLE_THEME_FILE_NAME = f"{SERVER_SETTINGS_PATH}server_table_themes.txt"
DEFAULT_GRAPH_FILE = f"{SERVER_SETTINGS_PATH}server_graphs.txt"
DEFAULT_MII_FILE = f"{SERVER_SETTINGS_PATH}server_mii_defaults.txt"

ERROR_LOGGING_TYPE = "error"
MESSAGE_LOGGING_TYPE = "messagelogging"
FEEDBACK_LOGGING_TYPE = "feedback"

FILES_TO_BACKUP = {ERROR_LOGS_FILE,
                   FEEDBACK_LOGS_FILE,
                   MESSAGE_LOGGING_FILE,
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
RT_UPDATE_PREVIEW_LINK = "https://mariokartboards.com/lounge/ladder/tabler.php?type=rt&import="
CT_UPDATE_PREVIEW_LINK = "https://mariokartboards.com/lounge/ladder/tabler.php?type=ct&import="
RT_UPDATER_LINK = "https://www.mariokartboards.com/lounge/admin/rt/?import="
CT_UPDATER_LINK = "https://www.mariokartboards.com/lounge/admin/ct/?import="
RT_UPDATER_CHANNEL = 758161201682841610
CT_UPDATER_CHANNEL = 758161224202059847
RT_REPORTER_ID = 389252697284542465
RT_UPDATER_ID = 393600567781621761
CT_REPORTER_ID = 520808674411937792
CT_UPDATER_ID = 520808645252874240
lounge_server_id = 387347467332485122
#in order: Boss, Higher Tier Arb, Lower Tier Arb, Higher Tier CT Arb, Lower Tier CT Arb, RT Updater, CT Updater, RT Reporter, CT Reporter, Developer
lounge_staff_roles = {387347888935534593, 399382503825211393, 399384750923579392, 521149807994208295, 792891432301625364,
                      393600567781621761, 520808645252874240, 389252697284542465, 520808674411937792,
                      521154917675827221, 748367398905708634, 748367393264238663}


def author_is_lounge_staff(message_author):
    for role in message_author.roles:
        if role.id in lounge_staff_roles:
            return True
    return False

def main_lounge_can_report_table(message_author):
    return author_is_lounge_staff(message_author) or message_author.id == BAD_WOLF_ID


LoungeUpdateChannels = namedtuple('LoungeUpdateChannels', ['updater_channel_id_primary', 'updater_link_primary', 'preview_link_primary', 'type_text_primary',
                                                           'updater_channel_id_secondary', 'updater_link_secondary', 'preview_link_secondary', 'type_text_secondary'])
lounge_channel_mappings = {lounge_server_id:LoungeUpdateChannels(
    updater_channel_id_primary=RT_UPDATER_CHANNEL,
    updater_link_primary=RT_UPDATER_LINK,
    preview_link_primary=RT_UPDATE_PREVIEW_LINK,
    type_text_primary="RT",
    updater_channel_id_secondary=CT_UPDATER_CHANNEL,
    updater_link_secondary=CT_UPDATER_LINK,
    preview_link_secondary=CT_UPDATE_PREVIEW_LINK,
    type_text_secondary="CT")
    }



def is_bad_wolf(author):
    return author.id == BAD_WOLF_ID

def throw_if_not_lounge(guild):
    if guild.id != lounge_server_id:
        raise TableBotExceptions.NotLoungeServer()
    return True

def check_create(file_name):
    if not os.path.isfile(file_name):
        f = open(file_name, "w")
        f.close()

def log_text(text, logging_type=MESSAGE_LOGGING_TYPE):
    logging_file = MESSAGE_LOGGING_FILE
    if logging_type == ERROR_LOGGING_TYPE:
        logging_file = ERROR_LOGS_FILE
    if logging_type == FEEDBACK_LOGGING_TYPE:
        logging_file = FEEDBACK_LOGS_FILE
    if logging_type == MESSAGE_LOGGING_TYPE:
        logging_file = MESSAGE_LOGGING_FILE
        
    check_create(logging_file)
    with open(logging_file, "a+") as f:
        f.write(f"\n{str(datetime.now())}: ")
        try:
            f.write(text)
        except:
            pass
        
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
    if content != None and len(content) > 1998:
        await safe_send_file(message, content)
        return

    try:
        await message.channel.send(content=content, embed=embed, delete_after=delete_after)
    except discord.errors.Forbidden: #Missing permissions
        await safe_send_missing_permissions(message, delete_after=10)
        
        