#Internal imports (stuff I coded) for this file
import ServerFunctions
import Stats
import LoungeAPIFunctions
import UserDataProcessing
import TableBot
import UtilityFunctions
import Race
import help_documentation
import commands
import Lounge
import TableBotExceptions
import common
import MogiUpdate
#External library imports for this file
import discord
from discord.ext import tasks
import traceback
import copy
import sys
import atexit
import signal
import dill as p
import psutil
import random
from bs4 import NavigableString
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import os

finished_on_ready = False



CT_WAR_LOUNGE_ECHELONS_CAT_ID = 851666104228249652
WAR_LOUNGE_ECHELONS_CAT_ID = 751956338912788559
WAR_LOUNGE_COMP_DISC_CAT_ID = 751956337612685405
LOUNGE_ECHELONS_CAT_ID = 389250562836922378
LOUNGE_ECHELONS_CT_CAT_ID = 520790337443332104
LOUNGE_COMP_DISC_ID = 455763458483421194
TEMPORARY_VR_CATEGORIES = [LOUNGE_COMP_DISC_ID, LOUNGE_ECHELONS_CAT_ID, LOUNGE_ECHELONS_CT_CAT_ID, WAR_LOUNGE_COMP_DISC_CAT_ID, WAR_LOUNGE_ECHELONS_CAT_ID, CT_WAR_LOUNGE_ECHELONS_CAT_ID]

real_bot_key = None
beta_bot_key = None
testing_bot_key = None
bot_invite_link = "https://discord.com/api/oauth2/authorize?client_id=735782213118853180&permissions=116800&scope=bot"


#These commands modify the table
RESET_TERMS = {"reset", "restart", "cancel", "quit", "stop", "clear"}
START_WAR_TERMS = {"startwar", "sw", "starttable"}
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


switch_status = True

table_bots = {}
user_flag_exceptions = set()

lounge_submissions = Lounge.Lounge(common.LOUNGE_ID_COUNTER_FILE, common.LOUNGE_TABLE_UPDATES_FILE, common.MKW_LOUNGE_SERVER_ID, common.main_lounge_can_report_table)

if common.in_testing_server:
    common.MKW_LOUNGE_SERVER_ID = common.BAD_WOLF_SERVER_ID
    MogiUpdate.rt_summary_channels.clear()
    MogiUpdate.rt_summary_channels.update({"1":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "2":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "3":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "4":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "4-5":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "5":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "6":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "7":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "squadqueue":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID})
    MogiUpdate.ct_summary_channels.clear()
    MogiUpdate.ct_summary_channels.update({"1":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "2":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "3":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "4":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "4-5":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "5":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "6":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "7":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID, "squadqueue":common.BAD_WOLF_SERVER_NORMAL_TESTING_THREE_CHANNEL_ID})
    common.mkw_lounge_staff_roles.clear()
    common.mkw_lounge_staff_roles.update(common.BAD_WOLF_SERVER_STAFF_ROLES)
    lounge_submissions = Lounge.Lounge(common.LOUNGE_ID_COUNTER_FILE, common.LOUNGE_TABLE_UPDATES_FILE, common.BAD_WOLF_SERVER_ID, common.main_lounge_can_report_table)
    lounge_submissions.channels_mapping = common.TESTING_SERVER_LOUNGE_UPDATES

elif common.running_beta:
    common.MKW_LOUNGE_SERVER_ID = common.BAD_WOLF_SERVER_ID
    MogiUpdate.rt_summary_channels.clear()
    MogiUpdate.rt_summary_channels.update({"1":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "2":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "3":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "4":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "4-5":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "5":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "6":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "7":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "squadqueue":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID})
    MogiUpdate.ct_summary_channels.clear()
    MogiUpdate.ct_summary_channels.update({"1":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "2":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "3":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "4":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "4-5":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "5":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "6":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "7":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID, "squadqueue":common.BAD_WOLF_SERVER_BETA_TESTING_THREE_CHANNEL_ID})
    common.mkw_lounge_staff_roles.clear()
    common.mkw_lounge_staff_roles.update(common.BAD_WOLF_SERVER_STAFF_ROLES)
    common.mkw_lounge_staff_roles.add(common.BAD_WOLF_SERVER_EVERYONE_ROLE_ID)
    lounge_submissions = Lounge.Lounge(common.LOUNGE_ID_COUNTER_FILE, common.LOUNGE_TABLE_UPDATES_FILE, common.BAD_WOLF_SERVER_ID, common.main_lounge_can_report_table)


bad_wolf_facts = []

def createEmptyTableBot(server_id=None):
    return TableBot.ChannelBot(server_id=server_id)

client = discord.Client()





def commandIsAllowed(isLoungeServer:bool, message_author:discord.Member, this_bot:TableBot.ChannelBot, command:str):
    
    if not isLoungeServer:
        return True
    
    
    for role in message_author.roles:
        if role.id in common.mkw_lounge_staff_roles:
            return True
    
    
    if this_bot is not None and this_bot.getWar() is not None and (this_bot.prev_command_sw or this_bot.manualWarSetUp):
        return this_bot.getRoom().getSetupUser() is None or this_bot.getRoom().getSetupUser() == message_author.id
    
    if command not in needPermissionCommands:
        return True
    
    if this_bot is None or this_bot.getRoom() is None or not this_bot.getRoom().is_initialized() or this_bot.getRoom().getSetupUser() is None:
        return True

    #At this point, we know the command's server is Lounge, it's not staff, and a room has been loaded
    #Check if the user was the setUpuser
    return this_bot.getRoom().canModifyTable(message_author.id)

    
def getNumActiveWars():
    inactivity_time_period_count = timedelta(minutes=30)
    num_wars = 0
    for s in table_bots:
        for c in table_bots[s]:
            if table_bots[s][c] is not None and table_bots[s][c].getWar() is not None:
                time_passed = datetime.now() - table_bots[s][c].last_used
                if time_passed < inactivity_time_period_count:
                    num_wars += 1
    return num_wars


#Strips the given prefix from the start of the command
#Note, the caller must ensure that the given string has a prefix by using has_prefix to ensure proper behaviour
#lstrip won't work here (go read the documentation and find a scenario that it wouldn't work in)
def strip_prefix(command, pref=common.default_prefix):
    new_command = command[len(pref):]
    return new_command

#Checks if the given string has the given prefix at the front of it
def has_prefix(command, pref=common.default_prefix):
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
            return True
        if len(new_prefix) > common.MAX_PREFIX_LENGTH:
            await message.channel.send(f"Prefixes must be {common.MAX_PREFIX_LENGTH} characters or less.")
            return True
        
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
    Path(common.MIIS_PATH).mkdir(parents=True, exist_ok=True)
    Path(common.SERVER_SETTINGS_PATH).mkdir(parents=True, exist_ok=True)
    Path(common.FLAG_IMAGES_PATH).mkdir(parents=True, exist_ok=True)
    Path(common.FONT_PATH).mkdir(parents=True, exist_ok=True)
    Path(common.HELP_PATH).mkdir(parents=True, exist_ok=True)
    Path(common.LOGGING_PATH).mkdir(parents=True, exist_ok=True)
    Path(common.TABLE_HEADERS_PATH).mkdir(parents=True, exist_ok=True)
    Path(common.DATA_PATH).mkdir(parents=True, exist_ok=True)

#Bring in the bot key and LoungeAPI key
def private_data_init():
    global real_bot_key
    global beta_bot_key
    global testing_bot_key
    with open(common.PRIVATE_INFO_FILE, "r") as f:
        real_bot_key = f.readline().strip("\n")
        beta_bot_key = f.readline().strip("\n")
        testing_bot_key = f.readline().strip("\n")
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
    
    if message.author == client.user:
        return
    if message.guild is None:
        return
    if not finished_on_ready:
        return
    
    has_pref = None
    server_prefix = common.default_prefix
    try:
        
        server_id = message.guild.id
        channel_id = message.channel.id
        author_id = message.author.id
        is_lounge_server = server_id == common.MKW_LOUNGE_SERVER_ID
        
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
        
        
        
        """if message.content.strip().lower() == 'addme':
            mkw_lounge_staff_roles.add(740659173695553667)
        elif message.content.strip().lower() == 'removeme':
            mkw_lounge_staff_roles.remove(740659173695553667)
        """
        
        
        if has_prefix:
            if len(args) > 0:
                if not commands.vr_is_on and (args[0] in VERIFY_ROOM_TERMS):
                    return

            
        if message.content.strip().lower() in ["?help"] or (client.user.mentioned_in(message) and 'help' in message.content.strip().lower()):
            if message.channel.category_id in TEMPORARY_VR_CATEGORIES:
                return
            if str(author_id) in UserDataProcessing.blacklisted_Users and author_id != common.BAD_WOLF_ID:
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
                if this_bot.getRoom() is not None:
                    if this_bot.getRoom().getSetupUser() is not None:
                        room_lounge_names = this_bot.getRoom().get_loungenames_can_modify_table()
                        to_send += ", ".join(room_lounge_names)
                        to_send += "**."
                    if this_bot.loungeFinishTime is None:
                        await message.channel.send(f"{to_send} Wait until they are finished.")  
                    else:
                        await message.channel.send(f"{to_send} {this_bot.getBotunlockedInStr()}")  
            else:
                
                if str(author_id) in UserDataProcessing.blacklisted_Users and author_id != common.BAD_WOLF_ID:
                    await message.channel.send(f"You have been blacklisted by a bot admin. You are not allowed to use this bot. Reason: {UserDataProcessing.blacklisted_Users[str(author_id)]}")
                
                elif args[0] in RESET_TERMS:
                    await commands.TablingCommands.reset_command(message, table_bots)
                                
                #Core commands
                elif this_bot.manualWarSetUp:
                    command = old_command
                    await commands.TablingCommands.manual_war_setup(message, this_bot, command)
                
                elif this_bot.prev_command_sw:
                    await commands.TablingCommands.after_start_war_command(message, this_bot, args, server_prefix)
                
                elif args[0] in GARBAGE_COLLECT_TERMS:
                    commands.BadWolfCommands.garbage_collect_command(message)
                    
                elif args[0] in ADD_BAD_WOLF_FACT_TERMS:
                    commands.BadWolfCommands.add_fact_command(message, command, bad_wolf_facts, pkl_bad_wolf_facts)
                    
                elif args[0] in REMOVE_BAD_WOLF_FACT_TERMS:
                    commands.BadWolfCommands.remove_fact_command(message, args, bad_wolf_facts, pkl_bad_wolf_facts)
                    
                elif args[0] in BAD_WOLF_FACT_TERMS:
                    commands.BadWolfCommands.send_all_facts_command(message, bad_wolf_facts)
                        
                elif args[0] in START_WAR_TERMS:
                    await commands.TablingCommands.start_war_command(message, this_bot, args, server_prefix, is_lounge_server, command, common.author_is_lounge_staff)
                
                elif args[0] in TABLE_TEXT_TERMS:
                    await commands.TablingCommands.table_text_command(message, this_bot, server_prefix, is_lounge_server)
                elif args[0] in WAR_PICTURE_TERMS:
                    await commands.TablingCommands.war_picture_command(message, this_bot, args, server_prefix, is_lounge_server)
                      
                        
                #Lounge reporting updates
                elif args[0] in TOTAL_CLEAR_TERMS:
                    await commands.BadWolfCommands.total_clear_command(message, lounge_submissions)
                         
                elif args[0] in LOUNGE_RT_MOGI_UPDATE_TERMS:
                    await commands.LoungeCommands.rt_mogi_update(client, this_bot, message, args, lounge_submissions)
                
                elif args[0] in LOUNGE_CT_MOGI_UPDATE_TERMS:
                    await commands.LoungeCommands.ct_mogi_update(client, this_bot, message, args, lounge_submissions)
                    
            
                elif args[0] in LOUNGE_TABLE_SUBMISSION_APPROVAL_TERMS:
                    await commands.LoungeCommands.approve_submission_command(client, message, args, lounge_submissions)
                    
                elif args[0] in LOUNGE_TABLE_SUBMISSION_DENY_TERMS:
                    await commands.LoungeCommands.approve_submission_command(client, message, args, lounge_submissions)
                    
                elif args[0] in LOUNGE_PENDING_TABLE_SUBMISSION_TERMS:
                    await commands.LoungeCommands.pending_submissions_command(message, lounge_submissions)
                    
                #Fun commands
                elif args[0] in STATS_TERMS:
                    num_wars = getNumActiveWars()
                    stats_str = Stats.stats(num_wars, client)
                    if stats_str is None:
                        await message.channel.send("Error fetching stats. Try again.")
                    else:
                        await message.channel.send(stats_str)
                
                elif (args[0] in ["badwolf"]) or (len(args) > 1 and (args[0] in ["bad"] and args[1] in ["wolf"])):
                    await message.channel.send(file=discord.File(common.BADWOLF_PICTURE_FILE))    
                
                elif args[0] in INVITE_TERMS:
                    await message.channel.send(bot_invite_link)              
                
                
                #Informational commands
                elif args[0] in GET_LOCK_TERMS and is_lounge_server:
                    await commands.LoungeCommands.get_lock_command(message, this_bot)
                
                elif args[0] in TRANSFER_LOCK_TERMS and is_lounge_server:
                    await commands.LoungeCommands.transfer_lock_command(message, args, this_bot)
                    
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
                    await commands.TablingCommands.change_player_score_command(message, this_bot, args, server_prefix, is_lounge_server, command)
                
                elif args[0] in PLAYER_PENALTY_TERMS:
                    await commands.TablingCommands.player_penalty_command(message, this_bot, args, server_prefix, is_lounge_server)
                
                elif args[0] in TEAM_PENALTY_TERMS:
                    await commands.TablingCommands.team_penalty_command(message, this_bot, args, server_prefix, is_lounge_server)
                
                elif args[0] in FCS_TERMS:
                    await commands.TablingCommands.fcs_command(message, this_bot, args, server_prefix, is_lounge_server)
                    
                elif args[0] in GET_FLAG_TERMS:
                    await commands.OtherCommands.get_flag_command(message, server_prefix)
                        
                elif args[0] in LOUNGE_NAME_TERMS:
                    await commands.OtherCommands.lounge_name_command(message)
                    
                elif args[0] in SET_FLAG_TERMS:
                    await commands.OtherCommands.set_flag_command(message, args, user_flag_exceptions)
                    
                elif args[0] in RXX_TERMS:
                    await commands.TablingCommands.rxx_command(message, this_bot, server_prefix, is_lounge_server)
                        
                elif args[0] in SERVER_USAGE_TERMS:
                    await commands.BadWolfCommands.server_process_memory_command(message)
                
                elif args[0] in TABLE_BOT_MEMORY_USAGE_TERMS:
                    commands.BadWolfCommands.is_badwolf_check(message.author, "cannot display table bot internal memory usage")
                    size_str = ""
                    print(f"get_size: Lounge table reports size (KiB):")
                    size_str += "Lounge submission tracking size (KiB): " + str(get_size(lounge_submissions)//1024)
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
                    size_str += "\nbot_abuse_tracking (KiB): " + str(get_size(common.bot_abuse_tracking)//1024)
                    print(f"get_size: table_bots (KiB):")
                    size_str += "\ntable_bots (KiB): " + str(get_size(table_bots)//1024)
                    print(f"get_size: PROCESS SIZE (KiB) (virt):")
                    size_str += "\nPROCESS SIZE (KiB) (virt): " + str((psutil.Process(os.getpid()).memory_info().vms)//1024)
                    print(f"get_size: PROCESS SIZE (KiB) (actual): ")
                    size_str += "\nPROCESS SIZE (KiB) (actual): " + str((psutil.Process(os.getpid()).memory_info().rss)//1024)
                    print(f"get_size: Done.")
                    await message.channel.send(size_str)
            
                elif args[0] in SET_PREFIX_TERMS:
                    await commands.ServerDefaultCommands.change_server_prefix_command(message, args)
                    
                elif args[0] in ALL_PLAYERS_TERMS:
                    await commands.TablingCommands.all_players_command(message, this_bot, server_prefix, is_lounge_server)
                
                elif args[0] in FC_TERMS:
                    await commands.OtherCommands.fc_command(message, args, old_command)
                
                elif args[0] in MII_TERMS:
                    await commands.OtherCommands.mii_command(message, args, old_command)
                
                elif args[0] in SET_WAR_NAME_TERMS:
                    await commands.TablingCommands.set_war_name_command(message, this_bot, args, server_prefix, is_lounge_server, command)
                    
                elif args[0] in LOG_TERMS:
                    await commands.OtherCommands.log_feedback_command(message, args, command)
                
                elif args[0] in GET_LOGS_TERMS:
                    await commands.BadWolfCommands.get_logs_command(message)
    
    
                elif args[0] in RACES_TERMS:
                    await commands.TablingCommands.display_races_played_command(message, this_bot, server_prefix, is_lounge_server)
                
                elif args[0] in PLAYER_DISCONNECT_TERMS:
                    await commands.TablingCommands.disconnections_command(message, this_bot, args, server_prefix, is_lounge_server)
                       
                #Admin commands     
                elif args[0] in DUMP_DATA_TERMS:
                    await commands.BadWolfCommands.dump_data_command(message, pickle_tablebots)
                
                elif args[0] in BLACKLIST_USER_TERMS:
                    await commands.BotAdminCommands.blacklist_user_command(message, args, command)
                        
                elif args[0] in UNDO_TERMS:
                    await commands.TablingCommands.undo_command(message, this_bot, server_prefix, is_lounge_server)
                
                elif args[0] in VERIFY_ROOM_TERMS:
                    if commands.vr_is_on:
                        await commands.OtherCommands.vr_command(this_bot, message, args, old_command, createEmptyTableBot()) #create a new one so it won't interfere with any room they might have loaded (like a table)
                
                elif args[0] in WORLDWIDE_TERMS:
                    await commands.OtherCommands.wws_command(client, this_bot, message, ww_type=Race.RT_WW_ROOM_TYPE)
                
                elif args[0] in CTWW_TERMS:
                    await commands.OtherCommands.wws_command(client, this_bot, message, ww_type=Race.CTGP_CTWW_ROOM_TYPE)  
                
                elif args[0] in BATTLES_TERMS:
                    await commands.OtherCommands.wws_command(client, this_bot, message, ww_type=Race.BATTLE_ROOM_TYPE)
                
                elif args[0] in MERGE_ROOM_TERMS:
                    await commands.TablingCommands.merge_room_command(message, this_bot, args, server_prefix, is_lounge_server)
                
                elif args[0] in ADD_BOT_ADMIN_TERMS:
                    await commands.BadWolfCommands.add_bot_admin_command(message, args)
                        
                elif args[0] in REMOVE_BOT_ADMIN_TERMS:
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
        lounge_submissions.clear_user_cooldown(message.author)
        await common.safe_send(message, "MKW Table Bot is missing permissions and cannot do this command. Contact your admins. The bot needs the following permissions:\n- Send Messages\n- Read Message History\n- Manage Messages (Lounge only)\n- Add Reactions\n- Manage Reactions\n- Embed Links\n- Attach files\n\nIf the bot has all of these permissions, make sure you're not overriding them with a role's permissions. If you can't figure out your role permissions, granting the bot Administrator role should work.")
    except TableBotExceptions.BlacklistedUser:
        pass #Already sent blacklisted message, if necessary
    except TableBotExceptions.NotBadWolf as not_bad_wolf_exception:
        await common.safe_send(message, f"You are not Bad Wolf: {not_bad_wolf_exception}")
    except TableBotExceptions.NotBotAdmin as not_bot_admin_exception:
        await common.safe_send(message, f"You are not a bot admin: {not_bot_admin_exception}")
    except TableBotExceptions.NotServerAdministrator as not_admin_failure:
        await common.safe_send(message, f"You are not a server administrator: {not_admin_failure}")
    except TableBotExceptions.NotStaff as not_staff_exception:
        await common.safe_send(message, f"You are not staff in this server: {not_staff_exception}")
    except TableBotExceptions.WrongServer:
        await common.safe_send(message, f"Not a valid command. For more help, do the command: {server_prefix}help")
    except TableBotExceptions.WrongUpdaterChannel as wrong_updater_channel_exception:
        await common.safe_send(message, f"Use this command in the appropriate updater channel: {wrong_updater_channel_exception}")
    except TableBotExceptions.WarSetupStillRunning:
        await common.safe_send(message, f"I'm still trying to set up your war. Please wait until I respond with a confirmation. If you think it has been too long since I've responded, you can try ?reset and start your war again.")
    except discord.errors.DiscordServerError:
        await common.safe_send(message, "Discord's servers are either down or struggling, so I cannot send table pictures right now. Wait a few minutes for the issue to resolve.")
    except aiohttp.client_exceptions.ClientOSError:
        await common.safe_send(message, "Discord's servers had an error. This is usually temporary, so do your command again.")       
    except:
        with open(common.ERROR_LOGS_FILE, "a+") as f:
            f.write(f"\n{str(datetime.now())}: \n")
            traceback.print_exc(file=f)

        lounge_submissions.clear_user_cooldown(message.author)
        await common.safe_send(message, f"Internal bot error. An unknown problem occurred. Please use {server_prefix}log to tell me what happened. Please wait 1 minute before sending another command. If this issue continues, try: {server_prefix}reset")
        raise
    else:
        if has_pref: #No exceptions, and we did send a response, so online
            pass


#Read discord.py's documentation of on_ready function to understand why certain things are done in this function
@client.event
async def on_ready():
    print(f"Logging in as {client.user}")
    global user_flag_exceptions
    global finished_on_ready
    
    if not finished_on_ready:
        load_tablebot_pickle()
        load_CTGP_region_pickle()
        commands.load_vr_is_on()
        load_bad_wolf_facts_pkl()
    
    common.set_bot_abuse_report_channel(client)
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
    abuserIDs = set()
    
    for user_id, message_count in common.bot_abuse_tracking.items():
        if message_count > common.SPAM_THRESHOLD:
            if str(user_id) not in UserDataProcessing.blacklisted_Users:
                abuserIDs.add(str(user_id))
    common.bot_abuse_tracking.clear()
    
    
    if len(abuserIDs) > 0:
        if common.BOT_ABUSE_REPORT_CHANNEL is not None:
            await common.BOT_ABUSE_REPORT_CHANNEL.send(f"The following IDs were sending messages too quickly and were told to slow down: {', '.join(abuserIDs)}")
        

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
    if common.MKW_LOUNGE_SERVER_ID in table_bots:
        for lounge_bot_channel_id in table_bots[common.MKW_LOUNGE_SERVER_ID]:
            if table_bots[common.MKW_LOUNGE_SERVER_ID][lounge_bot_channel_id].isFinishedLounge(): #if the table bot is inactive, delete it
                table_bots[common.MKW_LOUNGE_SERVER_ID][lounge_bot_channel_id].freeLock()
        

def load_tablebot_pickle():
    global table_bots
    if os.path.exists(common.TABLE_BOT_PKL_FILE):
        with open(common.TABLE_BOT_PKL_FILE, "rb") as pickle_in:
            try:
                table_bots = p.load(pickle_in)
            except:
                print("Could not read in the pickle for table bots.")

def load_CTGP_region_pickle():
    if os.path.exists(common.CTGP_REGION_FILE):
        with open(common.CTGP_REGION_FILE, "rb") as pickle_in:
            try:
                Race.CTGP_CTWW_ROOM_TYPE = p.load(pickle_in)
            except:
                print(f"Could not read in the CTGP_REGION for ?ctww command. Current region is: {Race.CTGP_CTWW_ROOM_TYPE}") 

      
def pickle_lounge_updates():
    lounge_submissions.dump_pkl()
    
def pkl_bad_wolf_facts():
    global bad_wolf_facts
    with open(common.BAD_WOLF_FACT_FILE, "wb") as pickle_out:
        try:
            p.dump(bad_wolf_facts, pickle_out)
        except:
            print("Could not dump pickle for bad wolf facts. Current facts:", '\n'.join(bad_wolf_facts))
            
def load_bad_wolf_facts_pkl():
    global bad_wolf_facts
    if os.path.exists(common.BAD_WOLF_FACT_FILE):
        with open(common.BAD_WOLF_FACT_FILE, "rb") as pickle_in:
            try:
                bad_wolf_facts = p.load(pickle_in)
            except:
                print("Could not read in the pickle for bad wolf facts.")
    
                
def pickle_tablebots():
    global table_bots
    if table_bots is not None:
        with open(common.TABLE_BOT_PKL_FILE, "wb+") as pickle_out:
            try:
                p.dump(table_bots, pickle_out)
                return
            except:
                print("Could not dump pickle for table bots. Exception occurred.")
    
    print("Could not dump pickle for table bots. None existed.") 
    
def pickle_CTGP_region():
    with open(common.CTGP_REGION_FILE, "wb+") as pickle_out:
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
        common.log_text("LOUNGE API DATA DUMP FAILED! CRITICAL!", common.ERROR_LOGGING_TYPE)
    pickle_tablebots()
    pickle_CTGP_region()
    pickle_lounge_updates()
    pkl_bad_wolf_facts()
    Stats.backup_files()
    Stats.dump_to_stats_file()
    print(f"{str(datetime.now())}: Finished saving data")
    

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
    common.log_text(f"Sever: {message.guild} - Channel: {message.channel} - User: {message.author} - Command: {message.content}")

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
if common.in_testing_server:
    client.run(testing_bot_key)
elif common.running_beta:
    client.run(beta_bot_key)
else:
    client.run(real_bot_key)
    

