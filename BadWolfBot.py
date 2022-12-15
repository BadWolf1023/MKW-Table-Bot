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
import URLShortener
import AbuseTracking
import TagAIShell
from data_tracking import DataTracker
import InteractionUtils
from api import api_channelbot_interface, endpoints
import MiiPuller

#External library imports for this file
import discord
import time
from discord.ext import tasks
from discord.ext import commands as ext_commands
import traceback
import sys
import json
import atexit
import signal
import dill as p
import psutil
from bs4 import NavigableString
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import os
import asyncio
from typing import Dict
from fastapi import FastAPI
import uvicorn
from collections import defaultdict

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
bot_invite_picture = "https://media.discordapp.net/attachments/781249043623182406/911592069636685884/unknown.png"

#These commands modify the table
RESET_TERMS = {"reset", "restart", "cancel", "quit", "stop", "clear"}
START_WAR_TERMS = {"startwar", "sw", "starttable", "start"}
UNDO_TERMS = {"undo", "undocommand", "reverse"}
REDO_TERMS = {"redo", "redocommand"}
LIST_UNDOS_TERMS = {"undos", "getundos", "toundo"}
LIST_REDOS_TERMS = {"redos", "getredos", "toredo"}

#These commands also modify the table, but can be undone using the ?undo command
REMOVE_RACE_TERMS = {"removerace"}
SUBSTITUTE_TERMS = {"sub", "substitute"}
PLAYER_PENALTY_TERMS = {"pen", "penalty"}
TEAM_PENALTY_TERMS = {"teampen", "teampenalty", "tagpen", "tagpenalty"}
EDIT_PLAYER_SCORE_TERMS = {"edit"}
EDIT_FULL_GP_TERMS = {"fulledit", "editgp", "editall", "gpedit"}
PLAYER_DISCONNECT_TERMS = {"dc", "dcs"}
MERGE_ROOM_TERMS = {"mr", "mergeroom"}
SET_TABLE_NAME_TERMS = {"setwarname", "settablename"}
CHANGE_PLAYER_NAME_TERMS = {'changename', 'cn'}
CHANGE_PLAYER_TAG_TERMS = {'assignteam', 'changeteam', 'assigntag', 'changetag', 'setteam', 'settag', 'ct'}
CHANGE_ROOM_SIZE_TERMS = {'changeroomsize', "editroomsize", "forceroomsize", "crs"}
EARLY_DC_TERMS = {'earlydc'}
DEPRECATED_QUICK_EDIT_TERMS = {'quickedit', 'qe'}
QUICK_EDIT_TERMS = DEPRECATED_QUICK_EDIT_TERMS | {"changeplace", "changeposition", "cp"}
RACE_EDIT_TERMS = {'raceedit', 'editrace', 'racepositions', 'changerace'}
RACE_ORDER_TERMS = {'raceorder', 'changeraces', 'changeraceorder', 'racesorder', 'changeorder', 'order', 'changeracesorder'}

TABLE_THEME_TERMS = {'style', 'theme', 'tablestyle', 'tabletheme'}
GRAPH_TERMS = {'graph', 'tablegraph', 'graphtheme'}
DISPLAY_GP_SIZE_TERMS = {'size', 'tablesize', 'displaysize'}


#Commands that require a table to be started, but don't modify the war/room/table in any way
TABLE_TEXT_TERMS = {"tt", "tabletext"}
PREDICT_TERMS = {"predict", "preview"}
WAR_PICTURE_TERMS = {"wp", "warpicture", "wo", "w;", "w["}
RACE_RESULTS_TERMS = {"rr", "raceresults"}
RACES_TERMS = {"races", "tracks", "tracklist"}
RXX_TERMS = {"rxx", "rlid", "roomid"}
TABLE_ID_TERMS = {"tableid", "eventid", "id"}
ALL_PLAYERS_TERMS = {"allplayers", "ap"}
FCS_TERMS = {"fcs"}
TRANSFER_TABLE_TERMS = {"transferfrom", "copyfrom", "transfer", "copy", "copytable", "transfertable", "movetable", "move"}
GET_SUBSTITUTIONS_TERMS = {"subs", "substitutes", "substitutions", "getsubs", "allsubs"}
API_TERMS = {"api", "apilink", "obsoverlay", "overlay", "scoreboard"}

#Button interactions (only people in room can use buttons in Lounge; however, this isn't applied to the commands)
INTERACTIONS = {'restricted_interaction'}

#General commands that do not require a table to be started (stateless commands)
PAGE_TERMS = {"page", "pages", "playerpage", "playerpages"}
FC_TERMS = {"fc"}
LOUNGE_NAME_TERMS = {"lounge", "loungename", "ln"}
GET_FLAG_TERMS = {"getflag", "gf"}
SET_FLAG_TERMS = {"setflag", "sf"}
MII_TERMS = {"mii"}
PREVIOUS_MII_TERMS = {"pastmii", "oldmii", "previousmii"}
WORLDWIDE_TERMS = {"wws", "ww", "rtww", "rtwws", "worldwide", "worldwides"}
CTWW_TERMS = {"ctgpww", "ctgpwws", "ctwws", "ctww", "ctww", "ctwws", "ctworldwide", "ctworldwides", "customtrackworldwide", "customtrackworldwides"}
BATTLES_TERMS = {"battle", "battles", "btww", "btwws", "battleww", "battlewws", "battleworldwide", "battleworldwides"}
VERIFY_ROOM_TERMS = {"vr", "verifyroom"}
STATS_TERMS = {"stats", "stat"}
INVITE_TERMS = {"invite"}

#Player/Meta commands (also stateless)
POPULAR_TRACKS_TERMS = {"populartracks", "populartrack", "pt", "pts", "hottrack", "hottracks"}
UNPOPULAR_TRACKS_TERMS = {"unpopulartracks", "unpopulartrack", "upt", "upts", "unhottrack", "unhottracks", "coldtrack", "coldtracks"}
BEST_TRACK_TERMS = {"besttrack", "besttracks", "bt", "bts", "toptrack", "toptracks"}
WORST_TRACK_TERMS = {"worsttrack", "worsttracks", "wt"}
TOP_PLAYERS_TERMS = {"topplayers", "topplayer", "tp"}
RECORD_TERMS = {"record"}

#Informative, getting started/tutorial commands
QUICK_START_TERMS = {"quickstart"}
TUTORIAL_TERMS = {"tutorial"}
HELP_TERMS = {"help"}

#Lounge table submission commands
LOUNGE_RT_MOGI_UPDATE_TERMS = {'rtmogiupdate', 'rttableupdate', 'rtupdatemogi', 'rtupdate'}
LOUNGE_CT_MOGI_UPDATE_TERMS = {'ctmogiupdate', 'cttableupdate', 'ctupdatemogi', 'ctupdate'}
LOUNGE_MOGI_UPDATE_TERMS = LOUNGE_RT_MOGI_UPDATE_TERMS | LOUNGE_CT_MOGI_UPDATE_TERMS

#Lounge Reporter+ commands for table submissions
LOUNGE_TABLE_SUBMISSION_APPROVAL_TERMS = {"report", "approve", "accept", "a"}
LOUNGE_TABLE_SUBMISSION_DENY_TERMS =  {"deny", "reject", "d"}
LOUNGE_TABLE_SUBMISSION_TERMS = LOUNGE_TABLE_SUBMISSION_APPROVAL_TERMS |  LOUNGE_TABLE_SUBMISSION_DENY_TERMS
LOUNGE_PENDING_TABLE_SUBMISSION_TERMS = {"pending", "pendingsubmission", "pendingsubmissions", "p"}

#Lounge Staff Commands:
LOUNGE_WHO_IS_TERMS = {"whois"}

#Server administrator commands only
SERVER_SETTINGS_TERMS = {'settings', 'serversettings', 'sets', 'serversets'}
SET_PREFIX_TERMS = {"setprefix"}
SERVER_DEFAULT_TABLE_THEME_TERMS = {'defaulttheme', 'defaultservertheme', 'serverstyle', 'servertheme', 'servertablestyle', 'servertabletheme'}
SERVER_DEFAULT_GRAPH_TERMS = {'defaultgraph', 'defaultservergraph', 'servergraph', 'servertablegraph', 'servergraphtheme'}
SERVER_DEFAULT_MII_TERMS = {'defaultmii', 'servermii','servermiis','defaultservermiis','defaultmiis', 'defaultmiisetting', 'defaultmiisettings', 'miisetting'}
SERVER_DEFAULT_LARGE_TIME_TERMS = {'defaultlargetime','defaultlargetimes', 'defaultsui', 'defaultpsb', 'serverlargetimes', 'serverlargetime', 'serversui', 'serverpsb'}


#Bot Admin Only Commands
SET_CTGP_REGION_TERMS = {'set_ctgp_region'}
VR_ON_TERMS = {'vr_on'}
VR_OFF_TERMS = {'vr_off'}
BLACKLIST_USER_TERMS = {"blacklistuser"}
BLACKLIST_WORD_TERMS = {"blacklistword", "addblacklistedword", "addblacklistword", "addword"}
REMOVE_BLACKLISTED_WORD_TERMS = {"removeblacklistword", "removeblacklistedword", "removeword"}

#Bot Owner Commands only
SERVER_USAGE_TERMS = {"serverusage", "usage", "serverstats"}
TABLE_BOT_MEMORY_USAGE_TERMS = {"memory", "memoryusage"}
GARBAGE_COLLECT_TERMS = {"gc", "garbagecollect"}
TOTAL_CLEAR_TERMS = {'totalclear'}
DUMP_DATA_TERMS = {"dtt", "dothething"}
LOOKUP_TERMS = {"lookup"}
ADD_BOT_ADMIN_TERMS = {"addbotadmin", "addadmin"}
REMOVE_BOT_ADMIN_TERMS = {"removebotadmin", "removeadmin"}
GET_LOGS_TERMS = {"getlog", "getlogs", "logs"}
ADD_SHA_TERMS = {"addsha", "sha"}
REMOVE_SHA_TERMS = {"removesha", "delsha"}
RELOAD_PROPERTIES_TERMS = {"reloadproperties", "reload_properties", "propertyreload"}
SET_API_URL_TERMS = {"apiurl", "setapiurl", "api_url", "set_api_url"}



needPermissionCommands = DISPLAY_GP_SIZE_TERMS | TABLE_THEME_TERMS | GRAPH_TERMS | RESET_TERMS | START_WAR_TERMS | UNDO_TERMS | REDO_TERMS | LIST_REDOS_TERMS | LIST_UNDOS_TERMS | REMOVE_RACE_TERMS | PLAYER_PENALTY_TERMS | TEAM_PENALTY_TERMS | EDIT_PLAYER_SCORE_TERMS | PLAYER_DISCONNECT_TERMS | MERGE_ROOM_TERMS | SET_TABLE_NAME_TERMS | CHANGE_PLAYER_NAME_TERMS | CHANGE_PLAYER_TAG_TERMS | CHANGE_ROOM_SIZE_TERMS | EARLY_DC_TERMS | QUICK_EDIT_TERMS | SUBSTITUTE_TERMS | GET_SUBSTITUTIONS_TERMS | INTERACTIONS
ALLOWED_COMMANDS_IN_LOUNGE_ECHELONS = LOUNGE_MOGI_UPDATE_TERMS | STATS_TERMS | INVITE_TERMS | MII_TERMS | FC_TERMS | BATTLES_TERMS | CTWW_TERMS | WORLDWIDE_TERMS | VERIFY_ROOM_TERMS | SET_FLAG_TERMS | GET_FLAG_TERMS | POPULAR_TRACKS_TERMS | UNPOPULAR_TRACKS_TERMS | TOP_PLAYERS_TERMS | BEST_TRACK_TERMS | WORST_TRACK_TERMS | RECORD_TERMS

common.needPermissionCommands.update(needPermissionCommands)

finished_on_ready = False
REGISTER_SLASH_COMMANDS = True #whether the bot should register its slash commands (since there is no reason to use slash commands until April 2022)

intents = discord.Intents.default()
intents.typing = False
if common.is_dev:
    intents.message_content = True

SLASH_EXTENSIONS = [
    'slash_cogs.TablingSlashCommands', 
    'slash_cogs.AdminSlashCommands', 
    'slash_cogs.PrivateSlashCommands',
    'slash_cogs.LoungeSlashCommands', 
    'slash_cogs.MiscSlashCommands',
    'slash_cogs.StatisticsSlashCommands'
] 

switch_status = True

lounge_submissions = Lounge.Lounge(common.LOUNGE_ID_COUNTER_FILE, common.LOUNGE_TABLE_UPDATES_FILE, common.MKW_LOUNGE_SERVER_ID, common.author_is_reporter_plus)
if common.is_beta or common.is_dev:
    lounge_submissions = Lounge.Lounge(common.LOUNGE_ID_COUNTER_FILE, common.LOUNGE_TABLE_UPDATES_FILE, common.TABLE_BOT_DISCORD_SERVER_ID, lambda _: True)


def createEmptyTableBot(server_id=None, channel_id=None):
    return TableBot.ChannelBot(server_id=server_id, channel_id=channel_id)

def get_prefix(bot,msg: discord.Message) -> str:
    prefix = common.default_prefix
    if msg.guild is not None: 
        prefix = ServerFunctions.get_server_prefix(msg.guild.id)
    
    return ext_commands.when_mentioned_or(prefix)(bot, msg)

class BadWolfBot(ext_commands.Bot):
    def __init__(self):
        super().__init__(description="MKW Table Bot", owner_ids=common.OWNERS, intents=intents, chunk_guilds_at_startup=False) #debug_guilds=common.SLASH_GUILDS
        self.table_bots: Dict[int, Dict[int, TableBot.ChannelBot]] = defaultdict(dict)
        self.lounge_submissions = lounge_submissions
        self.mentions = None
        self.mii_cooldowns = {}
        # self.sug_views = {}
        # self.pic_views = {}

        if REGISTER_SLASH_COMMANDS:
            for ext in SLASH_EXTENSIONS:
                self.load_extension(ext)

    #Strips the given prefix from the start of the command
    #Note, the caller must ensure that the given string has a prefix by using has_prefix to ensure proper behaviour
    #lstrip won't work here (go read the documentation and find a scenario that it wouldn't work in)
    def strip_prefix(self, command, pref=common.default_prefix):
        if self.mentions[0] in command:
            new_command = command[len(self.mentions[0]):]
        elif self.mentions[1] in command:
            new_command = command[len(self.mentions[1]):]
        else:
            new_command = command[len(pref):]
        new_command = new_command.lstrip()
        return new_command

    #Checks if the given string has the given prefix at the front of it
    def has_prefix(self, command, pref=common.default_prefix):
        if type(command) != type(""):
            return False, False, None
        if len(command) < len(pref) and len(command) < len(self.mentions[1]):
            return False, False, None

        if command.startswith(self.mentions[0]) or command.startswith(self.mentions[1]):
            return True, True, f'@{self.user.name} '
        if command.startswith(pref):
            return True, False, pref
        return False, False, None

    def get_table_bots(self):
        return self.table_bots
    
    def should_send_help(self, message):
        content = message.content.strip().lower()
        return content in ["?help"] or (any([mention in content for mention in self.mentions]) and 'help' in content)
    
    async def send_mass_information(self):
        for num, guild in enumerate(self.guilds, start=1):
            for channel in guild.channels:
                try:
                    await channel.send("**IMPORTANT TABLE BOT INFORMATION**\n\nTable Bot does not support prefix commands anymore, only slash commands. Normal text commands using a prefix, like `?sw 2v2 6`, will no longer work.\n\n**If Table Bot slash commands do not pop up in your server, click Table Bot in the members list, and then click “Add to server”, and then follow the prompts. You __do not__ need to kick the bot first.** If you need help, please send a friend request on Discord to: **Bad Wolf#1288**\n\nIf you are struggling with slash commands:\n- Remember that the `/raw` slash command works for most things. Example: `/raw sw 2v2 6`\n- Mentioning the bot will always work as a prefix. Example: `@MKW Table Bot sw 2v2 6`\n\nAs discussed in the MKW Table Bot server, it was Discord’s decision to turn off normal text commands, not ours.")
                    print(f'{num}. GUILD: {guild.name} | CHANNEL: #{channel.name}')
                    break
                except:
                    pass

    async def on_ready(self):
        global finished_on_ready
        print("Logging in...")
        
        if not finished_on_ready:
            self.load_tablebot_pickle()
            load_CTGP_region_pickle()
            commands.load_vr_is_on()
            # await self.send_mass_information()
        
        AbuseTracking.set_bot_abuse_report_channel(self)
        common.ERROR_LOGS_CHANNEL = self.get_channel(common.ERROR_LOGS_CHANNEL_ID)


        try:
            self.updatePresence.start()
        except RuntimeError:
            print("UpdatePresence task has already been started.")
        try:
            self.removeInactiveTableBots.start()
        except RuntimeError:
            print("removeInactiveTableBots task already started.")
        try:
            self.freeFinishedTableBotsLounge.start()
        except RuntimeError:
            print("freeFinishedTableBots task already started")
        try:
            self.stay_alive_503.start()
        except RuntimeError:
            print("stay_alive task already started")
        try:
            self.prune_mii_cooldowns.start()
        except RuntimeError:
            print("prune_mii_cooldowns task already started")
        try:
            self.clear_mii_cache.start()
        except RuntimeError:
            print("clear_mii_cache task already started")
        try:
            self.update_valid_flags.start()
        except RuntimeError:
            pass
                
        try:
            self.dumpDataAndBackup.start()
        except RuntimeError:
            print("dumpData+Backup task already started")
        # try:
        #     checkBotAbuse.start()
        # except RuntimeError:
        #     print("checkBotAbuse task already started")
        

        self.mentions = [f'<@!{self.user.id}>', f'<@{self.user.id}>']
    
        finished_on_ready = True
        print(f"Logged in as {self.user}")
    
    @tasks.loop(hours=168)
    async def update_valid_flags(self):
        json_str = await common.get_request(common.LORENZI_FLAG_API, resp_type='text')
        flag_codes = json.loads(json_str)
        UserDataProcessing.valid_flag_codes = set(flag_codes)

        for flag_code in UserDataProcessing.valid_flag_codes:
            if not os.path.exists(image_path := common.FLAG_IMAGES_PATH + f"{flag_code}.png"):
                await common.download_image(common.LORENZI_FLAG_PIC_URL.format(flag_code), image_path)
    
    @tasks.loop(hours=2)
    async def clear_mii_cache(self):
        for fc in list(MiiPuller.MII_CACHE.keys())[::-1]:
            if (MiiPuller.cache_time_expired(MiiPuller.MII_CACHE[fc][1])):
                MiiPuller.MII_CACHE.pop(fc)
        
        for fc in list(MiiPuller.MII_PHOTO_CACHE.keys())[::-1]:
            if (MiiPuller.photo_cache_is_expired(MiiPuller.MII_PHOTO_CACHE[fc])):
                MiiPuller.MII_PHOTO_CACHE.pop(fc)
                common.delete_file(f"{common.MIIS_CACHE_PATH}{fc}.png")

    # For memory purposes; don't want dictionary to keep ballooning
    @tasks.loop(hours=8)
    async def prune_mii_cooldowns(self):
        for user, last_used in list(self.mii_cooldowns.items())[::-1]:
            if time.monotonic()-last_used > common.MII_COOLDOWN:
                self.mii_cooldowns.pop(user)

    #This function will run every 1 minute. It will remove any table bots that are
    #"finished" in Lounge - the definition of what is finished can be found in the ChannelBot class
    @tasks.loop(minutes=1)
    async def freeFinishedTableBotsLounge(self):
        lock_server_id = common.TABLE_BOT_DISCORD_SERVER_ID if common.is_beta else common.MKW_LOUNGE_SERVER_ID
        if lock_server_id in self.table_bots:
            for lounge_bot_channel_id in self.table_bots[lock_server_id]:
                if self.table_bots[lock_server_id][lounge_bot_channel_id].isFinishedLounge(): 
                    self.table_bots[lock_server_id][lounge_bot_channel_id].freeLock()

    #This function will run every 15 min, removing any table bots that are
    #inactive, as defined by TableBot.isinactive() (currently 2.5 hours)
    @tasks.loop(minutes=15)
    async def removeInactiveTableBots(self):
        to_remove = []
        for server_id in self.table_bots:
            for channel_id in self.table_bots[server_id]:
                if self.table_bots[server_id][channel_id].isInactive(): #if the table bot is inactive, delete it
                    to_remove.append((server_id, channel_id))
                    
        for (serv_id, chan_id) in to_remove:
            self.table_bots[serv_id][chan_id].destroy()
            del(self.table_bots[serv_id][chan_id])
    
    #This function dumps everything we have pulled recently from the API
    #in our two dictionaries to local storage and the main dictionaries      
    @tasks.loop(hours=24)
    async def dumpDataAndBackup(self):
        await self.save_data()

    def load_tablebot_pickle(self):
        if os.path.exists(common.TABLE_BOT_PKL_FILE):
            with open(common.TABLE_BOT_PKL_FILE, "rb") as pickle_in:
                try:
                    self.table_bots = defaultdict(dict, p.load(pickle_in))
                except:
                    print("Could not read in the pickle for table bots.")
    
    def pickle_tablebots(self):
        if self.table_bots is not None:
            with open(common.TABLE_BOT_PKL_FILE, "wb+") as pickle_out:
                try:
                    p.dump(self.table_bots, pickle_out)
                    return
                except:
                    print("Could not dump pickle for table bots. Exception occurred.")
        
        print("Could not dump pickle for table bots. None existed.")

    def pickle_lounge_updates(self):
        self.lounge_submissions.dump_pkl() 

    def destroy_all_tablebots(self):
        for server_id in self.table_bots:
            for channel_id in self.table_bots[server_id]:
                self.table_bots[server_id][channel_id].destroy()
    
    async def save_data(self):
        print(f"{str(datetime.now())}: Saving data...")
        successful = UserDataProcessing.non_async_dump_data()
        if not successful:
            print("LOUNGE API DATA DUMP FAILED! CRITICAL!")
            common.log_text("LOUNGE API DATA DUMP FAILED! CRITICAL!", common.ERROR_LOGGING_TYPE)
        DataTracker.save_data()
        Race.save_data()
        self.pickle_tablebots()
        pickle_CTGP_region()
        self.pickle_lounge_updates()
        Stats.save_metadata()
        if common.is_prod:
            Stats.backup_files()
            await Stats.prune_backups()
        
        print(f"{str(datetime.now())}: Finished saving data")
    
    #Rotates the bot's status every 30 seconds with various information
    @tasks.loop(seconds=30)
    async def updatePresence(self):
        global switch_status
        game_str = ""
        if switch_status:
            game_str = "?quickstart for the basics, ?help for documentation"
        else:
            game_str = f"{str(self.getNumActiveWars())} active table"
            if self.getNumActiveWars() != 1:
                game_str += 's'
        
        switch_status = not switch_status
        
        game = discord.Game(game_str)
        await self.change_presence(status=discord.Status.online, activity=game)
    
    def getNumActiveWars(self):
        inactivity_time_period_count = timedelta(minutes=30)
        num_wars = 0
        for s in self.table_bots:
            for c in self.table_bots[s]:
                if self.table_bots[s][c] is not None and self.table_bots[s][c].getWar() is not None:
                    time_passed = datetime.now() - self.table_bots[s][c].last_used
                    if time_passed < inactivity_time_period_count:
                        num_wars += 1
        return num_wars
    
    #I found that sending a message every 5 minutes to a dedicated channel in my server
    #helps prevent some timing out/disconnect problems
    #This implies there might be a problem with discord.py's heartbeat functionality, but I'm not certain
    async def send_to_503_channel(self, text):
        await self.get_channel(776031312048947230).send(text)
        
    @tasks.loop(minutes=5)
    async def stay_alive_503(self):
        try:
            await self.send_to_503_channel("Stay alive to prevent 503")
        except:
            pass
    
    #If there is a channel bot for a server and a channel already, return it
    #Otherwise, create a new one, store it, and return that one
    #May use defaultdicts in the future for better readability
    def check_create_channel_bot(self, message:discord.Message) -> TableBot.ChannelBot:
        server_id = message.guild.id
        channel_id = message.channel.id
        # if server_id not in self.table_bots:
        #     self.table_bots[server_id] = {}
        if channel_id not in self.table_bots[server_id]:
            self.table_bots[server_id][channel_id] = createEmptyTableBot(server_id, channel_id)
        self.table_bots[server_id][channel_id].updatedLastUsed()
        return self.table_bots[server_id][channel_id]

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.application_command:
            return 
        
        message = InteractionUtils.create_proxy_msg(interaction)
        command = interaction.data['name']

        log_command_sent(message)

        # await AbuseTracking.blacklisted_user_check(message)
        # if await AbuseTracking.abuse_track_check(message): 
        #     return

        is_lounge_server = InteractionUtils.simulating_lounge_server(interaction)
        
        if interaction.channel.category_id in TEMPORARY_VR_CATEGORIES and command not in ALLOWED_COMMANDS_IN_LOUNGE_ECHELONS:
            return
        
        this_bot = self.check_create_channel_bot(message)
        
        if not commandIsAllowed(is_lounge_server, interaction.user, this_bot, command):
            return await send_lounge_locked_message(message, this_bot)
            
        full_command_name = []
        command_level = interaction.data
        while command_level:
            full_command_name.append(command_level['name'])
            if "options" not in command_level: # check for nested options
                break

            new_level = None
            for option in command_level['options']:
                if 'options' in option: #there is a nested option
                    new_level = option
                    break
            command_level = new_level
        
        full_command_name = " ".join(full_command_name)
        Stats.log_command(full_command_name, message.author.id, slash=True)
        await self.process_application_commands(interaction)
    
    async def on_connect(self):
        try:
            return await super().on_connect()
        except discord.errors.Forbidden: # bot doesn't have application commands scope; this should be retroactively given in the future, so we ignore any 403 Forbidden - Missing Access errors
            pass
    
    async def slash_interaction_pre_invoke(self, ctx: discord.ApplicationContext, args=None):
        
        message = InteractionUtils.create_proxy_msg(ctx.interaction, ctx=ctx, args=args)

        is_lounge_server = InteractionUtils.simulating_lounge_server(message)
        
        this_bot = self.check_create_channel_bot(message)
        if is_lounge_server and this_bot.isFinishedLounge():
            this_bot.freeLock()

        name = ctx.command.full_parent_name + " " + ctx.interaction.data['name']
        name = common.SLASH_TERMS_CONVERSIONS.get(name, name)
        return name.strip(), message, this_bot, '/', is_lounge_server


    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        """
        Slash command errors
        """
        message = ctx.message
        if not message: message = InteractionUtils.create_proxy_msg(ctx.interaction,ctx=ctx)
        server_prefix = '/'
        try:
            channel_bot = self.table_bots[ctx.guild_id][ctx.channel_id]
        except KeyError:
            channel_bot = None

        if isinstance(error,discord.ApplicationCommandInvokeError):
            error = error.original
        await self.handle_exception(error,message,server_prefix, channel_bot)
    
    async def on_message(self, message: discord.Message):
        """
        On_message bot event overridden
        """
        if message.author == self.user:
            return
        if message.guild is None:
            return
        if not finished_on_ready:
            return
        if common.is_beta and not InteractionUtils.check_beta_server(message):
            return
        server_prefix = '?'
        this_bot = None

        try:
            #server_id = message.guild.id   
            is_lounge_server = InteractionUtils.simulating_lounge_server(message)
            server_prefix = ServerFunctions.get_server_prefix(message.guild.id)
            message_has_prefix, is_mention, _ = self.has_prefix(message.content, server_prefix)
            if is_mention:
                message.mentions.pop(0)

            #Message doesn't start with the server's prefix and isn't ?help
            if self.should_send_help(message):
                log_command_sent(message)
                # await AbuseTracking.blacklisted_user_check(message)
                # if await AbuseTracking.abuse_track_check(message): 
                #     return
                await help_documentation.send_help(message, [], server_prefix, is_lounge_server)
                return
                
            if not message_has_prefix:
                return
            
            command = self.strip_prefix(message.content, server_prefix)
            
            if command_is_spam(command):
                return       
        
            args = command.split()
            main_command = args[0].lower()
            
            if message.channel.category_id in TEMPORARY_VR_CATEGORIES and main_command not in ALLOWED_COMMANDS_IN_LOUNGE_ECHELONS:
                return
                
            log_command_sent(message)

            # await AbuseTracking.blacklisted_user_check(message)
            # if await AbuseTracking.abuse_track_check(message): 
            #     return
                                
            this_bot:TableBot.ChannelBot = self.check_create_channel_bot(message)
            if is_lounge_server and this_bot.isFinishedLounge():
                this_bot.freeLock()
            
            if not commandIsAllowed(is_lounge_server, message.author, this_bot, main_command):
                await send_lounge_locked_message(message, this_bot)
            else:
                await self.process_message_commands(message, args, this_bot, server_prefix, is_lounge_server)
        except Exception as e:
            await self.handle_exception(e,message,server_prefix, this_bot)

    async def handle_exception(self, error: Exception, message: discord.Message, server_prefix: str, this_bot: TableBot.ChannelBot):
        try:
            raise error
        except (discord.errors.Forbidden,ext_commands.BotMissingPermissions):
            self.lounge_submissions.clear_user_cooldown(message.author)
            await common.safe_send(message,
                                   "MKW Table Bot is missing permissions and cannot do this command. Contact your admins. The bot needs the following permissions:\n- Send Messages\n- Read Message History\n- Manage Messages (Lounge only)\n- Add Reactions\n- Manage Reactions\n- Embed Links\n- Attach files\n\nIf the bot has all of these permissions, make sure you're not overriding them with a role's permissions. If you can't figure out your role permissions, granting the bot Administrator role should work.")
        except TableBotExceptions.BlacklistedUser:
            log_command_sent(message)
        except TableBotExceptions.WarnedUser:
            log_command_sent(message)
        except TableBotExceptions.TableNotLoaded as not_loaded:
            await common.safe_send(message,f"{not_loaded}")
        except TableBotExceptions.NotBadWolf as not_bad_wolf_exception:
            await common.safe_send(message,f"You are not Bad Wolf: {not_bad_wolf_exception}")
        except TableBotExceptions.NotLoungeStaff:
            await common.safe_send(message,f"Not a valid command. For more help, do the command: {server_prefix}help")
        except TableBotExceptions.NotBotAdmin as not_bot_admin_exception:
            await common.safe_send(message,f"You are not a bot admin: {not_bot_admin_exception}")
        except TableBotExceptions.NotServerAdministrator as not_admin_failure:
            await common.safe_send(message,f"You are not a server administrator: {not_admin_failure}")
        except TableBotExceptions.NotStaff as not_staff_exception:
            await common.safe_send(message,f"You are not staff in this server: {not_staff_exception}")
        except TableBotExceptions.WrongServer as wrong_server_exception:
            if common.is_beta:
                await common.safe_send(message,
                                       f"{wrong_server_exception}: **I am not <@735782213118853180>. Use <@735782213118853180> in <#389521626645004302> to submit your table.**")
            else:
                await message.channel.send(f"Not a valid command. For more help, do the command: `{server_prefix}help`")
        except TableBotExceptions.WrongUpdaterChannel as wrong_updater_channel_exception:
            await common.safe_send(message,
                                   f"Use this command in the appropriate updater channel: {wrong_updater_channel_exception}")
        except TableBotExceptions.WarSetupStillRunning:
            await common.safe_send(message,
                                   f"I'm still trying to set up your table. Please wait until I respond with a confirmation. If you think it has been too long since I've responded, you can try ?reset and start your table again.")
        except URLShortener.URLShortenFailure:
            await common.safe_send(message, f"TinyURL failed to shorten a link. Retrying the command probably won't work.")
            common.log_traceback(traceback, this_bot, message)
        except discord.errors.DiscordServerError:
            await common.safe_send(message,
                                   "Discord's servers are either down or struggling, so I cannot send table pictures right now. Wait a few minutes for the issue to resolve.")
        except discord.errors.NotFound:
            pass
        except aiohttp.ClientOSError:
            await common.safe_send(message,
                                   "Either Wiimmfi, Lounge, or Discord's servers had an error. This is usually temporary, so do your command again.")
            raise
        except asyncio.exceptions.TimeoutError:
            await common.safe_send(message,
                                   "A HTTP request timed out. Please wait a few seconds until trying again.")
        except TableBotExceptions.WiimmfiSiteFailure:
            logging_info = log_command_sent(message,extra_text="Error info: MKWX inaccessible, other error.")
            await common.safe_send(message,
                                   "Cannot access Wiimmfi's mkwx. I'm either blocked by Cloudflare, or the website is down.")
            await self.send_to_503_channel(logging_info)
        except TableBotExceptions.CommandDisabled:
            await common.safe_send(message,"This command has been disabled.")
        except (ext_commands.CommandNotFound,TableBotExceptions.CommandNotFound):
            await common.safe_send(message,f"Not a valid command. For more help, do the command: `{server_prefix}help`")
        except TableBotExceptions.BackupPictureGeneratorFailed as e:
            await common.safe_send(message, "Local table picture generator failed. This shouldn't have happened, so report it as a bug in MKW Table Bot server.")
            raise e
        except Exception as e:
            common.log_traceback(traceback, this_bot, message)
            self.lounge_submissions.clear_user_cooldown(message.author)
            await common.safe_send(message,
                                   f"Internal bot error. An unknown problem occurred. Please wait 1 minute before sending another command. If this issue continues, try: `{server_prefix}reset`")
            raise e
        else:
            pass
    
    async def process_message_commands(self, message, args, this_bot, server_prefix, is_lounge_server, from_slash=False):
        main_command = args[0].lower()
        if not from_slash:
            Stats.log_command(main_command, message.author.id, slash=from_slash)

        #Core commands
        if main_command in RESET_TERMS:
            await commands.TablingCommands.reset_command(message, self.table_bots)   

        elif main_command in START_WAR_TERMS:
            await commands.TablingCommands.start_war_command(message, this_bot, args, server_prefix, is_lounge_server, common.author_is_table_bot_support_plus)       

        elif this_bot.manualWarSetUp:
            await commands.TablingCommands.manual_war_setup(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif this_bot.prev_command_sw:
            await commands.TablingCommands.after_start_war_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in GARBAGE_COLLECT_TERMS:
            await commands.BotOwnerCommands.garbage_collect_command(message)
        
        elif main_command in TABLE_TEXT_TERMS:
            await commands.TablingCommands.table_text_command(message, this_bot, args, server_prefix, is_lounge_server)

        elif main_command in PREDICT_TERMS:
            await commands.TablingCommands.predict_command(message, this_bot, args, server_prefix, self.lounge_submissions)

        elif main_command in WAR_PICTURE_TERMS:
            await commands.TablingCommands.war_picture_command(message, this_bot, args, server_prefix, is_lounge_server)
            
                
        #Lounge reporting updates
        elif main_command in TOTAL_CLEAR_TERMS:
            await commands.BotOwnerCommands.total_clear_command(message, self.lounge_submissions)
                
        elif main_command in LOUNGE_RT_MOGI_UPDATE_TERMS:
            await commands.LoungeCommands.rt_mogi_update(self, message, this_bot, args, self.lounge_submissions)
        
        elif main_command in LOUNGE_CT_MOGI_UPDATE_TERMS:
            await commands.LoungeCommands.ct_mogi_update(self, message, this_bot, args, self.lounge_submissions)
            
        elif main_command in LOUNGE_TABLE_SUBMISSION_APPROVAL_TERMS:
            await commands.LoungeCommands.approve_submission_command(self, message, args, self.lounge_submissions)
            
        elif main_command in LOUNGE_TABLE_SUBMISSION_DENY_TERMS:
            await commands.LoungeCommands.deny_submission_command(self, message, args, self.lounge_submissions)
            
        elif main_command in LOUNGE_PENDING_TABLE_SUBMISSION_TERMS:
            await commands.LoungeCommands.pending_submissions_command(message, self.lounge_submissions)
            
        #Fun commands
        elif main_command in STATS_TERMS:
            await commands.OtherCommands.stats_command(message, self)
        
        elif (main_command in ["badwolf"]) or (len(args) > 1 and (main_command in ["bad"] and args[1] in ["wolf"])):
            await message.channel.send(file=discord.File(common.BADWOLF_PICTURE_FILE))    
        
        elif main_command in INVITE_TERMS:
            await message.channel.send(f"{bot_invite_picture}\n\n**Are you on mobile and you don't see this button? Update your Discord app and it should appear!**")              
         
        elif main_command in RACE_RESULTS_TERMS:
            await commands.TablingCommands.race_results_command(message, this_bot, args, server_prefix, is_lounge_server)
                        
        elif main_command in REMOVE_RACE_TERMS:
            await commands.TablingCommands.remove_race_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in SUBSTITUTE_TERMS:
            await commands.TablingCommands.substitute_player_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in GET_SUBSTITUTIONS_TERMS:
            await commands.TablingCommands.get_subs_command(message, this_bot, server_prefix, is_lounge_server)
        
        elif main_command in TRANSFER_TABLE_TERMS:
            await commands.TablingCommands.transfer_table_command(message, this_bot, args, server_prefix, is_lounge_server, self.table_bots, self)
                
        elif main_command in SET_CTGP_REGION_TERMS:
            await commands.BotAdminCommands.change_ctgp_region_command(message, args)
        
        elif main_command in VR_ON_TERMS:
            await commands.BotAdminCommands.global_vr_command(message, on=True)
                
        elif main_command in VR_OFF_TERMS:
            await commands.BotAdminCommands.global_vr_command(message, on=False)
        
        elif main_command in API_TERMS:
            await commands.TablingCommands.get_api_command(message, this_bot, server_prefix, is_lounge_server)
                
        elif main_command in QUICK_START_TERMS:
            await help_documentation.send_quickstart(message)
            
        elif main_command in TUTORIAL_TERMS:
            await message.channel.send("https://www.youtube.com/watch?v=fCQnfo06_RI")                      
        
        elif main_command in HELP_TERMS:
            await help_documentation.send_help(message, args, server_prefix, is_lounge_server)
        
        #Utility commands
        elif main_command in EARLY_DC_TERMS:
            await commands.TablingCommands.early_dc_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in CHANGE_ROOM_SIZE_TERMS:
            await commands.TablingCommands.change_room_size_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in RACE_EDIT_TERMS:
            await commands.TablingCommands.race_edit_command(message, this_bot, args, is_lounge_server)
        
        elif main_command in RACE_ORDER_TERMS:
            await commands.TablingCommands.change_race_order_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in QUICK_EDIT_TERMS:
            # if main_command in DEPRECATED_QUICK_EDIT_TERMS:
            #     await message.channel.send(f"**NOTE: The command `{server_prefix}{main_command}` will be renamed soon. Only `{server_prefix}changeposition` and `{server_prefix}changeplace` will work in the future.**")
            await commands.TablingCommands.quick_edit_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in CHANGE_PLAYER_TAG_TERMS:
            await commands.TablingCommands.change_player_tag_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in CHANGE_PLAYER_NAME_TERMS:
            await commands.TablingCommands.change_player_name_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in EDIT_PLAYER_SCORE_TERMS:
            await commands.TablingCommands.change_player_score_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in EDIT_FULL_GP_TERMS:
            await commands.TablingCommands.change_all_player_score_command(message, this_bot, args, server_prefix, is_lounge_server)

        elif main_command in PLAYER_PENALTY_TERMS:
            # if False:
            #     await message.channel.send(f"Use the `{server_prefix}addpoints` command instead.")
            await commands.TablingCommands.player_penalty_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in TEAM_PENALTY_TERMS:
            await commands.TablingCommands.team_penalty_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in FCS_TERMS:
            await commands.TablingCommands.fcs_command(message, this_bot, args, server_prefix, is_lounge_server)
            
        elif main_command in GET_FLAG_TERMS:
            await commands.OtherCommands.get_flag_command(message, args, server_prefix)
                
        elif main_command in LOUNGE_NAME_TERMS:
            await commands.OtherCommands.lounge_name_command(message, args)
            
        elif main_command in SET_FLAG_TERMS:
            await commands.OtherCommands.set_flag_command(message, args)
            
        elif main_command in RXX_TERMS:
            await commands.TablingCommands.rxx_command(message, this_bot, server_prefix, is_lounge_server)
                
        elif main_command in TABLE_ID_TERMS:
            await commands.TablingCommands.table_id_command(message, this_bot, server_prefix, is_lounge_server)

        elif main_command in SERVER_USAGE_TERMS:
            await commands.BotOwnerCommands.server_process_memory_command(message)
            
        elif main_command in LOUNGE_WHO_IS_TERMS:
            await commands.LoungeCommands.who_is_command(message, args)
        elif main_command in LOOKUP_TERMS:
            await commands.LoungeCommands.lookup_command(message, args)
        elif main_command in TABLE_BOT_MEMORY_USAGE_TERMS:
            commands.BotOwnerCommands.is_bot_owner_check(message.author, "cannot display table bot internal memory usage")
            load_mes = await message.channel.send("Calculating memory usage...")
            size_str = ""

            print(f"get_size: Lounge table reports size (KiB):")
            size_str += "Lounge submission tracking size (KiB): " + str(get_size(lounge_submissions)//1024)
            print(f"get_size: FC_DiscordID:")
            size_str += "\nFC_DiscordID (KiB): " + str(get_size(UserDataProcessing.fc_discordId) // 1024)
            print(f"get_size: discordID_Lounges:")
            size_str += "\ndiscordID_Lounges (KiB): " + str(get_size(UserDataProcessing.discordId_lounges) // 1024)
            print(f"get_size: discordID_Flags (KiB):")
            size_str += "\ndiscordID_Flags (KiB): " + str(get_size(UserDataProcessing.discordId_flags) // 1024)
            print(f"get_size: blacklisted_Users (KiB):")
            size_str += "\nblacklisted_Users (KiB): " + str(get_size(UserDataProcessing.blacklisted_users) // 1024)
            print(f"get_size: valid_flag_codes (KiB):")
            size_str += "\nvalid_flag_codes (KiB): " + str(get_size(UserDataProcessing.valid_flag_codes)//1024)
            print(f"get_size: bot_abuse_tracking (KiB):")
            size_str += "\nbot_abuse_tracking (KiB): " + str(get_size(AbuseTracking.bot_abuse_tracking)//1024)
            print(f"get_size: table_bots (KiB):")
            size_str += "\ntable_bots (KiB): " + str(get_size(self.table_bots)//1024)
            print(f"get_size: PROCESS SIZE (KiB) (virt):")
            size_str += "\nPROCESS SIZE (KiB) (virt): " + str((psutil.Process(os.getpid()).memory_info().vms)//1024)
            print(f"get_size: PROCESS SIZE (KiB) (actual): ")
            size_str += "\nPROCESS SIZE (KiB) (actual): " + str((psutil.Process(os.getpid()).memory_info().rss)//1024)
            print(f"get_size: Done.")
            await load_mes.delete()
            await message.channel.send(size_str)
    
        elif main_command in SET_PREFIX_TERMS:
            await commands.ServerDefaultCommands.change_server_prefix_command(message, args)
            
        elif main_command in ALL_PLAYERS_TERMS:
            await commands.TablingCommands.all_players_command(message, this_bot, server_prefix, is_lounge_server)
        
        elif main_command in FC_TERMS:
            await commands.OtherCommands.fc_command(message, args)

        elif main_command in PAGE_TERMS:
            await commands.OtherCommands.player_page_command(message, args)
        
        elif main_command in MII_TERMS:
            await commands.OtherCommands.mii_command(message, args)
        
        elif main_command in PREVIOUS_MII_TERMS:
            await commands.OtherCommands.previous_mii_command(message, args)
        
        elif main_command in SET_TABLE_NAME_TERMS:
            await commands.TablingCommands.set_table_name_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in GET_LOGS_TERMS:
            await commands.BotOwnerCommands.get_logs_command(message)
        
        elif main_command in ADD_SHA_TERMS:
            await commands.BotAdminCommands.add_sha_track(message, args)
            
        elif main_command in REMOVE_SHA_TERMS:
            await commands.BotAdminCommands.remove_sha_track(message, args)
        
        elif main_command in RELOAD_PROPERTIES_TERMS:
            await commands.BotOwnerCommands.reload_properties(message)
            
        elif main_command in SET_API_URL_TERMS:
            await commands.BotOwnerCommands.set_api_url(message, args)
        
        elif main_command in {'close', 'stopbot', 'disconnect', 'kill'} and common.is_bot_owner(message.author):
            try:
                await self.save_data()
                self.destroy_all_tablebots()
                await message.channel.send("Data has been saved and all table bots have been cleaned up; bot gracefully closed.")
            except Exception as e:
                await message.channel.send("An error occurred while saving data; data not successfully saved.")
                raise e
            
            await self.close()
            # sys.exit()
            
        elif main_command in RACES_TERMS:
            await commands.TablingCommands.display_races_played_command(message, this_bot, server_prefix, is_lounge_server)
        
        elif main_command in PLAYER_DISCONNECT_TERMS:
            await commands.TablingCommands.disconnections_command(message, this_bot, args, server_prefix, is_lounge_server)
            
        #Admin commands     
        elif main_command in DUMP_DATA_TERMS:
            await commands.BotOwnerCommands.dump_data_command(message, self.pickle_tablebots)
        
        elif main_command in BLACKLIST_USER_TERMS:
            await commands.BotAdminCommands.blacklist_user_command(message, args)
                
        elif main_command in UNDO_TERMS:
            await commands.TablingCommands.undo_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in REDO_TERMS:
            await commands.TablingCommands.redo_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in LIST_UNDOS_TERMS:
            await commands.TablingCommands.get_undos_command(message, this_bot, server_prefix, is_lounge_server)
        
        elif main_command in LIST_REDOS_TERMS:
            await commands.TablingCommands.get_redos_command(message, this_bot, server_prefix, is_lounge_server)
        
        elif main_command in VERIFY_ROOM_TERMS:
            if commands.vr_is_on:
                await commands.OtherCommands.vr_command(message, this_bot, args)
        
        elif main_command in WORLDWIDE_TERMS:
            await commands.OtherCommands.wws_command(message, this_bot, ww_type=Race.RT_WW_REGION)
        
        elif main_command in CTWW_TERMS:
            await commands.OtherCommands.wws_command(message, this_bot, ww_type=Race.CTGP_CTWW_REGION)  
        
        elif main_command in BATTLES_TERMS:
            await commands.OtherCommands.wws_command(message, this_bot, ww_type=Race.BATTLE_REGION)
        
        elif main_command in MERGE_ROOM_TERMS:
            await commands.TablingCommands.merge_room_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in ADD_BOT_ADMIN_TERMS:
            await commands.BotOwnerCommands.add_bot_admin_command(message, args)
                
        elif main_command in REMOVE_BOT_ADMIN_TERMS:
            await commands.BotOwnerCommands.remove_bot_admin_command(message, args)

        elif main_command in BLACKLIST_WORD_TERMS:
            await commands.BotAdminCommands.add_blacklisted_word_command(message, args)
        
        elif main_command in REMOVE_BLACKLISTED_WORD_TERMS:
            await commands.BotAdminCommands.remove_blacklisted_word_command(message, args)
                    
        elif main_command in TABLE_THEME_TERMS:
            await commands.TablingCommands.table_theme_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in SERVER_DEFAULT_TABLE_THEME_TERMS:
            await commands.ServerDefaultCommands.theme_setting_command(message, this_bot, args, server_prefix)
        
        elif main_command in GRAPH_TERMS:
            await commands.TablingCommands.table_graph_command(message, this_bot, args, server_prefix, is_lounge_server)
        
        elif main_command in SERVER_DEFAULT_GRAPH_TERMS:
            await commands.ServerDefaultCommands.graph_setting_command(message, this_bot, args, server_prefix)
        
        elif main_command in SERVER_DEFAULT_MII_TERMS:
            await commands.ServerDefaultCommands.mii_setting_command(message, this_bot, args, server_prefix)
    
        elif main_command in SERVER_DEFAULT_LARGE_TIME_TERMS:
            await commands.ServerDefaultCommands.large_time_setting_command(message, this_bot, args, server_prefix)
        
        elif main_command in SERVER_SETTINGS_TERMS:
            await commands.ServerDefaultCommands.show_settings_command(message)

        elif main_command in DISPLAY_GP_SIZE_TERMS:
            await commands.TablingCommands.gp_display_size_command(message, this_bot, args, server_prefix, is_lounge_server)
            
        elif main_command in POPULAR_TRACKS_TERMS:
            await commands.StatisticCommands.popular_tracks_command(message, args, server_prefix, is_top_tracks=True)
        
        elif main_command in UNPOPULAR_TRACKS_TERMS:
            await commands.StatisticCommands.popular_tracks_command(message, args, server_prefix, is_top_tracks=False)

        elif main_command in BEST_TRACK_TERMS:
            await commands.StatisticCommands.player_tracks_command(message, args, server_prefix, sort_asc=False)

        elif main_command in WORST_TRACK_TERMS:
            await commands.StatisticCommands.player_tracks_command(message, args, server_prefix, sort_asc=True)

        elif main_command in TOP_PLAYERS_TERMS:
            await commands.StatisticCommands.top_players_command(message, args, server_prefix)
        
        elif main_command in RECORD_TERMS:
            await commands.StatisticCommands.record_command(message, args, server_prefix)

        else:
            raise TableBotExceptions.CommandNotFound
                
    
    def run(self, key):
        super().run(key, reconnect=True)
    
    async def close(self):
        await self.on_exit()
        #await super().close()
        os._exit(0)
    
    async def on_exit(self):
        await self.save_data()
        self.destroy_all_tablebots()
        await DataTracker.on_exit()
        print(f"{str(datetime.now())}: All table bots cleaned up.")

def commandIsAllowed(isLoungeServer: bool, message_author: discord.Member, this_bot: TableBot.ChannelBot, command: str, is_interaction: bool = False):
    if not isLoungeServer:
        return True

    if common.author_is_table_bot_support_plus(message_author):
        return True

    if is_interaction and this_bot and this_bot.is_table_loaded() and command in needPermissionCommands:
        return this_bot.getRoom().canModifyTable(message_author.id)

    if this_bot is not None and this_bot.getWar() is not None and (this_bot.prev_command_sw or this_bot.manualWarSetUp):
        return this_bot.getRoom().canModifyTable(message_author.id) #Fixed! Check ALL people who can modify table, not just the person who started it!

    if command not in needPermissionCommands:
        return True

    if this_bot is None or not this_bot.is_table_loaded() or this_bot.getRoom().is_freed:
        return True

    #At this point, we know the command's server is Lounge, it's not staff, and a room has been loaded
    return this_bot.getRoom().canModifyTable(message_author.id)


def command_is_spam(command:str):
    for c in command:
        if c in common.COMMAND_TRIGGER_CHARS:
            return False
    return True

def is_vr_command(message:discord.Message):
    str_msg = message.content.strip()
    if str_msg[0] not in {"!"}:
        return False
    str_msg = str_msg.lstrip("!").strip()
    return str_msg.lower() in VERIFY_ROOM_TERMS


async def send_lounge_locked_message(message, this_bot):
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

def log_command_sent(message:discord.Message, extra_text=""):
    common.log_text(f"Server: {message.guild} - Channel: {message.channel} - User: {message.author} - Command: {message.content} {extra_text}")
    return common.full_command_log(message, extra_text)


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
    Path(common.MIIS_CACHE_PATH).mkdir(parents=True, exist_ok=True)

#Bring in the bot key and LoungeAPI key
def private_data_init():
    global real_bot_key
    global beta_bot_key
    global testing_bot_key
    
    def read_next_token(file_handle, seperation_key = ":") -> str:
        return file_handle.readline().strip("\n").split(seperation_key)[1].strip()
    
    with open(common.PRIVATE_INFO_FILE, "r", encoding="utf-8") as f:
        real_bot_key = read_next_token(f)
        beta_bot_key = read_next_token(f)
        testing_bot_key = read_next_token(f)
        URLShortener.BITLY_API_TOKEN = read_next_token(f)
        URLShortener.TINYURL_API_TOKEN = read_next_token(f)
        # URLShortener.reload_module()
        LoungeAPIFunctions.code = read_next_token(f)


#Every 60 seconds, checks to see if anyone was "spamming" the bot and notifies a private channel in my server
#Of the person(s) who were warned
#Also clears the abuse tracking every 60 seconds
# @tasks.loop(minutes=1)
# async def checkBotAbuse():
#     await AbuseTracking.check_bot_abuse()
        
 
def load_CTGP_region_pickle():
    if os.path.exists(common.CTGP_REGION_FILE):
        with open(common.CTGP_REGION_FILE, "rb") as pickle_in:
            try:
                Race.CTGP_CTWW_REGION = p.load(pickle_in)
            except:
                print(f"Could not read in the CTGP_REGION for ?ctww command. Current region is: {Race.CTGP_CTWW_REGION}") 

    
def pickle_CTGP_region():
    with open(common.CTGP_REGION_FILE, "wb+") as pickle_out:
        try:
            p.dump(Race.CTGP_CTWW_REGION, pickle_out)
            return
        except:
            print("Could not dump pickle for CTGP region for ?ctww. Exception occurred.")
            
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


# nodemon BadWolfBot.py --signal SIGQUIT
bot: BadWolfBot = None
is_quitting = False
def handler(signum, frame):
    global is_quitting
    if not is_quitting:
        print(f"Received {'SIGINT' if common.ON_WINDOWS else 'SIGQUIT'}\n")
        is_quitting = True
        
        asyncio.create_task(bot.close())
end_signal = signal.SIGINT
if not common.ON_WINDOWS:
    end_signal = signal.SIGQUIT
signal.signal(end_signal, handler)

def data_init():
    create_folders()
    private_data_init()
    Race.initialize()
    UserDataProcessing.initialize()
    ServerFunctions.initialize()
    UtilityFunctions.initialize()
    TagAIShell.initialize()
    Stats.initialize()

async def initialize():
    global bot
    endpoints.initialize(app)
    data_init()
    await DataTracker.initialize()

    bot = BadWolfBot()
    await start_bot()
    await api_init()

    common.client = bot
    common.main = sys.modules[__name__]

async def api_init():
    api_channelbot_interface.initialize(bot.get_table_bots)
    
async def start_bot():
    if common.is_dev:
        key = testing_bot_key
    elif common.is_beta:
        key = beta_bot_key
    else:
        key = real_bot_key
    asyncio.create_task(bot.start(key))

async def close_wrapper():
    return await bot.close()

if __name__ == "__main__":
    PORT = common.properties["api_port"]
    app = FastAPI(on_startup=[initialize], on_shutdown=[close_wrapper])
    uvicorn.run(app, log_config=f"log.ini", port=PORT)



    
