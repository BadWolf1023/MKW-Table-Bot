'''
Created on Jun 12, 2021

@author: willg
'''
import os
from datetime import datetime, timedelta
import numpy as np
import aiohttp
import TableBotExceptions
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

#Raises exception if author is not bad wolf
def is_bad_wolf(self, author):
    if author.id != BAD_WOLF_ID:
        raise TableBotExceptions.NotBadWolf()
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
        
        