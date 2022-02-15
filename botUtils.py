import common
import TableBot
import discord

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
TEAM_PENALTY_TERMS = {"teampen", "teampenalty"}
EDIT_PLAYER_SCORE_TERMS = {"edit"}
PLAYER_DISCONNECT_TERMS = {"dc", "dcs"}
MERGE_ROOM_TERMS = {"mr", "mergeroom"}
SET_WAR_NAME_TERMS = {"setwarname"}
CHANGE_PLAYER_NAME_TERMS = {'changename', 'cn'}
CHANGE_PLAYER_TAG_TERMS = {'assignteam', 'changeteam', 'assigntag', 'changetag', 'setteam', 'settag', 'ct'}
CHANGE_ROOM_SIZE_TERMS = {'changeroomsize', "editroomsize", "forceroomsize", "crs"}
EARLY_DC_TERMS = {'earlydc'}
DEPRECATED_QUICK_EDIT_TERMS = {'quickedit', 'qe'}
QUICK_EDIT_TERMS = DEPRECATED_QUICK_EDIT_TERMS | {"changeplace", "changeposition", "cp"}

TABLE_THEME_TERMS = {'style', 'theme', 'tablestyle', 'tabletheme'}
GRAPH_TERMS = {'graph', 'tablegraph', 'graphtheme'}
DISPLAY_GP_SIZE_TERMS = {'size', 'tablesize', 'displaysize'}


#Commands that require a war to be started, but don't modify the war/room/table in any way
TABLE_TEXT_TERMS = {"tt", "tabletext"}
WAR_PICTURE_TERMS = {"wp", "warpicture", "wo", "w;", "w["}
RACE_RESULTS_TERMS = {"rr", "raceresults"}
RACES_TERMS = {"races", "tracks", "tracklist"}
RXX_TERMS = {"rxx", "rlid", "roomid"}
ALL_PLAYERS_TERMS = {"allplayers", "ap"}
FCS_TERMS = {"fcs"}
TRANSFER_TABLE_TERMS = {"transferfrom", "copyfrom", "transfer", "copy", "copytable", "transfertable", "movetable", "move"}
GET_SUBSTITUTIONS_TERMS = {"subs", "substitutes", "substitutions", "getsubs", "allsubs"}

#Button interactions (only people in room can use buttons in Lounge; however, this isn't applied to the commands)
INTERACTIONS = {'interaction'}

#General commands that do not require a war to be started (stateless commands)
FC_TERMS = {"fc"}
LOUNGE_NAME_TERMS = {"lounge", "loungename", "ln"}
GET_FLAG_TERMS = {"getflag", "gf"}
SET_FLAG_TERMS = {"setflag", "sf"}
MII_TERMS = {"mii"}
WORLDWIDE_TERMS = {"wws", "ww", "rtww", "rtwws", "worldwide", "worldwides"}
CTWW_TERMS = {"ctgpww", "ctgpwws", "ctwws", "ctww", "ctww", "ctwws", "ctworldwide", "ctworldwides", "customtrackworldwide", "customtrackworldwides"}
BATTLES_TERMS = {"battle", "battles", "btww", "btwws", "battleww", "battlewws", "battleworldwide", "battleworldwides"}
VERIFY_ROOM_TERMS = {"vr", "verifyroom"}
STATS_TERMS = {"stats", "stat"}
INVITE_TERMS = {"invite"}
LOG_TERMS = {"log"}

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
TOTAL_CLEAR_TERMS = {'totalclear'}
DUMP_DATA_TERMS = {"dtt", "dothething"}
LOOKUP_TERMS = {"lookup"}
ADD_BOT_ADMIN_TERMS = {"addbotadmin", "addadmin"}
REMOVE_BOT_ADMIN_TERMS = {"removebotadmin", "removeadmin"}
GET_LOGS_TERMS = {"getlog", "getlogs", "logs"}
ADD_SHA_TERMS = {"addsha", "sha"}
REMOVE_SHA_TERMS = {"removesha", "delsha"}

needPermissionCommands = DISPLAY_GP_SIZE_TERMS | TABLE_THEME_TERMS | GRAPH_TERMS | RESET_TERMS | START_WAR_TERMS | UNDO_TERMS | REDO_TERMS | LIST_REDOS_TERMS | LIST_UNDOS_TERMS | REMOVE_RACE_TERMS | PLAYER_PENALTY_TERMS | TEAM_PENALTY_TERMS | EDIT_PLAYER_SCORE_TERMS | PLAYER_DISCONNECT_TERMS | MERGE_ROOM_TERMS | SET_WAR_NAME_TERMS | CHANGE_PLAYER_NAME_TERMS | CHANGE_PLAYER_TAG_TERMS | CHANGE_ROOM_SIZE_TERMS | EARLY_DC_TERMS | QUICK_EDIT_TERMS | SUBSTITUTE_TERMS | GET_SUBSTITUTIONS_TERMS | INTERACTIONS
ALLOWED_COMMANDS_IN_LOUNGE_ECHELONS = LOUNGE_MOGI_UPDATE_TERMS | STATS_TERMS | INVITE_TERMS | MII_TERMS | FC_TERMS | BATTLES_TERMS | CTWW_TERMS | WORLDWIDE_TERMS | VERIFY_ROOM_TERMS | SET_FLAG_TERMS | GET_FLAG_TERMS | POPULAR_TRACKS_TERMS | UNPOPULAR_TRACKS_TERMS | TOP_PLAYERS_TERMS | BEST_TRACK_TERMS | WORST_TRACK_TERMS | RECORD_TERMS

def createEmptyTableBot(server_id=None, channel_id=None):
    return TableBot.ChannelBot(server_id=server_id, channel_id=channel_id)

def log_command_sent(message: discord.Message, extra_text=""):
    common.log_text(f"Server: {message.guild} - Channel: {message.channel} - User: {message.author} - Command: {message.content} {extra_text}")
    return common.full_command_log(message, extra_text) 

async def send_lounge_locked_message(message: discord.Message, this_bot: TableBot.ChannelBot):
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

def commandIsAllowed(isLoungeServer: bool, message_author: discord.Member, this_bot: TableBot.ChannelBot, command: str):
    if not isLoungeServer:
        return True

    if common.author_is_table_bot_support_plus(message_author):
        return True

    if this_bot is not None and this_bot.getWar() is not None and (this_bot.prev_command_sw or this_bot.manualWarSetUp):
        return this_bot.getRoom().canModifyTable(message_author.id) #Fixed! Check ALL people who can modify table, not just the person who started it!

    if command not in needPermissionCommands:
        return True

    if this_bot is None or not this_bot.is_table_loaded() or not this_bot.getRoom().is_freed:
        return True

    #At this point, we know the command's server is Lounge, it's not staff, and a room has been loaded
    return this_bot.getRoom().canModifyTable(message_author.id)