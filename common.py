'''
Created on Jun 12, 2021

@author: willg
'''
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
import numpy as np
import aiohttp
import TableBotExceptions
from collections import namedtuple
import discord
from pathlib import Path
import ssl
import certifi
import dill


sslcontext = ssl.create_default_context(cafile=certifi.where())

version = "12.0.0" #Final release from Bad Wolf, stabilizing various things and releasing beta commands

PROPERTIES_FILE = f"properties.json"
properties = json.load(open(PROPERTIES_FILE)) if os.path.exists(PROPERTIES_FILE) else {}

MII_COMMAND_DISABLED = False
MIIS_ON_TABLE_DISABLED = False
ON_WINDOWS = os.name == 'nt'
HREF_HTML_NAME = 'href' if ON_WINDOWS else 'data-href'
TOOLTIP_NAME = "data-tooltip" if ON_WINDOWS else "title"
SAVED_ROOMS_DIR = "testing_rooms/windows/" if ON_WINDOWS else "testing_rooms/linux/"

default_prefix = "?"
MAX_PREFIX_LENGTH = 3

INVITE_LINK = "https://discord.com/api/oauth2/authorize?client_id=735782213118853180&permissions=274878031936&scope=bot"

SCORE_MATRIX = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 8, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 9, 4, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [15, 9, 5, 2, 1, 0, 0, 0, 0, 0, 0, 0],
    [15, 10, 6, 3, 1, 0, 0, 0, 0, 0, 0, 0],
    [15, 10, 7, 5, 3, 1, 0, 0, 0, 0, 0, 0],
    [15, 11, 8, 6, 4, 2, 1, 0, 0, 0, 0, 0],
    [15, 11, 8, 6, 4, 3, 2, 1, 0, 0, 0, 0],
    [15, 12, 10, 8, 6, 4, 3, 2, 1, 0, 0, 0],
    [15, 12, 10, 8, 6, 5, 4, 3, 2, 1, 0, 0],
    [15, 12, 10, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]

CUPLAYOUT_TRACK_IDS = {
  "abandoned boardwalk": 170,
  "abyssal ruins": 201,
  "alpine peak": 59,
  "aquadrom stage": 200,
  "aquania": 169,
  "asdf course": 77,
  "athletic raceway": 183,
  "aura metropolis": 167,
  "autumn leavesway": 146,
  "big express city": 36,
  "big nature city": 244,
  "boshi skatepark": 219,
  "bowser's fiery fortress": 228,
  "calidae desert": 160,
  "camp kartigan": 182,
  "candy coaster": 121,
  "canyon run": 125,
  "castle of darkness": 155,
  "castle of time": 250,
  "cave island": 151,
  "celestial ruins": 44,
  "cherry blossom garden": 204,
  "christmas court": 197,
  "coin heaven": 162,
  "colour circuit": 39,
  "colour wonderland": 50,
  "comet starway": 239,
  "concord town": 35,
  "crystal dungeon": 206,
  "crystal plains": 198,
  "ctr blizzard bluff": 168,
  "ctr cortex castle": 141,
  "ctr n. gin labs": 216,
  "daisy hillside": 60,
  "daisy's palace": 42,
  "dark matter fortress": 211,
  "dark matter shrine": 133,
  "dawn township": 111,
  "delfino island": 110,
  "desert castle raceway": 156,
  "desert fort": 78,
  "desert mushroom ruins": 172,
  "desktop dash": 165,
  "dk ruins": 189,
  "dkr star city": 85,
  "dragon burial grounds": 190,
  "dragonite's island": 247,
  "dreamworld cloudway": 191,
  "ds airship fortress": 91,
  "ds bowser castle": 40,
  "ds cheep cheep beach": 119,
  "ds dk pass": 194,
  "ds figure-8 circuit": 115,
  "ds luigi's mansion": 147,
  "ds mario circuit": 153,
  "ds shroom ridge": 41,
  "ds tick-tock clock": 135,
  "ds waluigi pinball": 102,
  "ds wario stadium": 117,
  "envenom snowstorm": 138,
  "festival town": 243,
  "final grounds": 123,
  "fishdom island": 87,
  "flowery greenhouse": 51,
  "flying kingdom": 74,
  "forest creek": 202,
  "fungal jungle": 231,
  "garden of dreams": 134,
  "gba bowser castle 1": 166,
  "gba bowser castle 2": 233,
  "gba bowser castle 4": 101,
  "gba broken pier": 105,
  "gba cheep cheep island": 112,
  "gba cheese land": 145,
  "gba lakeside park": 185,
  "gba luigi circuit": 184,
  "gba mario circuit": 187,
  "gba peach circuit": 43,
  "gba rainbow road": 48,
  "gba ribbon road": 152,
  "gba riverside park": 33,
  "gba sky garden": 149,
  "gba snow land": 212,
  "gba sunset wilds": 46,
  "gcn baby park": 164,
  "gcn bowser's castle": 100,
  "gcn daisy cruiser": 116,
  "gcn dry dry desert": 32,
  "gcn luigi circuit": 129,
  "gcn mushroom bridge": 213,
  "gcn mushroom city": 173,
  "gcn rainbow road": 88,
  "gcn sherbet land": 139,
  "gcn wario colosseum": 132,
  "gcn yoshi circuit": 106,
  "glimmer express trains": 143,
  "gothic castle": 181,
  "gp mario beach": 224,
  "halogen highway": 49,
  "haunted gardens": 84,
  "headlong skyway": 238,
  "heart of china": 253,
  "hellado mountain": 177,
  "honeybee hideout": 69,
  "icepeak mountain": 227,
  "incendia castle": 81,
  "infernal pipeyard": 144,
  "item fireland": 52,
  "jiyuu village": 248,
  "jungle cliff": 95,
  "jungle glade": 232,
  "jungle jamble": 220,
  "jungle ruins": 140,
  "kartwood creek": 86,
  "kinoko cave": 163,
  "koopa shell pipeland": 254,
  "lava lake": 175,
  "lava road": 218,
  "lost fortress": 37,
  "luigi's island": 222,
  "lunar lights": 93,
  "lunar spaceway": 221,
  "luncheon tour": 108,
  "magmatic sanctuary": 240,
  "mansion of madness": 234,
  "marble towers": 252,
  "mario castle raceway": 73,
  "medieval castlegrounds": 217,
  "melody sanctum": 148,
  "melting magma melee": 122,
  "misty ruins": 157,
  "mushroom island": 186,
  "mushroom peaks": 64,
  "mushroom valley": 38,
  "musical cliff": 154,
  "n64 banshee boardwalk": 104,
  "n64 choco mountain": 103,
  "n64 frappe snowland": 192,
  "n64 kalimari desert": 161,
  "n64 koopa troopa beach": 179,
  "n64 luigi raceway": 47,
  "n64 rainbow road": 57,
  "n64 royal raceway": 89,
  "n64 toad's turnpike": 226,
  "n64 wario stadium": 225,
  "neo koopa city": 136,
  "new moon manor": 126,
  "nightlife party": 96,
  "nivurbia": 150,
  "pianta shore": 61,
  "pinewood path": 63,
  "pipe underworld": 124,
  "piranha plant pipeline": 174,
  "quaking mad cliffs": 109,
  "rainbow road: solar edition": 249,
  "rezway": 171,
  "rock rock ridge": 53,
  "rosalina's snow world": 72,
  "rush city run": 79,
  "sadx twinkle circuit": 230,
  "sahara hideout": 237,
  "sakura sanctuary": 76,
  "sarasa kingdom": 80,
  "sea stadium": 159,
  "shy guy's market": 45,
  "siberian chateau": 34,
  "sinister vault": 208,
  "six king labyrinth": 92,
  "sky grove": 205,
  "sky high island": 215,
  "sky shrine": 75,
  "skyline avenue": 99,
  "slot circuit": 210,
  "snes bowser castle 1": 236,
  "snes bowser castle 2": 68,
  "snes bowser castle 3": 223,
  "snes choco island 2": 113,
  "snes donut plains 2": 94,
  "snes donut plains 3": 131,
  "snes ghost valley 1": 242,
  "snes koopa beach 2": 245,
  "snes mario circuit 1": 71,
  "snes mario circuit 2": 120,
  "snes rainbow road": 137,
  "spectral station": 90,
  "spike desert": 128,
  "star slope": 54,
  "stargaze summit": 158,
  "summer starville": 107,
  "sunset forest": 82,
  "sunset ridge": 178,
  "super marine world": 235,
  "superstar dystopia": 118,
  "suzuka circuit": 193,
  "the rabbit hole": 83,
  "thump bump forest": 199,
  "thwomp swamp": 251,
  "toad raceway": 127,
  "tropical factory": 207,
  "twin peaks": 114,
  "underground sky": 196,
  "undiscovered offlimit": 97,
  "unfinished mario circuit": 180,
  "unnamed valley": 130,
  "vile isle": 214,
  "volcanic valley": 195,
  "volcano canyon": 65,
  "waluigi's motocross": 70,
  "warp pipe island": 188,
  "wetland woods": 209,
  "white garden": 246,
  "windmill village": 203,
  "windy whirl": 229,
  "wolf castlegrounds": 142,
  "wuhu island": 62,
  "wuhu mountain": 176,
  "yoshi lagoon": 98,
  "yoshi's woolly raceway": 241
}

#current_notification = "Help documentation has been changed so you find what you're looking for quickly. Check it out by running `{SERVER_PREFIX}help`. Server administrators now have more table bot defaults they can set for their server."

#Main loop constants
is_dev = properties['mode'] == 'dev'
is_beta = properties['mode'] == 'beta'
is_prod = properties['mode'] == 'prod'

in_testing_server = is_dev
running_beta = is_beta
beta_is_real = False

DISABLE_MKWX_COMMANDS = False
LIMIT_MKWX_COMMANDS = False
STUB_MKWX = False
STUB_MKWX_FILE_NAME = "testing_rooms/mkwx.html"

LIMITED_DONT_INCLUDE_IN_COUNT = {776031312048947230, 826962131592544306, 888089086307475456}#503 server,  testing channel, 503-dup
BAD_WOLFS_CHANNELS = {747290383297282156, 747290363433320539, 739734266199408651}#BW's server TB1, BW's server TB2,BW's server TB3
OTHER_SERVER_CHANNEL_IDS = {747290182096650332,#RT T5, RT T4, RT T3, RT T2, RT T1, CT T4, CT T2, CT T1, 
                       747290167391551509,
                       747290151016857622,
                       747290132675166330,
                       747289647003992078,
                       747290436275535913,
                       739851885665845272,
                       739734249329918083,
                       725870650211827755, #jackie channel #1
                       729305443616161804, #jackie channel #2
                       739264992607731722, #arvin channel #1
                       435836808358789121, #emilP channel #1
                       824713048220368896, #osf channel #1
                       814967280022585374, #Process channel #1
                       583799288317083678, #Process channel #2
                       776487774093443114, #remi channel #1
                       856422278002245646, #chaos channel #1
                       856564700174090310, #chaos channel #2
                       788937681710743562, #lorone channel #1
                       871920891716579348, #lorone channel #2
                       796076771941941279, #Sprixy #1
                       745436799299747881, #Sprixy #2
                       804418977685045298, #Rompe #1
                       769597112731435018, #Rompe #2
                       886901990850977832, #Asuna #1
                       743022435678552064 #Asuna #2
                       } 
LIMITED_CHANNEL_IDS = LIMITED_DONT_INCLUDE_IN_COUNT
LIMITED_SERVER_IDS = None
BETA_CATEGORY_IDS = {744842611998588928, 740659739611889765, 895999567894556672}
SQUAD_QUEUE_CATEGORY_ID = 791199067232272404

current_notification = ""


#TableBot variables, for ChannelBots
inactivity_time_period = timedelta(hours=2, minutes=30)
lounge_inactivity_time_period = timedelta(minutes=8)
inactivity_unlock = timedelta(minutes=30)
wp_cooldown_seconds = 15
mkwx_page_cooldown_seconds = 5

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
MIIS_CACHE_PATH = f"{MIIS_PATH}mii_cache/"
TABLE_HEADERS_PATH = "table_headers/"
DATA_PATH = "tablebot_data/"
LOGGING_PATH = "logging/"
DATA_TRACKING_PATH = "data_tracking/"

ROOM_DATA_TRACKING_DATABASE_FILE = f"{DATA_PATH}room_data_tracking.db"
ROOM_DATA_POPULATE_TIER_TABLE_SQL = f"{DATA_TRACKING_PATH}channel_tiers_addition.sql"
ROOM_DATA_TRACKING_DATABASE_CREATION_SQL = f"{DATA_TRACKING_PATH}room_tracking_db_setup.sql"
ROOM_DATA_TRACKING_DATABASE_MAINTENANCE_SQL = f"{DATA_TRACKING_PATH}database_maintenance.sql"

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
ROOM_DATA_TRACKER_FILE = f"{DATA_PATH}all_room_data.pkl"
SHA_TRACK_NAMES_FILE = f"{DATA_PATH}sha_track_names.pkl"

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
                   VR_IS_ON_FILE,
                   ROOM_DATA_TRACKER_FILE,
                   SHA_TRACK_NAMES_FILE,
                   ROOM_DATA_TRACKING_DATABASE_FILE
                   }

LEFT_ARROW_EMOTE = '\u25c0'
RIGHT_ARROW_EMOTE = '\u25b6'
embed_page_time = timedelta(minutes=2)

base_url_lorenzi = "https://gb.hlorenzi.com/table.png?data="
base_url_edit_table_lorenzi = "https://gb.hlorenzi.com/table?data="

BAD_WOLF_ID = 706120725882470460 
CW_ID = 366774710186278914
ANDREW_ID = 267395889423712258


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
                              BAD_WOLF_SERVER_ADMIN_ID]) #Admin in test server

reporter_plus_roles = set([393600567781621761, #RT Updater
                              520808645252874240, #CT Updater
                              389252697284542465, #RT Reporter
                              520808674411937792 #CT Reporter
                              ]) | mkw_lounge_staff_roles

table_bot_support_plus_roles = reporter_plus_roles | set([748367398905708634])

SHA_ADDERS = [
    683193773055934474, # Fear#1616
]

#Bot Admin information
blacklistedWordsFileIsOpen = False
blackListedWords = set()
botAdminsFileIsOpen = False
botAdmins = set()

#Abuse tracking
BOT_ABUSE_REPORT_CHANNEL_ID = 766272946091851776
CLOUD_FLARE_REPORT_CHANNEL_ID = 888551356238020618
SPAM_THRESHOLD = 13
WARN_THRESHOLD = 13
AUTO_BAN_THRESHOLD = 18


COMMAND_TRIGGER_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def author_has_role_in(message_author, role_ids):
    for role in message_author.roles:
        if role.id in role_ids:
            return True
    return False

def author_is_lounge_staff(message_author):
    return author_has_role_in(message_author, mkw_lounge_staff_roles) or is_bad_wolf(message_author)

def author_is_reporter_plus(message_author):
    return author_has_role_in(message_author, reporter_plus_roles)

def author_is_table_bot_support_plus(message_author):
    return author_has_role_in(message_author, table_bot_support_plus_roles)

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
    if is_dev or is_beta:
        return author.id in {BAD_WOLF_ID, CW_ID, ANDREW_ID}
    else:
        return author.id in {BAD_WOLF_ID, ANDREW_ID}

def is_bot_admin(author):
    return str(author.id) in botAdmins or is_bad_wolf(author)

def is_sha_adder(author):
    return author.id in SHA_ADDERS

def throw_if_not_lounge(guild):
    if guild.id != MKW_LOUNGE_SERVER_ID:
        raise TableBotExceptions.NotLoungeServer()
    return True

def check_create(file_name):
    if not os.path.isfile(file_name):
        f = open(file_name, "w", encoding="utf-8")
        f.close()

    
def full_command_log(message, extra_text=""):
    to_log = f"Server Name: {message.guild} - Server ID: {message.guild.id} - Channel: {message.channel} - Channel ID: {message.channel.id} - User: {message.author} - User ID: {message.author.id} - User Name: {message.author.display_name} - Command: {message.content} {extra_text}"
    return log_text(to_log, FULL_MESSAGE_LOGGING_TYPE)

def log_error(text):
    return log_text(text, logging_type=ERROR_LOGGING_TYPE)

def log_traceback(traceback):
    with open(ERROR_LOGS_FILE, "a+", encoding="utf-8") as f:
        f.write(f"\n{str(datetime.now())}: \n")
        traceback.print_exc(file=f)
    
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
    with open(logging_file, "a+", encoding="utf-8") as f:
        f.write(f"\n{str(datetime.now())}: ")
        try:
            f.write(text)
        except:
            pass
    return text
        
async def download_image(image_url, image_path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, ssl=sslcontext) as resp:
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
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    txt_file = discord.File(file_path, filename=file_name)
    try:
        await message.channel.send(content="My message was too long, so I've attached it as a txt file instead.", file=txt_file)
    except discord.errors.Forbidden:
        await safe_send_missing_permissions(message)
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

def read_sql_file(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return f.read()
    
def dump_pkl(data, file_name, error_message, display_data_on_error=False):
    with open(file_name, "wb") as pickle_out:
        try:
            dill.dump(data, pickle_out)
        except:
            print(error_message)
            if display_data_on_error:
                print(f"Current data: {data}")

def load_pkl(file_name, error_message, default):
    if os.path.exists(file_name):
        with open(file_name, "rb") as pickle_in:
            try:
                return dill.load(pickle_in)
            except:
                print(error_message)
    return default()

async def run_command_async(command:str):
    # print(command)
    proc = await asyncio.create_subprocess_exec(
        *command.split(" "),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    a,b = await proc.communicate()
    # print(a,b)
    
def get_utc_time():
    return datetime.now(timezone.utc)
