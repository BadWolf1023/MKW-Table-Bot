#Bot internal imports - stuff I coded
import ServerFunctions
import ImageCombine
import War
from TagAI import getTagsSmart, getTagSmart
import Stats
import LoungeAPIFunctions
import ScoreKeeper as SK
import UserDataProcessing
from UserDataProcessing import lounge_add
import TableBot
import UtilityFunctions
import Race
import MogiUpdate
import help_documentation
import commands
from common import *
import TableBotExceptions



#External library imports - stuff other smart people coded
import urllib.parse
import discord
from discord.ext import tasks
import itertools
import traceback
import copy
import sys
import atexit
import signal
from collections import defaultdict
import dill as p
import psutil
import gc
import subprocess
import random
from bs4 import NavigableString
from pathlib import Path
from typing import List


finished_on_ready = False



CT_WAR_LOUNGE_ECHELONS_CAT_ID = 851666104228249652
WAR_LOUNGE_ECHELONS_CAT_ID = 751956338912788559
WAR_LOUNGE_COMP_DISC_CAT_ID = 751956337612685405
LOUNGE_ECHELONS_CAT_ID = 389250562836922378
LOUNGE_ECHELONS_CT_CAT_ID = 520790337443332104
LOUNGE_COMP_DISC_ID = 455763458483421194
TEMPORARY_VR_CATEGORIES = [LOUNGE_COMP_DISC_ID, LOUNGE_ECHELONS_CAT_ID, LOUNGE_ECHELONS_CT_CAT_ID, WAR_LOUNGE_COMP_DISC_CAT_ID, WAR_LOUNGE_ECHELONS_CAT_ID, CT_WAR_LOUNGE_ECHELONS_CAT_ID]


blacklisted_command_count = defaultdict(int)
bot_abuse_tracking = defaultdict(int)
BOT_ABUSE_REPORT_CHANNEL_ID = 766272946091851776
SPAM_THRESHOLD = 13
WARN_THRESHOLD = 13
AUTO_BAN_THRESHOLD = 18


class Error(Exception):
    """Base class"""
    pass

class RoomMissingException(Error):
    def __init__(self):
        pass
    
    



badwolf_id = 706120725882470460
testing_bot_key = None
real_bot_key = None
bot_invite_link = "https://discord.com/api/oauth2/authorize?client_id=735782213118853180&permissions=116800&scope=bot"

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

#These commands modify the table
RESET_TERMS = {"reset", "restart", "cancel", "quit", "stop", "clear"}
START_WAR_TERMS = {"startwar", "sw"}
UNDO_TERMS = {"undo", "undocommand", "reverse"}

#These commands also modify the table, but can be undone using the ?undo command
REMOVE_RACE_TERMS = {"removerace"}
PLAYER_PENALTY_TERMS = {"pen", "penalty"}
TEAM_PENALTY_TERMS = {"teampen", "teampenalty"}
EDIT_PLAYER_SCORE_TERMS = {"edit"}
PLAYER_DISCONNECT_TERMS = {"dc", "dcs"}
MERGE_ROOM_TERMS = {"mr", "mergeroom"}
SET_WAR_NAME_TERMS = {"setwarname"}
CHANGE_PLAYER_NAME_TERMS = {'changename'}
CHANGE_PLAYER_TAG_TERMS = {'assignteam', 'changeteam', 'assigntag', 'changetag', 'setteam', 'settag'}
CHANGE_ROOM_SIZE_TERMS = {'changeroomsize', "editroomsize", "forceroomsize"}
EARLY_DC_TERMS = {'earlydc'}
QUICK_EDIT_TERMS = {'quickedit', 'qe'}
TABLE_THEME_TERMS = {'style', 'theme', 'tablestyle', 'tabletheme'}
GRAPH_TERMS = {'graph', 'tablegraph', 'graphtheme'}
DISPLAY_GP_SIZE_TERMS = {'size', 'tablesize', 'displaysize'}



#Commands that require a war to be started, but don't modify the war/room/table in any way
TABLE_TEXT_TERMS = {"tt", "tabletext"}
WAR_PICTURE_TERMS = {"wp", "warpicture"}
RACE_RESULTS_TERMS = {"rr", "raceresults"}
RACES_TERMS = {"races"}
RXX_TERMS = {"rxx", "rlid"}
ALL_PLAYERS_TERMS = {"allplayers", "ap"}
FCS_TERMS = {"fcs"}
CURRENT_ROOM_TERMS = {"currentroom"}


#General commands that do not require a war to be started (stateless commands)
FC_TERMS = {"fc"}
LOUNGE_NAME_TERMS = {"lounge", "loungename", "ln"}
GET_FLAG_TERMS = {"getflag", "gf"}
SET_FLAG_TERMS = {"setflag", "sf"}
MII_TERMS = {"mii"}
WORLDWIDE_TERMS = {"wws", "ww", "rtww", "rtwws", "worldwide", "worldwides"}
CTWW_TERMS = {"ctgpww", "ctgpwws", "ctwws", "ctww", "ctww", "ctwws", "ctworldwide", "ctworldwides", "customtrackworldwide", "customtrackworldwides"}
BATTLES_TERMS = {"bts", "battle", "battles", "btww", "btwws", "battleww", "battlewws", "battleworldwide", "battleworldwides"}
VERIFY_ROOM_TERMS = {"vr", "verifyroom"}
STATS_TERMS = {"stats", "stat"}
INVITE_TERMS = {"invite"}
LOG_TERMS = {"log"}

#Informative, getting started/tutorial commands
QUICK_START_TERMS = {"quickstart"}
TUTORIAL_TERMS = {"tutorial"}
HELP_TERMS = {"help"}
 
#Lounge table submission commands
LOUNGE_RT_MOGI_UPDATE_TERMS = {'rtmogiupdate', 'rttableupdate', 'rtupdatemogi', 'rtupdate'}
LOUNGE_CT_MOGI_UPDATE_TERMS = {'ctmogiupdate', 'cttableupdate', 'ctupdatemogi', 'ctupdate'}
LOUNGE_MOGI_UPDATE_TERMS = LOUNGE_RT_MOGI_UPDATE_TERMS | LOUNGE_CT_MOGI_UPDATE_TERMS

#Lounge staff commands for table submissions
LOUNGE_TABLE_SUBMISSION_APPROVAL_TERMS = {"report", "approve", "accept", "a"}
LOUNGE_TABLE_SUBMISSION_DENY_TERMS =  {"deny", "reject", "d"}
LOUNGE_TABLE_SUBMISSION_TERMS = LOUNGE_TABLE_SUBMISSION_APPROVAL_TERMS |  LOUNGE_TABLE_SUBMISSION_DENY_TERMS
LOUNGE_PENDING_TABLE_SUBMISSION_TERMS = {"pending", "pendingsubmission", "pendingsubmissions", "p"}

#Lounge only commands for table bot channels, used by staff and table bot support
GET_LOCK_TERMS = {"getlock", "gl"}
TRANSFER_LOCK_TERMS = {"transferlock", "tl"}

#Server administrator commands only
SET_PREFIX_TERMS = {"setprefix"}
SERVER_DEFAULT_TABLE_THEME_TERMS = {'defaulttheme', 'defaultservertheme', 'serverstyle', 'servertheme', 'servertablestyle', 'servertabletheme'}
SERVER_DEFAULT_GRAPH_TERMS = {'defaultgraph', 'defaultservergraph', 'servergraph', 'servertablegraph', 'servergraphtheme'}
SERVER_DEFAULT_MII_TERMS = {'defaultmii', 'servermii','servermiis','defaultservermiis','defaultmiis', 'defaultmiisetting', 'defaultmiisettings', 'miisetting'}
SERVER_DEFAULT_LARGE_TIME_TERMS = {'defaultlargetime','defaultlargetimes', 'defaultsui', 'defaultpsb', 'serverlargetimes', 'serverlargetime', 'serversui', 'serverpsb'}


#Bot Admin Only Commands
ADD_FLAG_EXCEPTION_TERMS = {'addflagexception'}
REMOVE_FLAG_EXCEPTION_TERMS = {'removeflagexception'}
SET_CTGP_REGION_TERMS = {'set_ctgp_region'}
VR_ON_TERMS = {'vr_on'}
VR_OFF_TERMS = {'vr_off'}
BLACKLIST_USER_TERMS = {"blacklistuser"}
BLACKLIST_WORD_TERMS = {"blacklistword", "addblacklistedword", "addblacklistword", "addword"}
REMOVE_BLACKLISTED_WORD_TERMS = {"removeblacklistword", "removeblacklistedword", "removeword"}

#Bad Wolf Commands only
SERVER_USAGE_TERMS = {"serverusage", "usage", "serverstats"}
TABLE_BOT_MEMORY_USAGE_TERMS = {"memory", "memoryusage"}
GARBAGE_COLLECT_TERMS = {"gc", "garbagecollect"}
ADD_BAD_WOLF_FACT_TERMS = {"addbadwolffact", "abwf"}
REMOVE_BAD_WOLF_FACT_TERMS = {"removebadwolffact", "rbwf"}
BAD_WOLF_FACT_TERMS = {"badwolffacts", "bwfs"}
TOTAL_CLEAR_TERMS = {'totalclear'}
DUMP_DATA_TERMS = {"dtt", "dothething"}
ADD_BOT_ADMIN_TERMS = {"addbotadmin", "addadmin"}
REMOVE_BOT_ADMIN_TERMS = {"removebotadmin", "removeadmin"}
GET_LOGS_TERMS = {"getlog", "getlogs", "logs"}

needPermissionCommands = DISPLAY_GP_SIZE_TERMS | TABLE_THEME_TERMS | GRAPH_TERMS | RESET_TERMS | START_WAR_TERMS | UNDO_TERMS | REMOVE_RACE_TERMS | PLAYER_PENALTY_TERMS | TEAM_PENALTY_TERMS | EDIT_PLAYER_SCORE_TERMS | PLAYER_DISCONNECT_TERMS | MERGE_ROOM_TERMS | SET_WAR_NAME_TERMS | CHANGE_PLAYER_NAME_TERMS | CHANGE_PLAYER_TAG_TERMS | CHANGE_ROOM_SIZE_TERMS | EARLY_DC_TERMS | QUICK_EDIT_TERMS

ALLOWED_COMMANDS_IN_LOUNGE_ECHELONS = LOUNGE_MOGI_UPDATE_TERMS | LOUNGE_TABLE_SUBMISSION_TERMS | LOUNGE_PENDING_TABLE_SUBMISSION_TERMS | STATS_TERMS | INVITE_TERMS | MII_TERMS | FC_TERMS | BATTLES_TERMS | CTWW_TERMS | WORLDWIDE_TERMS | VERIFY_ROOM_TERMS | LOUNGE_NAME_TERMS | SET_FLAG_TERMS | GET_FLAG_TERMS


if in_testing_server:
    lounge_server_id = 739733336871665696
    RT_UPDATER_CHANNEL = 851745996396560405
    CT_UPDATER_CHANNEL = 742947685652365392
    MogiUpdate.rt_summary_channels = {"1":851745996396560405, "2":None, "3":None, "4":None, "4-5":770109830957498428, "5":None, "6":None, "7":None, "squadqueue":742947723237392514}
    MogiUpdate.ct_summary_channels = {"1":740574415057846323, "2":None, "3":None, "4":None, "4-5":None, "5":None, "6":None, "7":None, "squadqueue":742947723237392514}
    lounge_staff_roles.add(740659173695553667) #Admin in test server

switch_status = True

table_bots = {}
user_flag_exceptions = set()
lounge_table_reports = {}
lounge_table_id_counter = 25 #set at a slightly higher number so the first few submissions aren't confusing for people




bad_wolf_facts = []

update_cooldowns = {}
update_cooldown_time = timedelta(seconds=20)


client = discord.Client()



def get_user_update_submit_cooldown(author_id):
    if author_id not in update_cooldowns:
        return -1

    curTime = datetime.now()
    time_passed = curTime - update_cooldowns[author_id]
    return int(update_cooldown_time.total_seconds()) - int(time_passed.total_seconds())
    
def author_is_lounge_staff(message_author:discord.Member):
    for role in message_author.roles:
        if role.id in lounge_staff_roles:
            return True
    return False

def can_report_table(message_author:discord.Member):
    return author_is_lounge_staff(message_author) or message_author.id == badwolf_id

def commandIsAllowed(isLoungeServer:bool, message_author:discord.Member, this_bot:TableBot.ChannelBot, command:str):
    
    if not isLoungeServer:
        return True
    
    
    for role in message_author.roles:
        if role.id in lounge_staff_roles:
            return True
    
    
    if this_bot != None and this_bot.getWar() != None and (this_bot.prev_command_sw or this_bot.manualWarSetUp):
        return this_bot.getRoom().getSetupUser() == None or this_bot.getRoom().getSetupUser() == message_author.id
    
    if command not in needPermissionCommands:
        return True
    
    if this_bot == None or this_bot.getRoom() == None or not this_bot.getRoom().is_initialized() or this_bot.getRoom().getSetupUser() == None:
        return True

    #At this point, we know the command's server is Lounge, it's not staff, and a room has been loaded
    #Check if the user was the setUpuser
    return this_bot.getRoom().canModifyTable(message_author.id)

    
def getNumActiveWars():
    inactivity_time_period_count = timedelta(minutes=30)
    num_wars = 0
    for s in table_bots:
        for c in table_bots[s]:
            if table_bots[s][c] != None and table_bots[s][c].getWar() != None:
                time_passed = datetime.now() - table_bots[s][c].last_used
                if time_passed < inactivity_time_period_count:
                    num_wars += 1
    return num_wars


#Strips the given prefix from the start of the command
#Note, the caller must ensure that the given string has a prefix by using has_prefix to ensure proper behaviour
#lstrip won't work here (go read the documentation and find a scenario that it wouldn't work in)
def strip_prefix(command, pref=default_prefix):
    new_command = command[len(pref):]
    return new_command

#Checks if the given string has the given prefix at the front of it
def has_prefix(command, pref=default_prefix):
    if type(command) != type(""):
        return False
    if len(command) < len(pref):
        return False
    return command.startswith(pref)

async def check_default_change_pref(message:discord.Message):
    if len(message.content) <= len("setprefix"):
        return False
    
    if message.content.split()[0].lower().strip() in ["?setprefix"]:
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Can't change prefix, you're not an administrator in this server.")
            return True
        args = message.content.split()
        if len(args) < 2:
            await message.channel.send("Give a prefix. Prefix not changed.")
            return True
        new_prefix = message.content[len("?setprefix"):].strip("\n").strip()
        if len(new_prefix) < 1:
            await message.channel.send("Cannot set an empty prefix. Prefix not changed.")
        was_success = ServerFunctions.change_server_prefix(str(message.guild.id), new_prefix)
        if was_success:
            await message.channel.send("Prefix changed to: " + new_prefix) 
        else:
            await message.channel.send("Error setting prefix. Prefix not changed.") 
        return True
    return False

def has_my_name(message:str):
    return False
    return "tablebot" in message.lower().replace(" ", "")




def createEmptyTableBot(server_id=None):
    return TableBot.ChannelBot(server_id=server_id)

async def get_races(rLID:str):
    new_bot = createEmptyTableBot() #create a new one so it won't interfere with any room they might have loaded (like a table)
    successful = await new_bot.load_room_smart([rLID])
    if not successful:
        return None
    return new_bot.getRoom().get_races_abbreviated(last_x_races=12)


last_fact_times = {}
fact_cooldown = timedelta(seconds=30)
async def send_bad_wolf_fact(message:discord.Message):
    global last_fact_times
    if len(bad_wolf_facts) > 0:
        cur_time = datetime.now()
        if message.channel.id not in last_fact_times \
        or (cur_time - last_fact_times[message.channel.id]) > fact_cooldown:
            last_fact_times[message.channel.id] = cur_time
            fact = random.choice(bad_wolf_facts)
            if "DISPLAY_NAME" in fact:
                fact = fact.replace("DISPLAY_NAME", message.author.display_name)
            if "MENTION" in fact:
                fact = fact.replace("MENTION", message.author.display_name)
            await message.channel.send(fact, delete_after=10)



#If there is a channel bot for a server and a channel already, return it
#Otherwise, create a new one, store it, and return that one
#May use defaultdicts in the future for better readability
def check_create_channel_bot(message:discord.Message):
    global table_bots
    server_id = message.guild.id
    channel_id = message.channel.id
    if server_id not in table_bots:
        table_bots[server_id] = {}
    if channel_id not in table_bots[server_id]:
        table_bots[server_id][channel_id] = createEmptyTableBot(server_id)
    table_bots[server_id][channel_id].updatedLastUsed()
    return table_bots[server_id][channel_id]
    
    
#Creates the necessary folders for running the bot
def create_folders():
    Path(MIIS_PATH).mkdir(parents=True, exist_ok=True)
    Path(SERVER_SETTINGS_PATH).mkdir(parents=True, exist_ok=True)
    Path(FLAG_IMAGES_PATH).mkdir(parents=True, exist_ok=True)
    Path(FONT_PATH).mkdir(parents=True, exist_ok=True)
    Path(HELP_PATH).mkdir(parents=True, exist_ok=True)
    Path(LOGGING_PATH).mkdir(parents=True, exist_ok=True)
    Path(TABLE_HEADERS_PATH).mkdir(parents=True, exist_ok=True)
    Path(DATA_PATH).mkdir(parents=True, exist_ok=True)

#Bring in the bot key and LoungeAPI key
def private_data_init():
    global testing_bot_key
    global real_bot_key
    with open(PRIVATE_INFO_FILE, "r") as f:
        testing_bot_key = f.readline().strip("\n")
        real_bot_key = f.readline().strip("\n")
        LoungeAPIFunctions.code = f.readline().strip("\n")

#Initialize everything
def initialize():
    create_folders()
    private_data_init()
    UserDataProcessing.initialize()
    ServerFunctions.initialize()
    UtilityFunctions.initialize()


@client.event
async def on_message(message: discord.Message):
    ##########################################################################################At this point, we know the room exists, and we certainly have rLID. We're not sure if we have the roomID yet though.    
    """for guild in client.guilds:
        if guild.name == "POV: u've been ur mom'd":
            print(guild.id)
    return"""
    
    if message.author == client.user:
        return
    if message.guild == None:
        return
    if not finished_on_ready:
        return
    has_pref = None
    global bad_wolf_facts
    try:
        
        server_id = message.guild.id
        channel_id = message.channel.id
        author_id = message.author.id
        is_lounge_server = server_id == lounge_server_id
        
        server_prefix = ServerFunctions.get_server_prefix(server_id)
        has_pref = has_prefix(message.content, server_prefix)
        if has_my_name(message.content):
            await send_bad_wolf_fact(message)
        #Message doesn't start with the server's prefix and isn't ?help
        if not has_pref and not message.content.lower()=="?help" and not (client.user.mentioned_in(message) and 'help' in message.content.strip().lower()):
            if message.channel.category_id not in TEMPORARY_VR_CATEGORIES:
                return
            else:
                str_msg = message.content.strip()
                if len(str_msg) < 2:
                    return
                server_prefix = str_msg[0]
                if server_prefix not in ["?","!"] or str_msg[1:].split()[0].lower() not in VERIFY_ROOM_TERMS:
                    return
                    
        
        command = strip_prefix(message.content, server_prefix)
        old_command = copy.copy(command)
        if command == "" or len([c for c in command if c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"]) == 0:
            return
        args = command.split()
        
        if str(author_id) in UserDataProcessing.blacklisted_Users and author_id != badwolf_id:
            if has_pref:
                if blacklisted_command_count[author_id] % 15 == 0:
                    await message.channel.send("You have been blacklisted by a bot admin. You are not allowed to use this bot. Reason: " + str(UserDataProcessing.blacklisted_Users[str(author_id)]), delete_after=10)
                blacklisted_command_count[author_id] += 1
            return
        """if message.content.strip().lower() == 'addme':
            lounge_staff_roles.add(740659173695553667)
        elif message.content.strip().lower() == 'removeme':
            lounge_staff_roles.remove(740659173695553667)
        """
        if has_prefix:
            if len(args) > 0:
                if not commands.vr_is_on and (args[0] in VERIFY_ROOM_TERMS):
                    return
            bot_abuse_tracking[author_id] += 1
            if bot_abuse_tracking[author_id] == WARN_THRESHOLD:
                await message.channel.send(f"{message.author.mention} slow down, you're sending too many commands. To avoid getting banned, wait 5 minutes before sending another command.")
            elif bot_abuse_tracking[author_id] == AUTO_BAN_THRESHOLD: #certain spam
                UserDataProcessing.add_Blacklisted_user(str(author_id), "Automated ban - you spammed the bot. This hurts users everywhere because it slows down the bot for everyone. You can appeal in 1 week.")
                await client.get_channel(BOT_ABUSE_REPORT_CHANNEL_ID).send(f"Automatic ban for spamming bot:\nDiscord: {str(message.author)}\nDiscord ID: {author_id}\nDisplay name: {message.author.display_name}\nLast message: {message.content}")
                return
            
        if message.content.strip().lower() in ["?help"] or (client.user.mentioned_in(message) and 'help' in message.content.strip().lower()):
            if message.channel.category_id in TEMPORARY_VR_CATEGORIES:
                return
            if str(author_id) in UserDataProcessing.blacklisted_Users and author_id != badwolf_id:
                #await message.channel.send("You have been blacklisted by a bot admin. You are not allowed to use this bot. Reason: " + str(UserDataProcessing.blacklisted_Users[str(author_id)]))
                return
            else:
                await help_documentation.send_help(message, is_lounge_server, args, server_prefix)
        else:
            was_default_change_pref = await check_default_change_pref(message)
            if was_default_change_pref:
                return
            
            
            #temporary vr check
            if message.channel.category_id in TEMPORARY_VR_CATEGORIES:
                str_msg = message.content.strip()
                if str_msg.startswith("!") or str_msg.startswith("?") or str_msg.startswith("^"):
                    this_bot = check_create_channel_bot(message)
                    if args[0] in ALLOWED_COMMANDS_IN_LOUNGE_ECHELONS:
                        pass
                    else:
                        if args[0] in VERIFY_ROOM_TERMS:
                            if commands.vr_is_on:
                                await commands.OtherCommands.vr_command(this_bot, message, args, old_command)
                        if str_msg[0] == "?":
                            if args[0] in FC_TERMS:
                                await commands.OtherCommands.fc_command(message, args, old_command)
                        return
                    
                else:
                    return
            
            
                        
            log_command_sent(message)
            
            this_bot:TableBot.ChannelBot = check_create_channel_bot(message)
            this_bot.updatedLastUsed()
            if is_lounge_server and this_bot.isFinishedLounge():
                this_bot.freeLock()
            
            if not commandIsAllowed(is_lounge_server, message.author, this_bot, args[0]):
                to_send = "The bot is locked to players in this room only: **"
                if this_bot.getRoom() != None:
                    if this_bot.getRoom().getSetupUser() != None:
                        room_lounge_names = this_bot.getRoom().get_loungenames_can_modify_table()
                        to_send += ", ".join(room_lounge_names)
                        to_send += "**."
                    if this_bot.loungeFinishTime == None:
                        await message.channel.send(f"{to_send} Wait until they are finished.")  
                    else:
                        await message.channel.send(f"{to_send} {this_bot.getBotunlockedInStr()}")  
            else:
                
                if str(author_id) in UserDataProcessing.blacklisted_Users and author_id != badwolf_id:
                    await message.channel.send(f"You have been blacklisted by a bot admin. You are not allowed to use this bot. Reason: {UserDataProcessing.blacklisted_Users[str(author_id)]}")
                
                elif args[0] in RESET_TERMS:
                    del(table_bots[server_id][channel_id])
                    await message.channel.send("Reset successful.")
                                
                #Core commands
                elif this_bot.manualWarSetUp:
                    command = old_command
                    await commands.TablingCommands.manual_war_setup(message, this_bot, command)
                
                elif this_bot.prev_command_sw:
                    this_bot.prev_command_sw = False
                    this_bot.manualWarSetUp = False
                    if args[0].lower().strip() not in ['yes', 'no', 'y', 'n']:
                        this_bot.setWar(None)
                        await message.channel.send(f"Please put {server_prefix}yes or {server_prefix}no to **Is this correct?** - War stopped.")   
                    elif args[0].lower().strip() in ['no', 'n']:
                        await message.channel.send(f"***Input the teams in the following format: *** Suppose for a 2v2v2, tag A is 2 and 3 on the list, B is 1 and 4, and Player is 5 and 6, you would enter:  *{server_prefix}A 2 3 / B 1 4 / Player 5 6*")
                        this_bot.manualWarSetUp = True
                    
                    elif this_bot.getRoom() == None or not this_bot.getRoom().is_initialized():
                        await message.channel.send(f"Unexpected error. Somehow, there is no room loaded. War stopped. Recommend the command: {server_prefix}reset")
                        this_bot.setWar(None)
                    else:
                        fc_tags = {}
                        numGPS = this_bot.getWar().numberOfGPs
                        players = list(this_bot.getRoom().getFCPlayerListStartEnd(1, numGPS*4).items())
                        player_fcs_tags, hasANoneTag = getTagsSmart(players, this_bot.getWar().playersPerTeam)
                        if hasANoneTag:
                            player_fcs_tags = {}
                            for fc_player in players:
                                player_fcs_tags[fc_player] = getTagSmart(fc_player[1])
                        player_fcs_tags = sorted(player_fcs_tags.items(), key=lambda x: x[1])
                                
                        if len(players) != this_bot.getWar().get_num_players():
                            await message.channel.send(f'''Respond "{server_prefix}no" when asked ***Is this correct?*** - the number of players in the room doesn't match your war format and teams. Trying to still start war, but teams will be incorrect.''')
                        
                        teamTag = None
                        previous_tags = []
                        tag_counter = 0
                        for playerNum, ((fc, playerName), (_, playerTag)) in enumerate(player_fcs_tags):
                            if len(playerTag) < 1:
                                playerTag = str(playerNum+1)
                            
                            if (playerNum) % this_bot.getWar().playersPerTeam == 0:
                                #Start a new team
                                teamTag = playerTag
                                if teamTag in previous_tags:
                                    tag_counter += 1
                                    teamTag = f"{teamTag}_{tag_counter}"
                                else:
                                    tag_counter = 0
                                previous_tags.append(teamTag)
                            fc_tags[fc] = teamTag
                            
                        this_bot.getWar().setTeams(fc_tags)
                        started_war_str = "Started war."
                        if this_bot.getWar().ignoreLargeTimes:
                            started_war_str += " (Ignoring errors for large finish times)"
                        started_war_str += " rxx: "
                        if len(this_bot.getRoom().rLIDs) == 1:
                            started_war_str += str(this_bot.getRoom().rLIDs[0])
                        else:
                            started_war_str += str(this_bot.getRoom().rLIDs)
                        await message.channel.send(started_war_str) 
                
                elif args[0] in GARBAGE_COLLECT_TERMS and author_id == badwolf_id:
                    gc.collect()
                    await message.channel.send("Collected")
                    
                elif args[0] in ADD_BAD_WOLF_FACT_TERMS and author_id == badwolf_id:
                    fact = " ".join(old_command.split()[1:]).strip()
                    if len(fact) == 0:
                        await message.channel.send("Cannot add empty fact.")
                        return
                    bad_wolf_facts.append(fact)
                    pkl_bad_wolf_facts()
                    await message.channel.send(f"Added: {fact}")
                    
                elif args[0] in REMOVE_BAD_WOLF_FACT_TERMS and author_id == badwolf_id:
                    index = "".join(args[1:])
                    if not index.isnumeric() or int(index) < 0 or int(index) >= len(bad_wolf_facts):
                        await message.channel.send(f"Cannot remove fact at index {index}")
                        return
                    removed_fact = bad_wolf_facts.pop(int(index))
                    pkl_bad_wolf_facts()
                    await message.channel.send(f"Removed: {removed_fact}")
                elif args[0] in BAD_WOLF_FACT_TERMS and author_id == badwolf_id:
                    if len(bad_wolf_facts) > 0:
                        await message.channel.send("\n".join(bad_wolf_facts))
                elif args[0] in START_WAR_TERMS:
                    await commands.TablingCommands.start_war_command(message, this_bot, args, server_prefix, is_lounge_server, command, author_is_lounge_staff)
                
                elif args[0] in TABLE_TEXT_TERMS:
                    await commands.TablingCommands.table_text_command(message, this_bot, server_prefix, is_lounge_server)
                elif args[0] in WAR_PICTURE_TERMS:
                    await commands.TablingCommands.war_picture_command(message, this_bot, args, server_prefix, is_lounge_server)
                      
                        
                #Lounge reporting updates
                elif args[0] in TOTAL_CLEAR_TERMS:
                    if message.author.id == badwolf_id:
                        global update_cooldowns
                        update_cooldowns.clear()
                        await message.channel.send("Cleared.")
                        
                elif args[0] in LOUNGE_MOGI_UPDATE_TERMS:
                    if not is_lounge_server:
                        return
                    global lounge_table_id_counter
                    global lounge_table_reports
                    is_rt = args[0] in LOUNGE_RT_MOGI_UPDATE_TERMS
                    updater_channel_id = RT_UPDATER_CHANNEL
                    updater_link = RT_UPDATER_LINK
                    preview_link = RT_UPDATE_PREVIEW_LINK
                    type_text = "RT"
                    #reporter_role = "<@&" + str(RT_REPORTER_ID) + ">"
                    #updater_role = "<@&" + str(RT_UPDATER_ID) + ">"
                    if not is_rt:
                        updater_channel_id = CT_UPDATER_CHANNEL
                        updater_link = CT_UPDATER_LINK
                        preview_link = CT_UPDATE_PREVIEW_LINK
                        type_text = "CT"
                        #reporter_role = "<@&" + str(CT_REPORTER_ID) + ">"
                        #updater_role = "<@&" + str(CT_UPDATER_ID) + ">"
                    cooldown = get_user_update_submit_cooldown(message.author.id)
                    
                    if cooldown > 0:
                        await message.channel.send("You have already submitted a table very recently. Please wait " + str(cooldown) + " more seconds before submitting another table.", delete_after=10)
                        return
                    
                    if len(args) < 2:
                        await message.channel.send("The format of this command is: ?" + args[0] + " TierNumber (TableText)\nIf you want to submit the table that you're doing with MKW Table Bot, you can just do ?" + args[0] + " TierNumber")
                        return
                    
    
                    tier_number, summary_channel_id = MogiUpdate.get_tier_and_summary_channel_id(args[1], is_rt)
                    if tier_number == None:
                        await message.channel.send("The format of this command is: ?" + args[0] + " TierNumber (TableText) - TierNumber must be a number. For RTs, must be between 1 and 8. For CTs, must be between 1 and 6. If you are trying to submit a squadqueue table, <tierNumber> should be: squadqueue")
                        return
                    
                    if len(args) == 2:
                        #check if they have war going currently
                        if this_bot.getWar() == None or this_bot.getRoom() == None:
                            await message.channel.send("You must start a war to use this command - if you want to submit a table you did manually, put in the table text")
                        elif len(this_bot.getRoom().getRaces()) < 12:
                            await message.channel.send("Cannot submit a table that has less than 12 races.")
                        else:
                            update_cooldowns[message.author.id] = datetime.now()
                            delete_me = await message.channel.send("Submitting table... please wait...")
                            original_table_text, table_sorted_data = SK.get_war_table_DCS(this_bot)
                            with_style_and_graph_table_text = original_table_text + this_bot.get_lorenzi_style_and_graph(prepend_newline=True)
                            url_table_text = urllib.parse.quote(with_style_and_graph_table_text)
                            image_url = base_url_lorenzi + url_table_text
                            
                            table_image_path = str(message.id) + ".png"
                            image_download_success = await download_image(image_url, table_image_path)
                            try:
                                if not image_download_success:
                                    await message.channel.send("Could not get image for table.")
                                    return
                                #did the room have *any* errors? Regardless of ignoring any type of error
                                war_had_errors = len(this_bot.getWar().get_all_war_errors_players(this_bot.getRoom(), False)) > 0
                                tableWasEdited = len(this_bot.getWar().manualEdits) > 0 or len(this_bot.getRoom().dc_on_or_before) > 0 or len(this_bot.getRoom().forcedRoomSize) > 0 or this_bot.getRoom().had_positions_changed() or len(this_bot.getRoom().get_removed_races_string()) > 0
                                header_combine_success = ImageCombine.add_autotable_header(errors=war_had_errors, table_image_path=table_image_path, out_image_path=table_image_path, edits=tableWasEdited)
                                footer_combine_success = True
                    
                                if header_combine_success and this_bot.getWar().displayMiis:
                                    footer_combine_success = ImageCombine.add_miis_to_table(this_bot, table_sorted_data, table_image_path=table_image_path, out_image_path=table_image_path)
                                if not header_combine_success or not footer_combine_success:
                                    await message.channel.send("Internal server error when combining images. Sorry, please notify BadWolf immediately.")  
                                else:
                                    error_code, _, json_data = await MogiUpdate.textInputUpdate(original_table_text, tier_number, is_rt=is_rt)
                                    
                                    if error_code != MogiUpdate.SUCCESS_EC:
                                        if error_code == None:
                                            await message.channel.send("Couldn't submit table. An unknown error occurred.")
                                        elif error_code == MogiUpdate.PLAYER_NOT_FOUND_EC:
                                            missing_players = json_data
                                            await message.channel.send("Couldn't submit table. The following players could not be found: **" + "**, **".join(missing_players) + "**\nCheck your submission for correct names. If your table has subs, they must be in this format: Sarah(4)/Jacob(8)")
                                        else:
                                            await message.channel.send("Couldn't submit table. Reason: *" + MogiUpdate.table_text_errors[error_code] + "*")
                                
                                    else:
                                        updater_channel = client.get_channel(updater_channel_id)
                                        preview_link += urllib.parse.quote(json_data)
                                        updater_link += urllib.parse.quote(json_data)
                                        
                                        
                                        embed = discord.Embed(
                                                            title = "",
                                                            description="[Click to load this update in the admin panel]("+ updater_link + ")",
                                                            colour = discord.Colour.dark_red()
                                                        )
                                        file = discord.File(table_image_path)
                                        lounge_table_id_counter += 1
                                        id_to_submit = lounge_table_id_counter
                                        
                                        embed.add_field(name="Submission ID:", value=str(id_to_submit))
                                        embed.add_field(name="Tier", value=tier_number)
                                        summary_channel = client.get_channel(summary_channel_id)
                                        embed.add_field(name="Approving to:", value=(summary_channel.mention if summary_channel != None else "Can't find channel"))
                                        embed.add_field(name='Submitted from:', value=message.channel.mention)
                                        embed.add_field(name='Submitted by:', value=message.author.mention)
                                        embed.add_field(name='Discord ID:', value=str(message.author.id))
                                        
                                        embed.set_image(url="attachment://" + table_image_path)
                                        embed.set_author(name="Updater Automation", icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")
                                        embed.set_footer(text="Updaters: Login to the admin panel before clicking the link.")
                                        
                                        
                                        sent_message = await updater_channel.send(file=file, embed=embed)
                                        lounge_table_reports[id_to_submit] = [sent_message.id, sent_message.channel.id, summary_channel_id, "PENDING"]
                                        
                                        
                                        file = discord.File(table_image_path)
                                        embed = discord.Embed(
                                                            title = "Successfully submitted to " + type_text + " Reporters and " + type_text + " Updaters",
                                                            description="[Click to preview this update]("+ preview_link + ")",
                                                            colour = discord.Colour.dark_red()
                                                        )
                                        embed.add_field(name="Submission ID:", value=id_to_submit)
                                        embed.set_image(url="attachment://" + table_image_path)
                                        embed.set_author(name="Updater Automation", icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")
                                        embed.set_footer(text="Note: the actual update may look different than this preview if the Updaters need to first update previous mogis. If the link is too long, just hit the enter key.")
                                        await message.channel.send(file=file, embed=embed)
                            finally:
                                if os.path.exists(table_image_path):
                                    os.remove(table_image_path)
                            update_cooldowns[message.author.id] = datetime.now()   
                            await delete_me.delete()   
                    else:
                        update_cooldowns[message.author.id] = datetime.now()
                        delete_me = await message.channel.send("Submitting table... please wait...")
                        temp = message.content
                        command_removed = temp[temp.lower().index(args[0])+len(args[0]):].strip("\n\t ")
                        table_text = command_removed[command_removed.lower().index(args[1])+len(args[1]):].strip("\n\t ")
                        
                        error_code, newTableText, json_data = await MogiUpdate.textInputUpdate(table_text, tier_number, is_rt=is_rt)
                        
                        
                        if error_code != MogiUpdate.SUCCESS_EC:
                            if error_code == None:
                                await message.channel.send("Couldn't submit table. An unknown error occurred.")
                            elif error_code == MogiUpdate.PLAYER_NOT_FOUND_EC:
                                missing_players = json_data
                                await message.channel.send("Couldn't submit table. The following players could not be found: **" + "**, **".join(missing_players) + "**\nCheck your submission for correct names. If your table has subs, they must be in this format: Sarah(4)/Jacob(8)")
                            else:
                                await message.channel.send("Couldn't submit table. Reason: *" + MogiUpdate.table_text_errors[error_code] + "*")
                    
                        
                        else:
                            url_table_text = urllib.parse.quote(newTableText)
                            image_url = base_url_lorenzi + url_table_text
                            table_image_path = str(message.id) + ".png"
                            image_download_success = await download_image(image_url, table_image_path)
                            try:
                                if not image_download_success:
                                    await message.channel.send("Could not get image for table.")
                                else:
                                    updater_channel = client.get_channel(updater_channel_id)
                                    preview_link += urllib.parse.quote(json_data)
                                    updater_link += urllib.parse.quote(json_data)
            
            
                                    embed = discord.Embed(
                                                        title = "",
                                                        description="[Click to load this update in the admin panel]("+ updater_link + ")",
                                                        colour = discord.Colour.dark_red()
                                                    )
                                    file = discord.File(table_image_path)
                                    lounge_table_id_counter += 1
                                    id_to_submit = lounge_table_id_counter
                                    embed.add_field(name='Submission ID:', value=str(id_to_submit))
                                    embed.add_field(name="Tier", value=tier_number)
                                    summary_channel = client.get_channel(summary_channel_id)
                                    embed.add_field(name="Approving to:", value=(summary_channel.mention if summary_channel != None else "Can't find channel"))
                                    embed.add_field(name='Submitted from:', value=message.channel.mention)
                                    embed.add_field(name='Submitted by:', value=message.author.mention)
                                    embed.add_field(name='Discord ID:', value=str(message.author.id))
                                    
                                    
                                    embed.set_image(url="attachment://" + table_image_path)
                                    embed.set_author(name="Updater Automation", icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")
                                    embed.set_footer(text="Updaters: Login to the admin panel before clicking the link.")
                                    
                                    
                                    sent_message = await updater_channel.send(file=file, embed=embed)
                                    lounge_table_reports[id_to_submit] = [sent_message.id, sent_message.channel.id, summary_channel_id, "PENDING"]
                                
                                    
                                    file = discord.File(table_image_path)
                                    embed = discord.Embed(
                                                        title = "Successfully submitted to " + type_text + " Reporters and " + type_text + " Updaters",
                                                        description="[Click to preview this update]("+ preview_link + ")",
                                                        colour = discord.Colour.dark_red()
                                                    )
                                    embed.add_field(name='Submission ID:', value=str(id_to_submit))
                                    embed.set_image(url="attachment://" + table_image_path)
                                    embed.set_author(name="Updater Automation", icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")
                                    embed.set_footer(text="Note: the actual update may look different than this preview if the Updaters need to first update previous mogis. If the link is too long, just hit the enter key.")
                                    
                                    await message.channel.send(file=file, embed=embed)
                            finally:
                                if os.path.exists(table_image_path):
                                    os.remove(table_image_path)
                        update_cooldowns[message.author.id] = datetime.now()   
                        await delete_me.delete()   
            
                elif args[0] in LOUNGE_TABLE_SUBMISSION_TERMS:
                    if not is_lounge_server:
                        return
                    if message.channel.id not in [RT_UPDATER_CHANNEL, CT_UPDATER_CHANNEL]:
                        return
                    if can_report_table(message.author):
                        reporter_approved = args[0] in LOUNGE_TABLE_SUBMISSION_APPROVAL_TERMS
                        if len(args) < 2:
                            await message.channel.send("The way to use this command is: ?" + args[0] + " submissionID")
                            return
                        submissionID = args[1]
                        if submissionID.isnumeric():
                            submissionID = int(submissionID)
                            if submissionID in lounge_table_reports:
                                submissionMessageID, submissionChannelID, summaryChannelID, submissionStatus = lounge_table_reports[submissionID]
                                submissionMessage = None
                                
                                try:
                                    submissionChannel = client.get_channel(submissionChannelID)
                                    if submissionChannel == None:
                                        await message.channel.send("I cannot see the submission channels (or they changed). Get boss help.")
                                        return
                                    submissionMessage = await submissionChannel.fetch_message(submissionMessageID)
                                except discord.errors.NotFound:
                                    await message.channel.send("That submission appears to have been deleted on Discord. I have now removed this submission from my records.")
                                    del lounge_table_reports[submissionID]
                                    return
                                
                                if reporter_approved:
                                    submissionEmbed = submissionMessage.embeds[0]
                                    submissionEmbed.remove_field(5)
                                    submissionEmbed.remove_field(4)
                                    submissionEmbed.remove_field(3)
                                    submissionEmbed.remove_field(2)
                                    submissionEmbed.set_field_at(1, name="Approved by:", value=message.author.mention)
                                    submissionEmbed.add_field(name="Approval link:", value="[Message](" + submissionMessage.jump_url + ")")
                                    
                                    summaryChannelRetrieved = True
                                    if summaryChannelID == None:
                                        summaryChannelRetrieved = False
                                    summaryChannelObj = client.get_channel(summaryChannelID)
                                    if summaryChannelObj == None:
                                        summaryChannelRetrieved = False
                                    if not summaryChannelRetrieved:
                                        await message.channel.send("I cannot see the summary channels. Contact a boss.")
                                        return
                                    try:
                                        await summaryChannelObj.send(embed=submissionEmbed)
                                    except discord.errors.Forbidden:
                                        await message.channel.send("I'm not allowed to send messages in summary channels. Contact a boss.")
                                        return
                                    
                                    lounge_table_reports[submissionID][3] = "APPROVED"
                                    await submissionMessage.clear_reaction("\u274C")
                                    await submissionMessage.add_reaction("\u2705")
                                    await message.add_reaction(u"\U0001F197")
                                else:
                                    await submissionMessage.clear_reaction("\u2705")
                                    await submissionMessage.add_reaction("\u274C")
                                    lounge_table_reports[submissionID][3] = "DENIED"
                                    await message.add_reaction(u"\U0001F197")
                            else:
                                await message.channel.send("I couldn't find this submission ID. Make sure you have the right submission ID.")                              
                        else:
                            await message.channel.send("The way to use this command is: ?" + args[0] + " submissionID - submissionID must be a number")
                elif args[0] in LOUNGE_PENDING_TABLE_SUBMISSION_TERMS:
                    if not is_lounge_server:
                        return
                    if can_report_table(message.author):
                        to_send = ""
                        for submissionID in lounge_table_reports:
                            _, submissionChannelID, summaryChannelID, submissionStatus = lounge_table_reports[submissionID]
                            if submissionStatus == "PENDING":
                                to_send += MogiUpdate.getTierFromChannelID(summaryChannelID) + " - Submission ID: " + str(submissionID) + "\n"
                        if to_send == "":
                            to_send = "No pending submissions."
                        await message.channel.send(to_send)
                #Fun commands
                elif args[0] in STATS_TERMS:
                    num_wars = getNumActiveWars()
                    stats_str = Stats.stats(num_wars, client)
                    if stats_str == None:
                        await message.channel.send("Error fetching stats. Try again.")
                    else:
                        await message.channel.send(stats_str)
                
                elif (args[0] in ["badwolf"]) or (len(args) > 1 and (args[0] in ["bad"] and args[1] in ["wolf"])):
                    await message.channel.send(file=discord.File(BADWOLF_PICTURE_FILE))    
                
                elif args[0] in INVITE_TERMS:
                    await message.channel.send(bot_invite_link)              
                
                
                
                #Informational commands
                elif args[0] in GET_LOCK_TERMS and is_lounge_server:
                    if this_bot.getRoom() == None or this_bot.getRoom().getSetupUser() == None:
                        await message.channel.send("Bot is not locked to any user.")
                    else:
                        room_lounge_names = this_bot.getRoom().get_loungenames_can_modify_table()
                        to_send = "The bot is locked to players in this room: **"
                        to_send += ", ".join(room_lounge_names)
                        to_send += "**.\n"
                        to_send += "The setup user who has the main lock is **" + str(this_bot.getRoom().getSetupUser()) + f"- {this_bot.getRoom().set_up_user_display_name}**"
                        
                        await message.channel.send(to_send)   
                
                elif args[0] in TRANSFER_LOCK_TERMS and is_lounge_server:
                    if author_is_lounge_staff(message.author):
                        if this_bot.getRoom() == None or this_bot.getRoom().getSetupUser() == None:
                            await message.channel.send("Cannot transfer lock. Bot not locked to any user.")
                        else:
                            if len(args) > 1:
                                newUser = args[1]
                                if not newUser.isnumeric():
                                    await message.channel.send("You must give their Discord ID. This is the long number you can get in Discord's Developer Mode.")
                                else:
                                    newUser = int(newUser)
                                    this_bot.getRoom().set_up_user = newUser
                                    this_bot.getRoom().set_up_user_display_name = ""
                                    await message.channel.send("Lock transferred to: " + str(newUser))
                            else:
                                await message.channel.send("You must give their Discord ID. This is the long number you can get in Discord's Developer Mode.")       
                    
                elif args[0] in RACE_RESULTS_TERMS:
                    await commands.TablingCommands.race_results_command(message, this_bot, args, server_prefix, is_lounge_server)
                                
                elif args[0] in REMOVE_RACE_TERMS:
                    await commands.TablingCommands.remove_race_command(message, this_bot, args, server_prefix, is_lounge_server)
                    
                elif args[0] in CURRENT_ROOM_TERMS:
                    await commands.TablingCommands.current_room_command(message, this_bot, server_prefix, is_lounge_server
                                                        )
                elif args[0] in ADD_FLAG_EXCEPTION_TERMS:
                    await commands.BotAdminCommands.add_flag_exception_command(message, args, user_flag_exceptions)
                        
                elif args[0] in REMOVE_FLAG_EXCEPTION_TERMS:
                    await commands.BotAdminCommands.remove_flag_exception_command(message, args, user_flag_exceptions)
                        
                elif args[0] in SET_CTGP_REGION_TERMS:
                    await commands.BotAdminCommands.change_ctgp_region_command(message, args)
                
                elif args[0] in VR_ON_TERMS:
                    await commands.BotAdminCommands.global_vr_command(message, args, on=True)
                        
                elif args[0] in VR_OFF_TERMS:
                    await commands.BotAdminCommands.global_vr_command(message, args, on=False)
                        
                elif args[0] in QUICK_START_TERMS:
                    await help_documentation.send_quickstart(message)
                    
                elif args[0] in TUTORIAL_TERMS:
                    await message.channel.send("https://www.youtube.com/watch?v=fCQnfo06_RI")                      
                
                elif args[0] in HELP_TERMS:
                    await help_documentation.send_help(message, is_lounge_server, args, server_prefix)
                
                
                #Utility commands
                elif args[0] in EARLY_DC_TERMS:
                    await commands.TablingCommands.early_dc_command(message, this_bot, args, server_prefix, is_lounge_server)
                
                elif args[0] in CHANGE_ROOM_SIZE_TERMS:
                    await commands.TablingCommands.change_room_size_command(message, this_bot, args, server_prefix, is_lounge_server)
                
                elif args[0] in QUICK_EDIT_TERMS:
                    await commands.TablingCommands.quick_edit_command(message, this_bot, args, server_prefix, is_lounge_server, command)
                
                elif args[0] in CHANGE_PLAYER_TAG_TERMS:
                    await commands.TablingCommands.change_player_tag_command(message, this_bot, args, server_prefix, is_lounge_server, command)
                
                elif args[0] in CHANGE_PLAYER_NAME_TERMS:
                    await commands.TablingCommands.change_player_name_command(message, this_bot, args, server_prefix, is_lounge_server, command)
                
                elif args[0] in EDIT_PLAYER_SCORE_TERMS:
                    if not this_bot.table_is_set():
                        await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
                    else:
                        if len(args) == 1:
                            to_send = this_bot.getRoom().get_sorted_player_list_string()
                            to_send += "\n**To edit the GP3 score of the 7th player on the list to 37 points:** *" + server_prefix + "edit 7 3 37*"
                            await message.channel.send(to_send)
                        elif len(args) != 4:
                            await message.channel.send("Do " + server_prefix + "edit for an example on how to use this command.")
                        elif len(args) == 4:
                            playerNum = old_command.split()[1].strip()
                            GPNum = args[2]
                            amount = args[3]
                            players = this_bot.getRoom().get_sorted_player_list()
                            if not GPNum.isnumeric() or not amount.isnumeric():
                                await message.channel.send("GP Number and amount must all be numbers. Do " + server_prefix + "edit for an example on how to use this command.")
                            else:
                                players = this_bot.getRoom().get_sorted_player_list()
                                numGPs = this_bot.getWar().numberOfGPs
                                GPNum = int(GPNum)
                                amount = int(amount)
                                if playerNum.isnumeric():
                                    playerNum = int(playerNum)
                                    if playerNum < 1 or playerNum > len(players):
                                        await message.channel.send("The player number must be on this list (between 1 and " + str(len(players)) + "). Do " + server_prefix + "edit for an example on how to use this command.")
                                    elif GPNum < 1 or GPNum > numGPs:
                                        await message.channel.send("The current war is only set to " + str(numGPs) + " GPs. Your GP number was: " + UtilityFunctions.process_name(str(GPNum)))
                                    else:
                                        this_bot.add_save_state(message.content)
                                        this_bot.getWar().addEdit(players[playerNum-1][0], GPNum, amount)
                                        await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + lounge_add(players[playerNum-1][0]) + " GP" + str(GPNum) + " score edited to " + str(amount) + " points."))
                                else:
                                    lounge_name = str(copy.copy(playerNum))
                                    loungeNameFCs = UserDataProcessing.getFCsByLoungeName(lounge_name)
                                    for _playerNum, (fc, _) in enumerate(players, 1):
                                        if fc in loungeNameFCs:
                                            break
                                    else:
                                        _playerNum = None
                                        
                                        
                                    if _playerNum == None:
                                        await message.channel.send("Could not find Lounge name " + UtilityFunctions.process_name(str(lounge_name)) + " in this room.")
                                    else:
                                        this_bot.add_save_state(message.content)
                                        this_bot.getWar().addEdit(players[_playerNum-1][0], GPNum, amount)
                                        await message.channel.send(UtilityFunctions.process_name(players[_playerNum-1][1] + lounge_add(players[_playerNum-1][0]) + " GP" + str(GPNum) + " score edited to " + str(amount) + " points."))

            
                
                elif args[0] in PLAYER_PENALTY_TERMS:
                    if not this_bot.table_is_set():
                        await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
                    else:
                        if len(args) == 1:
                            to_send = this_bot.getRoom().get_sorted_player_list_string()
                            to_send += "\n**To give the 2nd player on the list a 15 point penalty:** *" + server_prefix + "penalty 2 15*"
                            await message.channel.send(to_send)
                        elif len(args) != 3:
                            await message.channel.send("Do " + server_prefix + "penalty for an example on how to use this command.")
                        elif len(args) == 3:
                            playerNum = args[1]
                            amount = args[2]
                            players = this_bot.getRoom().get_sorted_player_list()
                            if not playerNum.isnumeric():
                                pass
                            else:
                                playerNum = int(playerNum)
                            if not amount.isnumeric():
                                if len(amount) > 0 and amount[0] == '-':
                                    if amount[1:].isnumeric():
                                        amount = int(amount[1:]) * -1
                            else:
                                amount = int(amount)
                                
                            if not isinstance(playerNum, int) or not isinstance(amount, int):
                                await message.channel.send("Both player number and the penalty amount must be numbers. Do " + server_prefix + "penalty for an example on how to use this command.")
                            elif playerNum < 1 or playerNum > len(players):
                                await message.channel.send("The player number must be on this list (between 1 and " + str(len(players)) + "). Do " + server_prefix + "penalty for an example on how to use this command.")
                            else:
                                this_bot.add_save_state(message.content)
                                this_bot.getRoom().addPlayerPenalty(players[playerNum-1][0], amount)
                                await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + lounge_add(players[playerNum-1][0]) + " given a " + str(amount) + " point penalty."))

                elif args[0] in TEAM_PENALTY_TERMS:
                    if not this_bot.table_is_set():
                        await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
                    else:
                        if this_bot.getWar().is_ffa():
                            await message.channel.send("You can't give team penalties in FFAs. Do " + server_prefix + "penalty to give an individual player a penalty in an FFA.")
                        elif len(args) == 1:
                            teams = sorted(this_bot.getWar().getTags())
                            to_send = ""
                            for team_num, team in enumerate(teams, 1):
                                to_send += UtilityFunctions.process_name(str(team_num)) + ". " + team + "\n"
                            to_send += "\n**To give the 2nd team on the list a 15 point penalty:** *" + server_prefix + "teampenalty 2 15*"
                            await message.channel.send(to_send)
                        elif len(args) != 3:
                            await message.channel.send("Do " + server_prefix + "teampenalty for an example on how to use this command.")
                        elif len(args) == 3:
                            teamNum = args[1]
                            amount = args[2]
                            teams = sorted(this_bot.getWar().getTags())
                            if not teamNum.isnumeric():
                                for ind, team in enumerate(teams):
                                    if team.lower() == teamNum:
                                        teamNum = ind + 1
                                        break
                            else:
                                teamNum = int(teamNum)
                            if not amount.isnumeric():
                                if len(amount) > 0 and amount[0] == '-':
                                    if amount[1:].isnumeric():
                                        amount = int(amount[1:]) * -1
                            else:
                                amount = int(amount)
                            
                            
                            if not isinstance(teamNum, int) or not isinstance(amount, int):
                                await message.channel.send("Both the team number and the penalty amount must be numbers. Do " + server_prefix + "teampenalty for an example on how to use this command.")
                            elif teamNum < 1 or teamNum > len(teams):
                                await message.channel.send("The team number must be on this list (between 1 and " + str(len(teams)) + "). Do " + server_prefix + "teampenalty for an example on how to use this command.")
                            else:
                                this_bot.add_save_state(message.content)
                                this_bot.getWar().addTeamPenalty(teams[teamNum-1], amount)
                                await message.channel.send(UtilityFunctions.process_name(teams[teamNum-1] + " given a " + str(amount) + " point penalty."))

                elif args[0] in FCS_TERMS:
                    if not this_bot.table_is_set() or not this_bot.getRoom().is_initialized():
                        await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
                    else:
                        await message.channel.send(this_bot.getRoom().getFCPlayerListString())
                    
                elif args[0] in GET_FLAG_TERMS:
                    flag = UserDataProcessing.get_flag(author_id)
                    if flag == None:
                        await message.channel.send(f"You don't have a flag set. Use {server_prefix}setflag [flag] to set your flag for tables. Flag codes can be found at: {LORENZI_FLAG_PAGE_URL_NO_PREVIEW}")
                    else:
                        image_name = ""
                        if flag.startswith("cl_") and flag.endswith("u"):
                            image_name += 'cl_C3B1u.png'
                        else:
                            image_name += f"{flag}.png"
                            
                        embed = discord.Embed(colour = discord.Colour.dark_blue())
                        file = discord.File(f"{FLAG_IMAGES_PATH}{image_name}", filename=image_name)
                        embed.set_thumbnail(url=f"attachment://{image_name}")
                        await message.channel.send(file=file, embed=embed)
                        
                elif args[0] in LOUNGE_NAME_TERMS:
                    discordIDToLoad = str(author_id)
                    await updateData(* await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad]) )
                    lounge_name = UserDataProcessing.get_lounge(author_id)
                    if lounge_name == None:
                        await message.channel.send("You don't have a lounge name. Join Lounge! (If you think this is an error, go on Wiimfi and try running this command again.)")
                    else:
                        await message.channel.send("Your lounge name is: " + UtilityFunctions.process_name(str(lounge_name)))
                        
                elif args[0] in SET_FLAG_TERMS:
                    if len(args) > 1:
                        #if 2nd argument is numeric, it's a discord ID
                        if args[1].isnumeric(): #This is an admin attempt
                            if str(author_id) in UtilityFunctions.botAdmins:
                                if len(args) == 2 or args[2] == "none":
                                    UserDataProcessing.add_flag(args[1], "")
                                    await message.channel.send(str(args[1] + "'s flag was successfully removed."))
                                else:
                                    UserDataProcessing.add_flag(args[1], args[2].lower())
                                    await message.channel.send(str(args[1] + "'s flag was successfully added and will now be displayed on tables."))
                            elif author_id in user_flag_exceptions:
                                flag = UserDataProcessing.get_flag(int(args[1]))
                                if flag == None:
                                    UserDataProcessing.add_flag(args[1], args[2].lower())
                                    await message.channel.send(str(args[1] + "'s flag was successfully added and will now be displayed on tables."))
                                else:
                                    await message.channel.send("This person already has a flag set.")
                            else:
                                await message.channel.send("You are not a bot admin, nor do you have an exception for adding flags.")
    
                        elif len(args) >= 2:
                            if args[1].lower() not in UserDataProcessing.valid_flag_codes:
                                await message.channel.send(f"This is not a valid flag code. For a list of flags and their codes, please visit: {LORENZI_FLAG_PAGE_URL_NO_PREVIEW}")
                            elif args[1].lower() == "none":
                                UserDataProcessing.add_flag(author_id, "")
                                await message.channel.send("Your flag was successfully removed.")
                            else:
                                UserDataProcessing.add_flag(author_id, args[1].lower())
                                await message.channel.send("Your flag was successfully added and will now be displayed on tables.")
                    elif len(args) == 1:
                        UserDataProcessing.add_flag(author_id, "")
                        await message.channel.send("Your flag was successfully removed.")
                    
                    
                elif args[0] in RXX_TERMS:
                    if not this_bot.table_is_set() or not this_bot.getRoom().is_initialized():
                        await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
                    else:
                        await message.channel.send(this_bot.getRoom().getRXXText())
                elif args[0] in SERVER_USAGE_TERMS:
                    if author_id == badwolf_id:
                        command_output = subprocess.check_output('top -b -o +%MEM | head -n 22', shell=True, text=True)
                        await message.channel.send(command_output)
                elif args[0] in TABLE_BOT_MEMORY_USAGE_TERMS:
                    if author_id == badwolf_id:
                        size_str = ""
                        print(f"get_size: Lounge table reports size (KiB):")
                        size_str += "Lounge table reports size (KiB): " + str(get_size(lounge_table_reports)//1024)
                        print(f"get_size: FC_DiscordID:")
                        size_str += "\nFC_DiscordID (KiB): " + str(get_size(UserDataProcessing.FC_DiscordID)//1024)
                        print(f"get_size: discordID_Lounges:")
                        size_str += "\ndiscordID_Lounges (KiB): " + str(get_size(UserDataProcessing.discordID_Lounges)//1024)
                        print(f"get_size: discordID_Flags (KiB):")
                        size_str += "\ndiscordID_Flags (KiB): " + str(get_size(UserDataProcessing.discordID_Flags)//1024)
                        print(f"get_size: blacklisted_Users (KiB):")
                        size_str += "\nblacklisted_Users (KiB): " + str(get_size(UserDataProcessing.blacklisted_Users)//1024)
                        print(f"get_size: valid_flag_codes (KiB):")
                        size_str += "\nvalid_flag_codes (KiB): " + str(get_size(UserDataProcessing.valid_flag_codes)//1024)
                        print(f"get_size: to_add_lounge (KiB):")
                        size_str += "\nto_add_lounge (KiB): " + str(get_size(UserDataProcessing.to_add_lounge)//1024)
                        print(f"get_size: to_add_fc (KiB):")
                        size_str += "\nto_add_fc (KiB): " + str(get_size(UserDataProcessing.to_add_fc)//1024)
                        print(f"get_size: bot_abuse_tracking (KiB):")
                        size_str += "\nbot_abuse_tracking (KiB): " + str(get_size(bot_abuse_tracking)//1024)
                        print(f"get_size: table_bots (KiB):")
                        size_str += "\ntable_bots (KiB): " + str(get_size(table_bots)//1024)
                        print(f"get_size: PROCESS SIZE (KiB) (virt):")
                        size_str += "\nPROCESS SIZE (KiB) (virt): " + str((psutil.Process(os.getpid()).memory_info().vms)//1024)
                        print(f"get_size: PROCESS SIZE (KiB) (actual): ")
                        size_str += "\nPROCESS SIZE (KiB) (actual): " + str((psutil.Process(os.getpid()).memory_info().rss)//1024)
                        print(f"get_size: Done.")
                        await message.channel.send(size_str)
                
                elif args[0] in SET_PREFIX_TERMS:
                    if not message.author.guild_permissions.administrator:
                        await message.channel.send("Can't change prefix, you're not an administrator in this server.")
                    elif len(args) < 2:
                        await message.channel.send("Give a prefix. Prefix not changed.")
                    else:
                        end_prefix_cmd = message.content.lower().index("setprefix") + len("setprefix")
                        new_prefix = message.content[end_prefix_cmd:].strip("\n").strip()
                        if len(new_prefix) < 1:
                            await message.channel.send("Cannot set an empty prefix. Prefix not changed.")
                        else:
                            was_success = ServerFunctions.change_server_prefix(str(server_id), new_prefix)
                            if was_success:
                                await message.channel.send("Prefix changed to: " + new_prefix) 
                            else:
                                await message.channel.send("Errors setting prefix. Prefix not changed.")
                
                elif args[0] in ALL_PLAYERS_TERMS:
                    await commands.TablingCommands.all_players_command(message, this_bot, server_prefix, is_lounge_server)
                elif args[0] in FC_TERMS:
                    await commands.OtherCommands.fc_command(message, args, old_command)
                elif args[0] in MII_TERMS:
                    await commands.OtherCommands.mii_command(message, args, old_command)
                elif args[0] in SET_WAR_NAME_TERMS:
                    await commands.TablingCommands.set_war_name_command(message, this_bot, args, server_prefix, old_command)
                    
                elif args[0] in LOG_TERMS:
                    if len(args) > 1:
                        to_log = f"{message.author} - {message.author.id}: {command}"
                        log_text(to_log, FEEDBACK_LOGGING_TYPE)
                        await message.channel.send("Logged") 
                elif args[0] in GET_LOGS_TERMS:
                    if author_id == badwolf_id:
                        if os.path.exists(FEEDBACK_LOGS_FILE):
                            await message.channel.send(file=discord.File(FEEDBACK_LOGS_FILE))
                        if os.path.exists(ERROR_LOGS_FILE):
                            await message.channel.send(file=discord.File(ERROR_LOGS_FILE))
                        if os.path.exists(MESSAGE_LOGGING_FILE):
                            await message.channel.send(file=discord.File(MESSAGE_LOGGING_FILE))

                    else:
                        await message.channel.send("You are not Bad Wolf.")
    
    
                elif args[0] in RACES_TERMS:
                    if not this_bot.table_is_set() or not this_bot.getRoom().is_initialized():
                        await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
                    else:
                        await message.channel.send(this_bot.getRoom().get_races_string())
                
                elif args[0] in PLAYER_DISCONNECT_TERMS:
                    if not this_bot.table_is_set():
                        await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
                    elif len(args) == 1:
                        had_DCS, DC_List_String = this_bot.getRoom().getDCListString(this_bot.getWar().getNumberOfGPS(), True)
                        if had_DCS:
                            DC_List_String += "\nIf the first disconnection on this list was on results: **" + server_prefix + "dc 1 onresults**\n" +\
                            "If they were not on results, do **" + server_prefix + "dc 1 before**"
                        await message.channel.send(DC_List_String)  
                    else:
                        if len(args) < 3:
                            await message.channel.send("You must give a dc number on the list and if they were on results or not. Run " + server_prefix + "dcs for more information.")
                        else:
                            missing_per_race = this_bot.getRoom().getMissingOnRace(this_bot.getWar().numberOfGPs)
                            merged = list(itertools.chain(*missing_per_race))
                            disconnection_number = args[1]
                            if not disconnection_number.isnumeric():
                                await message.channel.send(UtilityFunctions.process_name(str(disconnection_number)) + " is not a number on the dcs list. Do " + server_prefix + "dcs for an example on how to use this command.")
                            elif int(disconnection_number) > len(merged):
                                await message.channel.send("There have not been this many DCs. Run " + server_prefix + "dcs to learn how to use this command.")  
                            elif int(disconnection_number) < 1:
                                await message.channel.send("You must give a DC number on the list. Run " + server_prefix + "dcs to learn how to use this command.")  
                            else:
                                disconnection_number = int(disconnection_number)
                                on_or_before = args[2].lower().strip("\n").strip()
                                race, index = 0, 0
                                counter = 0
                                for missing in missing_per_race:
                                    race += 1
                                    
                                    for _ in missing:
                                        counter += 1
                                        if counter == disconnection_number:
                                            break
                                        index+=1
        
                                    else:
                                        index=0
                                        continue
                                    break
                                player_fc = missing_per_race[race-1][index][0]
                                player_name = UtilityFunctions.process_name(str(missing_per_race[race-1][index][1]) + lounge_add(player_fc))
                                if on_or_before in ["on", "during", "midrace", "results", "onresults"]:
                                    this_bot.add_save_state(message.content)
                                    this_bot.getRoom().dc_on_or_before[race][player_fc] = 'on'
                                    await message.channel.send("Saved: " + player_name + ' was on results for race #' + str(race))                    
                                elif on_or_before in ["before", "prior", "beforerace", "notonresults", "noresults", "off"]:
                                    this_bot.add_save_state(message.content)
                                    this_bot.getRoom().dc_on_or_before[race][player_fc] = 'before'
                                    await message.channel.send("Saved: " + player_name + ' was not on results for race #' + str(race))                    
                                else:
                                    await message.channel.send('"' + UtilityFunctions.process_name(str(on_or_before)) + '" needs to be either "on" or "before". Do ' + server_prefix + "dcs for an example on how to use this command.")

                
                       
                #Admin commands     
                elif args[0] in DUMP_DATA_TERMS:
                    if author_id != badwolf_id:
                        await message.channel.send("You are not a Bad Wolf.")
                    else:
                        successful = await UserDataProcessing.dump_data()
                        pickle_tablebots()
                        if successful:
                            await message.channel.send("Completed.")        
                        else:
                            await message.channel.send("Failed.")         
                
                elif args[0] in BLACKLIST_USER_TERMS:
                    if str(author_id) not in UtilityFunctions.botAdmins:
                        await message.channel.send("You are not a bot admin.")
                    elif len(args) < 2:
                        await message.channel.send("Check command.")
                    elif len(args) == 2:
                        if UserDataProcessing.add_Blacklisted_user(args[1], ""):
                            await message.channel.send("Removed blacklist for " + old_command.split()[1])
                        else:
                            await message.channel.send("Blacklist failed.")
                    elif len(args) > 2:
                        if UserDataProcessing.add_Blacklisted_user(args[1], " ".join(old_command.split()[2:])):
                            await message.channel.send("Blacklisted " + args[1])
                        else:
                            await message.channel.send("Blacklist failed.") 
                        
                
                elif args[0] in UNDO_TERMS:
                    await commands.TablingCommands.undo_command(message, this_bot, server_prefix, is_lounge_server)
                elif args[0] in VERIFY_ROOM_TERMS:
                    if commands.vr_is_on:
                        await commands.OtherCommands.vr_command(this_bot, message, args, old_command)
                
                elif args[0] in WORLDWIDE_TERMS:
                    await commands.OtherCommands.wws_command(client, this_bot, message, args, old_command, ww_type=Race.RT_WW_ROOM_TYPE)
                
                elif args[0] in CTWW_TERMS:
                    await commands.OtherCommands.wws_command(client, this_bot, message, args, old_command, ww_type=Race.CTGP_CTWW_ROOM_TYPE)  
                
                elif args[0] in BATTLES_TERMS:
                    await commands.OtherCommands.wws_command(client, this_bot, message, args, old_command, ww_type=Race.BATTLE_ROOM_TYPE)
                
                elif args[0] in MERGE_ROOM_TERMS:
                    await commands.TablingCommands.merge_room_command(message, this_bot, args, server_prefix, is_lounge_server)
                
                elif args[0] in ADD_BOT_ADMIN_TERMS:
                    if author_id != badwolf_id:
                        await message.channel.send("**You are not allowed to add admins to the bot. Only BadWolf is.**") 
                    else:
                        await commands.BadWolfCommands.add_bot_admin_command(message, args)
                        
                elif args[0] in REMOVE_BOT_ADMIN_TERMS:
                    if author_id != badwolf_id:
                        await message.channel.send("**You are not allowed to remove admins to the bot. Only BadWolf is.**") 
                    else:
                        await commands.BadWolfCommands.remove_bot_admin_command(message, args)
    
                elif args[0] in BLACKLIST_WORD_TERMS:
                    await commands.BotAdminCommands.add_blacklisted_word_command(message, args)
                
                elif args[0] in REMOVE_BLACKLISTED_WORD_TERMS:
                    await commands.BotAdminCommands.remove_blacklisted_word_command(message, args)
                            
                
                elif args[0] in TABLE_THEME_TERMS:
                    await commands.TablingCommands.table_theme_command(message, this_bot, args, server_prefix, is_lounge_server)
                elif args[0] in SERVER_DEFAULT_TABLE_THEME_TERMS:
                    await commands.ServerDefaultCommands.theme_setting_command(message, this_bot, args, server_prefix)
                elif args[0] in GRAPH_TERMS:
                    await commands.TablingCommands.table_graph_command(message, this_bot, args, server_prefix, is_lounge_server)
                
                elif args[0] in SERVER_DEFAULT_GRAPH_TERMS:
                    await commands.ServerDefaultCommands.graph_setting_command(message, this_bot, args, server_prefix)
                
                elif args[0] in SERVER_DEFAULT_MII_TERMS:
                    await commands.ServerDefaultCommands.mii_setting_command(message, this_bot, args, server_prefix)
               
                elif args[0] in SERVER_DEFAULT_LARGE_TIME_TERMS:
                    await commands.ServerDefaultCommands.large_time_setting_command(message, this_bot, args, server_prefix)

                elif args[0] in DISPLAY_GP_SIZE_TERMS:
                    await commands.TablingCommands.gp_display_size_command(message, this_bot, args, server_prefix, is_lounge_server)
                else:
                    await message.channel.send(f"Not a valid command. For more help, do the command: {server_prefix}help")  
                
                

    except discord.errors.Forbidden:
        if message.author.id in update_cooldowns:
            del update_cooldowns[message.author.id]
        try:
            await message.channel.send("MKW Table Bot is missing permissions and cannot do this command. Contact your admins. The bot needs the following permissions:\n- Send Messages\n- Read Message History\n- Manage Messages (Lounge only)\n- Add Reactions\n- Manage Reactions\n- Embed Links\n- Attach files\n\nIf the bot has all of these permissions, make sure you're not overriding them with a role's permissions. If you can't figure out your role permissions, granting the bot Administrator role should work.")
        except discord.errors.Forbidden: #We can't send messages
            pass
    except TableBotExceptions.WarSetupStillRunning:
        try:
            await message.channel.send("I'm still trying to set up your war. Please wait until I respond with a confirmation. If you think it has been too long since I've responded, you can try ?reset and start your war again.")
        except discord.errors.Forbidden: #We can't send messages
            pass
    except discord.errors.DiscordServerError:
        await message.channel.send("Discord's servers are either down or struggling, so I cannot send table pictures right now. Wait a few minutes for the issue to resolve.")
    except aiohttp.client_exceptions.ClientOSError:
        await message.channel.send("Discord's servers had an error. This is usually temporary, so do your command again.")
    except:
        with open(ERROR_LOGS_FILE, "a+") as f:
            f.write(f"\n{str(datetime.now())}: \n")
            traceback.print_exc(file=f)
        if message.author.id in update_cooldowns:
            del update_cooldowns[message.author.id]
        await message.channel.send(f"Internal bot error. An unknown problem occurred. Please use {server_prefix}log to tell me what happened. Please wait 1 minute before sending another command. If this issue continues, try: {server_prefix}reset")
        raise
    else:
        if has_pref: #No exceptions, and we did send a response, so online
            pass


#Read discord.py's documentation of on_ready function to understand why certain things are done in this function
@client.event
async def on_ready():
    global user_flag_exceptions
    global finished_on_ready
    
    if not finished_on_ready:
        load_lounge_updates()
        load_tablebot_pickle()
        load_CTGP_region_pickle()
        commands.load_vr_is_on()
        load_bad_wolf_facts_pkl()
    updatePresence.start()
    removeInactiveTableBots.start()
    freeFinishedTableBotsLounge.start()
    stay_alive_503.start()
    
    user_flag_exceptions.clear()
    user_flag_exceptions.update(UserDataProcessing.read_flag_exceptions())
    
    dumpDataAndBackup.start()
    checkBotAbuse.start()
    finished_on_ready = True
    
    
    
#Rotates the bot's status every 30 seconds with various information
@tasks.loop(seconds=30)
async def updatePresence():
    global switch_status
    game_str = ""
    if switch_status:
        game_str = "?quickstart for the basics, ?help for documentation"
    else:
        game_str = f"{str(getNumActiveWars())} active table"
        if getNumActiveWars() != 1:
            game_str += 's'
    
    switch_status = not switch_status
    
    game = discord.Game(game_str)
    await client.change_presence(status=discord.Status.online, activity=game)


#Every 60 seconds, checks to see if anyone was "spamming" the bot and notifies a private channel in my server
#Of the person(s) who were warned
#Also clears the abuse tracking every 60 seconds
@tasks.loop(seconds=60)
async def checkBotAbuse():
    global bot_abuse_tracking
    abuserIDs = set()
    
    for user_id, message_count in bot_abuse_tracking.items():
        if message_count > SPAM_THRESHOLD:
            if str(user_id) not in UserDataProcessing.blacklisted_Users:
                abuserIDs.add(str(user_id))
    bot_abuse_tracking.clear()
    
    
    if len(abuserIDs) > 0:
        await client.get_channel(BOT_ABUSE_REPORT_CHANNEL_ID).send(f"The following IDs were sending messages too quickly and were told to slow down: {', '.join(abuserIDs)}")
        

#This function will run every 15 min, removing any table bots that are
#inactive, as defined by TableBot.isinactive() (currently 2.5 hours)
@tasks.loop(minutes=15)
async def removeInactiveTableBots():
    to_remove = []
    for server_id in table_bots:
        for channel_id in table_bots[server_id]:
            if table_bots[server_id][channel_id].isInactive(): #if the table bot is inactive, delete it
                to_remove.append((server_id, channel_id))
                
    for (serv_id, chan_id)in to_remove:
        del(table_bots[serv_id][chan_id])
        

#I found that sending a message every 5 minutes to a dedicated channel in my server
#helps prevent some timing out/disconnect problems
#This implies there might be a problem with discord.py's heartbeat functionality, but I'm not certain
@tasks.loop(minutes=5)
async def stay_alive_503():
    try:
        await client.get_channel(776031312048947230).send("Stay alive to prevent 503")
    except:
        pass

   
#This function will run every 1 minutes. It will remove any table bots that are
#"finished" in Lounge - the definition of what is finished can be found in the ChannelBot class
@tasks.loop(minutes=1)
async def freeFinishedTableBotsLounge():
    if lounge_server_id in table_bots:
        for lounge_bot_channel_id in table_bots[lounge_server_id]:
            if table_bots[lounge_server_id][lounge_bot_channel_id].isFinishedLounge(): #if the table bot is inactive, delete it
                table_bots[lounge_server_id][lounge_bot_channel_id].freeLock()
                

            
            
    
#because this function can be called randomly, we won't load in the pickles if they are at initial values
def load_lounge_updates():   
    global lounge_table_id_counter
    global lounge_table_reports
    
    if len(lounge_table_reports) == 0:
        if os.path.exists(LOUNGE_ID_COUNTER_FILE):
            with open(LOUNGE_ID_COUNTER_FILE, "rb") as pickle_in:
                try:
                    lounge_table_id_counter = p.load(pickle_in)
                except:
                    print("Could not read in the pickle for lounge update table counter.")
                    
        
        if os.path.exists(LOUNGE_TABLE_UPDATES_FILE):
            with open(LOUNGE_TABLE_UPDATES_FILE, "rb") as pickle_in:
                try:
                    lounge_table_reports = p.load(pickle_in)
                except:
                    print("Could not read in the pickle for lounge update tables.")


def load_tablebot_pickle():
    global table_bots
    if os.path.exists(TABLE_BOT_PKL_FILE):
        with open(TABLE_BOT_PKL_FILE, "rb") as pickle_in:
            try:
                table_bots = p.load(pickle_in)
            except:
                print("Could not read in the pickle for table bots.")

def load_CTGP_region_pickle():
    if os.path.exists(CTGP_REGION_FILE):
        with open(CTGP_REGION_FILE, "rb") as pickle_in:
            try:
                Race.CTGP_CTWW_ROOM_TYPE = p.load(pickle_in)
            except:
                print(f"Could not read in the CTGP_REGION for ?ctww command. Current region is: {Race.CTGP_CTWW_ROOM_TYPE}") 

      
def pickle_lounge_updates():
    if len(lounge_table_reports) > 0:
        with open(LOUNGE_ID_COUNTER_FILE, "wb") as pickle_out:
            try:
                p.dump(lounge_table_id_counter, pickle_out)
            except:
                print("Could not dump pickle for counter ID. Current counter", lounge_table_id_counter)
                
        with open(LOUNGE_TABLE_UPDATES_FILE, "wb") as pickle_out:
            try:
                p.dump(lounge_table_reports, pickle_out)
            except:
                print("Could not dump counter dictionary. Current dict:", lounge_table_reports)
                
def pkl_bad_wolf_facts():
    global bad_wolf_facts
    with open(BAD_WOLF_FACT_FILE, "wb") as pickle_out:
        try:
            p.dump(bad_wolf_facts, pickle_out)
        except:
            print("Could not dump pickle for bad wolf facts. Current facts:", '\n'.join(bad_wolf_facts))
            
def load_bad_wolf_facts_pkl():
    global bad_wolf_facts
    if os.path.exists(BAD_WOLF_FACT_FILE):
        with open(BAD_WOLF_FACT_FILE, "rb") as pickle_in:
            try:
                bad_wolf_facts = p.load(pickle_in)
            except:
                print("Could not read in the pickle for bad wolf facts.")
    
                
def pickle_tablebots():
    global table_bots
    if table_bots != None:
        with open(TABLE_BOT_PKL_FILE, "wb+") as pickle_out:
            try:
                p.dump(table_bots, pickle_out)
                return
            except:
                print("Could not dump pickle for table bots. Exception occurred.")
    
    print("Could not dump pickle for table bots. None existed.") 
    
def pickle_CTGP_region():
    with open(CTGP_REGION_FILE, "wb+") as pickle_out:
        try:
            p.dump(Race.CTGP_CTWW_ROOM_TYPE, pickle_out)
            return
        except:
            print("Could not dump pickle for CTGP region for ?ctww. Exception occurred.")

def save_data():
    print(f"{str(datetime.now())}: Saving data")
    successful = UserDataProcessing.non_async_dump_data()
    if not successful:
        print("LOUNGE API DATA DUMP FAILED! CRITICAL!")
        log_text("LOUNGE API DATA DUMP FAILED! CRITICAL!", ERROR_LOGGING_TYPE)
    pickle_tablebots()
    pickle_CTGP_region()
    pickle_lounge_updates()
    pkl_bad_wolf_facts()
    Stats.backup_files()
    Stats.dump_to_stats_file()
    

def get_size(objct, seen=None):
    
    """Recursively finds size of objects"""
    if seen is None:
        seen = set()

    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    all_objects = [objct]
    total_size = 0
    while len(all_objects) > 0:
        cur_obj = all_objects.pop(0)
        obj_id = id(cur_obj)
        if obj_id in seen:
            continue
        seen.add(obj_id)
        total_size += sys.getsizeof(cur_obj)
        
        if isinstance(cur_obj, dict):
            for k, v in cur_obj.items():
                all_objects.append(k)
                all_objects.append(v)
                if isinstance(v, NavigableString):
                    print("Navigable String:", k)
                
        elif hasattr(cur_obj, '__dict__'):
            all_objects.append(cur_obj.__dict__)
        elif hasattr(cur_obj, '__iter__') and not isinstance(cur_obj, (str, bytes, bytearray)):
            for i in cur_obj:
                all_objects.append(i)
    return total_size

def log_command_sent(message:discord.Message):
    log_text(f"Sever: {message.guild} - Channel: {message.channel} - User: {message.author} - Command: {message.content}")

#This function dumps everything we have pulled recently from the API
#in our two dictionaries to local storage and the main dictionaries      
@tasks.loop(hours=24)
async def dumpDataAndBackup():
    save_data()


def handler(signum, frame):
    sys.exit()

signal.signal(signal.SIGINT, handler)

atexit.register(save_data)

initialize()
if in_testing_server:
    client.run(testing_bot_key)
else:
    client.run(real_bot_key)
    

