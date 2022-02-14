'''
Created on Jun 26, 2021

@author: willg
'''

#Bot internal imports - stuff I coded
import ComponentPaginator
from Placement import Placement
import WiimmfiSiteFunctions
import Room
import ServerFunctions
import ImageCombine
import War
import TagAIShell
import LoungeAPIFunctions
import ScoreKeeper as SK
import UserDataProcessing
import TableBot
from TableBot import ChannelBot
import UtilityFunctions
import MiiPuller
import Race
import MogiUpdate
import Lounge
import TableBotExceptions
import common
import Components
from data_tracking import DataTracker
import SmartTypes
import TimerDebuggers

#Other library imports, other people codes
import math
from tabulate import tabulate
from typing import List, Set, Union
from collections.abc import Callable
import urllib
import copy
import dill as pkl
import subprocess
import gc
from builtins import staticmethod
import itertools
import discord
import os
from datetime import datetime
import URLShortener
import Stats
import re
import traceback

vr_is_on = False

async def sendRoomWarNotLoaded(message: discord.Message, serverPrefix:str, is_lounge=False):
    if is_lounge:
        return await message.channel.send(f"Room is not loaded! Use the command `{serverPrefix}sw mogiformat numberOfTeams` to load a room.")
    else:
        return await message.channel.send(f"Room is not loaded! Use the command `{serverPrefix}sw warformat numberOfTeams (LoungeName/rxx/FC) (gps=numberOfGPs) (psb=on/off) (miis=yes/no)` to start a war.")

def updateData(id_lounge, fc_id):
    UserDataProcessing.smartUpdate(id_lounge, fc_id)

async def send_missing_permissions(channel:discord.TextChannel, content=None, delete_after=7):
    try:
        return await channel.send("I'm missing permissions. Contact your admins. The bot needs these additional permissions:\n- Send Messages\n- Add Reactions (for pages)\n- Manage Messages (to remove reactions)", delete_after=delete_after)
    except discord.errors.Forbidden: #We can't send messages
        pass
#Method looks up the given name to see if any known FCs are on the table and returns the index of the player if it is found
#If the given name was a number, checks to see if the number is actually on the player list and returns the integer version of that index if it is found
#If no FCs of the given player were found on the table, or if the integer given is out of range, an error message is returned
#Returns playerNumber, errorMessage - errorMessage will be None is a playerNumber is found. playerNumber will be None if no playerNumber could be found.
def getPlayerIndexInRoom(name:str, room:TableBot.Room.Room, server_prefix:str, command_name:str):
    players = room.get_sorted_player_list()
    playerNum = None

    #If they gave us an integer, check if it's on the list
    if UtilityFunctions.isint(name):
        playerNum = int(name)
        if playerNum < 1 or playerNum > len(players):
            return None, f"The player number must be between 1 and {len(players)}. Do `{server_prefix}{command_name}` for an example on how to use this command."
        else:
            return playerNum, None

    else:
        lounge_name = str(copy.copy(name))
        loungeNameFCs = UserDataProcessing.getFCsByLoungeName(lounge_name)
        for _playerNum, (fc, _) in enumerate(players, 1):
            if fc in loungeNameFCs:
                playerNum = _playerNum
                break
        else:
            playerNum = None

        if playerNum is None:
            return None, f"Could not find Lounge name \"{UtilityFunctions.process_name(str(lounge_name))}\" in this room."
        return playerNum, None

    #Sanity check, should not ever run:
    return None, f"Error in `getPlayerIndexInRoom`. Unreachable code hit. Use `{server_prefix}log` to tell me this happened."


async def mkwx_check(message, error_message):
    if common.is_bad_wolf(message.author):
        return True

    if common.DISABLE_MKWX_COMMANDS:
        raise TableBotExceptions.CommandDisabled(error_message)
    if common.LIMIT_MKWX_COMMANDS:
        if common.LIMITED_SERVER_IDS is not None and message.guild.id in common.LIMITED_SERVER_IDS:
            return True
        if common.LIMITED_CHANNEL_IDS is not None and message.channel.id in common.LIMITED_CHANNEL_IDS:
            return True
        raise TableBotExceptions.CommandDisabled(error_message)

def is_badwolf_check(author, failure_message):
        if not common.is_bad_wolf(author):
            raise TableBotExceptions.NotBadWolf(failure_message)
        return True

def ensure_table_loaded_check(channel_bot: TableBot.ChannelBot, server_prefix: str, is_lounge_server=False, custom_message=None):
    if channel_bot.is_table_loaded():
        return True
    error_message = ""
    if custom_message is not None:
        error_message = custom_message.replace("{server_prefix}", server_prefix)
    elif is_lounge_server:
        error_message = f"Room is not loaded! Use the command `{server_prefix}sw mogiformat numberOfTeams` to load a room."
    else:
        error_message = f"Room is not loaded! Use the command `{server_prefix}sw warformat numberOfTeams (LoungeName/rxx/FC) (gps=numberOfGPs) (psb=on/off) (miis=yes/no)` to start a war."
    raise TableBotExceptions.TableNotLoaded(error_message)
    

"""============== Bad Wolf only commands ================"""
#TODO: Refactor these - target the waterfall-like if-statements
class BadWolfCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains all of the commands that are private and only available to me"""

    @staticmethod
    def is_badwolf_check(author, failure_message):
        if not common.is_bad_wolf(author):
            raise TableBotExceptions.NotBadWolf(failure_message)
        return True

    @staticmethod
    async def get_logs_command(message:discord.Message):
        BadWolfCommands.is_badwolf_check(message.author, "cannot give logs")

        if os.path.exists(common.FEEDBACK_LOGS_FILE):
            await message.channel.send(file=discord.File(common.FEEDBACK_LOGS_FILE))
        if os.path.exists(common.ERROR_LOGS_FILE):
            await message.channel.send(file=discord.File(common.ERROR_LOGS_FILE))
        if os.path.exists(common.MESSAGE_LOGGING_FILE):
            await message.channel.send(file=discord.File(common.MESSAGE_LOGGING_FILE))
        if os.path.exists(common.FULL_MESSAGE_LOGGING_FILE):
            await message.channel.send(file=discord.File(common.FULL_MESSAGE_LOGGING_FILE))


    #Adds or removes a discord ID to/from the bot admins
    @staticmethod
    async def bot_admin_change(message:discord.Message, args:List[str], adding=True):
        if len(args) <= 1:
            await message.channel.send("Give a Discord ID.")
            return

        admin_id = str(args[1].strip())

        success = UtilityFunctions.addBotAdmin(admin_id) if adding else UtilityFunctions.removeBotAdmin(admin_id)
        if success:
            add_or_remove = "Added" if adding else "Removed"
            await message.channel.send(f"{add_or_remove} discord ID {admin_id} as a bot admin.")
        else:
            await message.channel.send("Something went wrong. Try again.")


    @staticmethod
    async def add_bot_admin_command(message:discord.Message, args:List[str]):
        BadWolfCommands.is_badwolf_check(message.author, "cannot add bot admin")
        await BadWolfCommands.bot_admin_change(message, args, adding=True)

    @staticmethod
    async def remove_bot_admin_command(message:discord.Message, args:List[str]):
        BadWolfCommands.is_badwolf_check(message.author, "cannot remove bot admin")
        await BadWolfCommands.bot_admin_change(message, args, adding=False)

    @staticmethod
    async def server_process_memory_command(message:discord.Message):
        BadWolfCommands.is_badwolf_check(message.author, "cannot show server memory usage")
        command_output = subprocess.check_output('top -b -o +%MEM | head -n 22', shell=True, text=True)
        await message.channel.send(command_output)


    @staticmethod
    async def garbage_collect_command(message:discord.Message):
        BadWolfCommands.is_badwolf_check(message.author, "cannot garbage collect")
        gc.collect()
        await message.channel.send("Collected")


    @staticmethod
    async def total_clear_command(message:discord.Message, lounge_update_data):
        BadWolfCommands.is_badwolf_check(message.author, "cannot clear lounge table submission cooldown tracking")
        lounge_update_data.update_cooldowns.clear()
        await message.channel.send("Cleared.")

    @staticmethod
    async def dump_data_command(message:discord.Message, data_dump_function):
        BadWolfCommands.is_badwolf_check(message.author, "cannot dump data")
        successful = await UserDataProcessing.dump_data()
        data_dump_function()
        if successful:
            await message.channel.send("Completed.")
        else:
            await message.channel.send("Failed.")



"""================ Bot Admin Commands =================="""
#TODO: Refactor these - target the waterfall-like if-statements
class BotAdminCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains the commands that only Bot Admins can do"""

    @staticmethod
    async def add_sha_track(message:discord.Message, args:List[str], command):
        BotAdminCommands.is_sha_adder_check(message.author, "cannot add sha track")
        if len(args) < 3:
            await message.channel.send("Requires 2 args `SHA, track_name`")
            return
        if not UtilityFunctions.is_hex(args[1]):
            await message.channel.send(f"The given track is not an SHA: {args[1]}")
            return
        given_track_name = " ".join(command.split()[2:])
        if args[1] in Race.sha_track_name_mappings:
            await message.channel.send(f"The given track is already in SHA mappings with the following name: {args[1]}\nOverwriting...")
        Race.sha_track_name_mappings[args[1]] = given_track_name
        await message.channel.send(f"Added: {args[1]} -> {given_track_name}")

    @staticmethod
    async def remove_sha_track(message:discord.Message, args:List[str]):
        BotAdminCommands.is_sha_adder_check(message.author, "cannot remove sha track")
        if len(args) != 2:
            await message.channel.send("Requires 1 args `SHA`")
            return
        if not UtilityFunctions.is_hex(args[1]):
            await message.channel.send(f"The given track is not an SHA: {args[1]}")
            return
        if args[1] not in Race.sha_track_name_mappings:
            await message.channel.send(f"The given track is not in SHA mappings. Current mappings: {'  |  '.join([str(k)+' : '+str(v) for k,v in Race.sha_track_name_mappings.items()])}")
            return
        given_track_name = Race.sha_track_name_mappings[args[1]]
        del Race.sha_track_name_mappings[args[1]]
        await message.channel.send(f"Removed: {args[1]} -> {given_track_name}")

    @staticmethod
    def is_bot_admin_check(author, failure_message):
        if not common.is_bot_admin(author):
            raise TableBotExceptions.NotBotAdmin(failure_message)
        return True

    @staticmethod
    def is_sha_adder_check(author, failure_message):
        if not (common.is_bot_admin(author) or common.is_sha_adder(author)):
            raise TableBotExceptions.NotBotAdmin(failure_message)
        return True

    @staticmethod
    async def blacklisted_word_change(message:discord.Message, args:List[str], adding=True):
        if len(args) <= 1:
            to_send = "Give a word to blacklist." if adding else "Specify a word to remove from the blacklist."
            await message.channel.send(to_send)
            return
        word = str(args[1].strip())
        success = UtilityFunctions.add_blacklisted_word(word) if adding else UtilityFunctions.remove_blacklisted_word(word)
        if success:
            to_send = f"Blacklisted the word: {word}" if adding else f"Removed this word from the blacklist: {word}"
            await message.channel.send(to_send)
        else:
            await message.channel.send("Something went wrong. Try again.")

    @staticmethod
    async def remove_blacklisted_word_command(message:discord.Message, args:List[str]):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot remove blacklisted word")
        await BotAdminCommands.blacklisted_word_change(message, args, adding=False)

    @staticmethod
    async def add_blacklisted_word_command(message:discord.Message, args:List[str]):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot add blacklisted word")
        await BotAdminCommands.blacklisted_word_change(message, args, adding=True)


    @staticmethod
    async def blacklist_user_command(message:discord.Message, args:List[str], command:str):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot blacklist user")

        if len(args) < 2:
            await message.channel.send(f"Give a Discord ID to blacklist. If you do not specify a reason for blacklisting a user, the given discord ID will be **removed** from the blacklist. To blacklist a discord ID, give a reason. `?{args[0]} <discordID> (reason)`")
            return

        if len(args) == 2:
            if UserDataProcessing.add_Blacklisted_user(args[1], ""):
                await message.channel.send("Removed blacklist for " + command.split()[1])
            else:
                await message.channel.send("Blacklist failed.")
            return

        if UserDataProcessing.add_Blacklisted_user(args[1], " ".join(command.split()[2:])):
            await message.channel.send("Blacklisted " + args[1])
        else:
            await message.channel.send("Blacklist failed.")

    @staticmethod
    async def change_flag_exception(message:discord.Message, args:List[str], user_flag_exceptions:Set[int], adding=True):
        if len(args) <= 1:
            await message.channel.send("You must give a discord ID.")
            return

        if not args[1].isnumeric():
            await message.channel.send("The discord ID given is not a valid number.")
            return

        user_exception = int(args[1])
        if adding:
            user_flag_exceptions.add(int(args[1]))
        else:
            user_flag_exceptions.discard(user_exception)

        UserDataProcessing.flag_exception(user_exception, adding)

        await message.channel.send(f"{user_exception} can {'now add flags' if adding else 'no longer add flags'}.")

    @staticmethod
    async def add_flag_exception_command(message:discord.Message, args:List[str], user_flag_exceptions:Set[int]):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot give user ID a flag exception privilege")
        await BadWolfCommands.change_flag_exception(message, args, user_flag_exceptions, adding=True)

    @staticmethod
    async def remove_flag_exception_command(message:discord.Message, args:List[str], user_flag_exceptions:Set[int]):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot remove user ID's flag exception privilege")
        await BadWolfCommands.change_flag_exception(message, args, user_flag_exceptions, adding=False)

    @staticmethod
    async def change_ctgp_region_command(message:discord.Message, args:List[str]):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot change CTGP CTWW region")
        if len(args) <= 1:
            await message.channel.send("You must give a new CTGP region to use for displaying CTGP WWs.")
        else:
            Race.set_ctgp_region(args[1])
            await message.channel.send(f"CTGP WW Region set to: {args[1]}")

    @staticmethod
    async def global_vr_command(message:discord.Message, on=True):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot change vr on/off")

        global vr_is_on
        vr_is_on = on
        dump_vr_is_on()
        await message.channel.send(f"Turned !vr/?vr {'on' if on else 'off'}.")


"""================ Statistic Commands =================="""
class StatisticCommands:
    """This class houses all the commands relating to getting data for the meta and players"""

    valid_rt_options = {"rt","rts","regular","regulars","regulartrack","regulartracks"}
    valid_ct_options = {"ct","cts","custom","customs","customtrack","customtracks"}

    valid_rt_tiers = ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"]
    valid_ct_tiers = ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"]

    rt_number_tracks = 15
    ct_number_tracks = 15

    rt_min_count = 1
    ct_min_count = 2

    min_leaderboard_count_rt = 10
    min_leaderboard_count_ct = 5
    leaderboard_players_per_page = 15

    @staticmethod
    def filter_out_bad_tracks(track_data:list, is_top_tracks=True) -> list:
        if not is_top_tracks:
            return [r for r in track_data if (len(r[0]) > 0 and not UtilityFunctions.is_hex(r[0]))]
        return [r for r in track_data if r[0]]

    @staticmethod
    def validate_rts_cts_arg(arg):
        is_ct = None
        if arg.lower() in StatisticCommands.valid_rt_options:
            is_ct = False
        elif arg.lower() in StatisticCommands.valid_ct_options:
            is_ct = True

        if is_ct is None:
            return None, f"{UtilityFunctions.process_name(arg)} is not a valid option. Put in **rt** or **ct**."
        return is_ct, None

    @staticmethod
    def validate_tier_arg(arg, is_ct):
        original_arg = arg
        rt_ct_error_string = "CT" if is_ct else "RT"
        arg = arg.lower()

        tier = None
        if not is_ct and arg in StatisticCommands.valid_rt_tiers:
            tier = int(arg.strip("t"))
        elif is_ct and arg in StatisticCommands.valid_ct_tiers:
            tier = int(arg.strip("t"))

        if tier is None:
            return None, f"{UtilityFunctions.process_name(original_arg)} is not a valid {rt_ct_error_string} tier. Valid options for {rt_ct_error_string} tier are: {', '.join(StatisticCommands.valid_ct_tiers) if is_ct else ', '.join(StatisticCommands.valid_rt_tiers)}"
        return tier, None

    @staticmethod
    def validate_days_arg(arg):
        original_arg = arg
        arg = arg.lower().replace("d", "")
        days = None
        if UtilityFunctions.isint(arg):
            days = int(arg)
            if days < 1:
                None, f"{UtilityFunctions.process_name(original_arg)} was given as the number of days, but it must be 1 or more"
            else:
                return days, None
        return None, f"{UtilityFunctions.process_name(original_arg)} must be the number of days"

    @staticmethod
    def validate_tracks_args(command:str):
        args = command.split()
        if len(args) < 2:
            return None, None, None, "Please specify for **rts** or **cts**."

        is_ct, error_message = StatisticCommands.validate_rts_cts_arg(args[1])
        if is_ct is None:
            return None, None, None, error_message

        if len(args) == 2:
            return is_ct, None, None, None

        if len(args) == 3:
            tier, tier_error_message = StatisticCommands.validate_tier_arg(args[2], is_ct)
            days = None
            if tier is None:
                days, _ = StatisticCommands.validate_days_arg(args[2])

            if tier is None and days is None:
                return is_ct, None, None, f"{UtilityFunctions.process_name(args[2])} is not a tier nor is it a number of days."

            if tier is not None:
                return is_ct, tier, None, None
            if days is not None:
                return is_ct, None, days, None

        if len(args) > 3: #They specified a tier and a days filter
            tier, tier_error_message = StatisticCommands.validate_tier_arg(args[2], is_ct)
            if tier is None:
                return is_ct, None, None, tier_error_message
            days, days_error_message = StatisticCommands.validate_days_arg(args[3])
            if days is None:
                return is_ct, tier, None, days_error_message
            return is_ct, tier, days, None

        raise TableBotExceptions.UnreachableCode()

    @staticmethod
    def parse_track_type(command):
        is_ct = None
        rt_regex = f"\s({'|'.join(StatisticCommands.valid_rt_options)})(\s|$)"
        ct_regex = f"\s({'|'.join(StatisticCommands.valid_ct_options)})(\s|$)"

        if re.search(rt_regex,command):
            is_ct = False
            command = re.sub(rt_regex," ",command)

        if re.search(ct_regex,command):
            is_ct = True
            command = re.sub(ct_regex," ",command)

        return is_ct, command

    @staticmethod
    def parse_track_args(command, is_ct=False):
        min_leaderboard_count = 0
        min_regex = '(min|min_count|min_races|min_plays)=(\d+)'
        if m := re.search(min_regex,command):
            min_leaderboard_count = int(m.group(2))
            command = re.sub(min_regex,"",command)

        tier = None
        valid_tiers =  StatisticCommands.valid_ct_tiers if (is_ct) else StatisticCommands.valid_rt_tiers
        tiers_regex = f"({'|'.join(valid_tiers)})"

        if m := re.search(tiers_regex,command):
            tier = int(m.group()[1:])
            command = re.sub(tiers_regex,"",command)

        days_regex = '\s\d+d'
        days = None
        matches = re.findall(days_regex,command)
        if len(matches) > 0:
            match = matches[-1].strip()
            if 'd' in match:
                match = match[:-1]
            days = int(match)
            command = command.replace(matches[-1],"")

        rest = None
        split = command.split(" ")
        if len(split) > 1:
            rest = " ".join(split[1:])

        return tier, days, min_leaderboard_count, rest

    @staticmethod
    def format_tracks_played_result(result:list, offset, total_races_played, is_ct:bool, is_top_tracks:bool, tier:int, number_of_days:int) -> str:
        tracks_played_str = '{:>2}  {:<25} | {:<12} | {:<1}\n'.format("#", "Track Name", "Times Played", "Track Played Percentage")
        for list_num, (track_full_name, track_fixed_name, times_played) in (enumerate(result, offset)):
            proportion_played = round((times_played / total_races_played)*100, 2)
            if not is_ct and track_fixed_name.startswith("Wii "):
                track_fixed_name = track_fixed_name[4:]
            tracks_played_str += "{:>3} {:<25} | {:<12} | {:<.2f}%\n".format(str(list_num)+".", track_fixed_name, times_played, proportion_played)

        message_title = (" Most Played" if is_top_tracks else " Least Played") + (" Custom Tracks" if is_ct else " Regular Tracks")
        if tier is not None:
            message_title += f" in Tier {tier}"
        if number_of_days is not None:
            message_title += f" in the Last {number_of_days} Day{'' if number_of_days == 1 else 's'}"
        return f"**{message_title}**\n```\n{tracks_played_str}```"

    @staticmethod
    async def get_track_name(track_lookup):
        for track_name, value in Race.track_name_abbreviation_mappings.items():
            try:
                if isinstance(value, tuple):
                    abbrevs = value[0]
                    if isinstance(abbrevs, str):
                        abbrevs = [abbrevs]
                else:
                    abbrevs = [value]
                abbrevs = [x.lower() for x in abbrevs]
                if track_lookup in abbrevs:
                    return track_name, track_name.replace("(Nintendo)", "").strip(), False
            except:
                pass

        track_list = await DataTracker.DataRetriever.get_track_list()
        for (track_name, url, fixed_track_name, is_ct, track_name_lookup) in track_list:
            if not is_ct:
                if track_lookup in track_name_lookup:
                    return track_name, fixed_track_name, False

        latest_version = -1
        latest_track = [None, None, None]
        for (track_name, url, fixed_track_name, is_ct, track_name_lookup) in track_list:
            if track_lookup in track_name_lookup:
                try:
                    v = int(url.split("/i/")[1])
                except:
                    v = 0
                if v > latest_version:
                    latest_version = v
                    latest_track = [track_name, fixed_track_name, True]

        # if latest_track[0] and "(" in latest_track[0]:
        #     latest_track[1] = latest_track[0][:latest_track[0].index("(")].strip()

        return latest_track

    @staticmethod
    async def popular_tracks_command(client, message:discord.Message, args:List[str], server_prefix:str, command:str, is_top_tracks=True):
        error_message = f"""Here are 3 examples of how to use this command:
Most played CTs of all time: `{server_prefix}{args[0]} ct`
Most played RTs in the past week: `{server_prefix}{args[0]} rt 7d`
Most played RTs in tier 4 during the last 5 days: `{server_prefix}{args[0]} rt t4 5d`"""

        is_ct, tier, number_of_days, specific_error = StatisticCommands.validate_tracks_args(command)

        if specific_error is not None:
            full_error_message = f"**Error:** {specific_error}\n\n{error_message}"
            await message.channel.send(full_error_message)
            return

        tracks_played = await DataTracker.DataRetriever.get_tracks_played_count(is_ct, tier, number_of_days)
        number_tracks = StatisticCommands.ct_number_tracks if is_ct else StatisticCommands.rt_number_tracks
        total_races_played = sum(track_data[2] for track_data in tracks_played)
        num_pages = math.ceil(len(tracks_played)/number_tracks)

        if not is_top_tracks:
            tracks_played = list(reversed(tracks_played))
        tracks_played = StatisticCommands.filter_out_bad_tracks(tracks_played, is_top_tracks)

        def get_page_callback(page):
            return StatisticCommands.format_tracks_played_result(tracks_played[page*number_tracks:(page+1)*number_tracks],
                                                                 page * number_tracks + 1,
                                                                 total_races_played,
                                                                 is_ct, is_top_tracks, tier=tier,
                                                                 number_of_days=number_of_days)

        # await paginate(message, len(tracks_played)/number_tracks, get_page_callback, client)
        pages = [get_page_callback(page) for page in range(int(num_pages))]
        paginator = ComponentPaginator.MessagePaginator(pages, show_indicator=True, timeout=common.embed_page_time.seconds)
        await paginator.send(message)

    @staticmethod
    async def player_tracks_command(client: discord.Client, message: discord.Message, args: List[str], server_prefix: str, command: str, sort_asc=False):
        adjective = "worst" if sort_asc else "best"
        error_message = f"""Here are examples of how to use this command:
- Your {adjective} RTs: `{server_prefix}{args[0]} rt`
- Somebody else's {adjective} RTs: `{server_prefix}{args[0]} rt [player_name]`
- Your {adjective} RTs in the past week: `{server_prefix}{args[0]} rt 7d`
- Your {adjective} RTs in Tier 4: `{server_prefix}{args[0]} rt t4`
- Your {adjective} CTs with at least 10 plays: `{server_prefix}{args[0]} ct min=10`
"""
        def get_full_error_message(specific_error: str) -> str:
            return f"**Error:** {specific_error}\n\n{error_message}"

        is_ct, rest = StatisticCommands.parse_track_type(command.lower())
        # if is_ct is None:
        #     is_ct = False
        tier, number_of_days, min_count, rest = StatisticCommands.parse_track_args(rest, is_ct)

        if is_ct is None:
            await message.channel.send(get_full_error_message("Please specify for **rts** or **cts**."))
            return

        if not rest:
            rest = SmartTypes.create_you_discord_id(message.author.id)
        smart_type = SmartTypes.SmartLookupTypes(rest, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        await smart_type.lounge_api_update()
        descriptive, pronoun = smart_type.get_clean_smart_print(message)
        fcs = smart_type.get_fcs()
        lounge_name = smart_type.get_lounge_name()

        if fcs is None:
            await message.channel.send(get_full_error_message(f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?"))
            return

        if not min_count:
            min_count = StatisticCommands.ct_min_count if is_ct else StatisticCommands.rt_min_count
        best_tracks = await DataTracker.DataRetriever.get_best_tracks(fcs, is_ct, tier, number_of_days, sort_asc, min_count)

        filter_descriptor = ""
        if tier is not None:
            filter_descriptor += f" in T{tier}"
        if number_of_days is not None:
            filter_descriptor += f" in the Last {number_of_days} Day{'' if number_of_days == 1 else 's'}"

        if len(best_tracks) == 0:
            await message.channel.send(f"No data was found for {lounge_name}{filter_descriptor.lower()}.")
            return

        best_tracks = StatisticCommands.filter_out_bad_tracks([list(t) for t in best_tracks])
        for i, track in enumerate(best_tracks,1):
            if not is_ct and track[0].startswith("Wii "):
                track[0] = track[0][4:]
            track[0] = f"{str(i) + ('. ' if i < 10 else '.')} {track[0]}"

            secs = track[3]
            track[3] = f'{int(secs // 60)}:{round(secs % 60):02}'

        headers = ['+ Track Name', 'Avg Pts', 'Avg Place', 'Best Time', "# Plays"]

        tracks_per_page = StatisticCommands.ct_number_tracks if is_ct else StatisticCommands.rt_number_tracks

        num_pages = math.ceil(len(best_tracks)/tracks_per_page)

        def get_page_callback(page):
            table =  tabulate(best_tracks[page*tracks_per_page:(page+1)*tracks_per_page], headers, tablefmt="simple",floatfmt=".2f",colalign=["left"], stralign="right")

            message_title = f'{"Worst" if sort_asc else "Best"} {"CTs" if is_ct else "RTs"} for {lounge_name}'
            message_title += filter_descriptor
            message_title += f' [Min {min_count} Plays]'

            return f'```diff\n- {message_title}\n\n{table}```'


        pages = [get_page_callback(page) for page in range(int(num_pages))]

        paginator = ComponentPaginator.MessagePaginator(pages, show_indicator=True, timeout=common.embed_page_time.seconds)
        await paginator.send(message)

    @staticmethod
    async def top_players_command(client: discord.Client, message: discord.Message, args: List[str], server_prefix: str, command:str):
        error_message = f"""Here are examples of how to use this command:
- Top Maple Treeway players: `{server_prefix}topplayers treeway`
- Top BC3 players in Tier 5: `{server_prefix}topplayers bc3 t5`
- Top BC3 players with at least 20 plays: `{server_prefix}topplayers bc3 min=20`
- Top BC3 players during the last week: `{server_prefix}topplayers bc3 7d`
"""

        tier,number_of_days,min_count,track_lookup_name = StatisticCommands.parse_track_args(command.lower())

        if not track_lookup_name:
            await message.channel.send(
                f"Please specify a track name. \n\n" + error_message)
            return

        track_name, fixed_track_name, is_ct = await StatisticCommands.get_track_name(track_lookup_name.lower().replace(" ", ""))

        if not track_name:
            await message.channel.send(f"No track named `{UtilityFunctions.process_name(track_lookup_name)}` found. \n\n" + error_message)
            return

        if not min_count:
            min_count = StatisticCommands.min_leaderboard_count_ct if is_ct else StatisticCommands.min_leaderboard_count_rt

        top_players = await DataTracker.DataRetriever.get_top_players(fixed_track_name, tier, number_of_days, min_count)

        fixed_track_name = fixed_track_name.replace("Wii","").strip()

        filter_descriptor = ""
        if tier is not None:
            filter_descriptor += f" in T{tier}"
        if number_of_days is not None:
            filter_descriptor += f" in the Last {number_of_days} Day{'' if number_of_days == 1 else 's'}"

        if len(top_players) == 0:
            await message.channel.send(f"No qualifying players were found for track `{fixed_track_name}`{filter_descriptor} "
                                       f"(minimum {min_count} races played).\n\n" + error_message)
            return

        top_players = [list(t) for t in top_players]
        for i, player in enumerate(top_players, 1):
            player[0] = UserDataProcessing.get_lounge(player[0])
            player[0] = f"{str(i) + ('. ' if i < 10 else '.')} {player[0]}"

            secs = int(player[3])
            player[3] = f'{int(secs // 60)}:{int(secs % 60):02}'

        headers = ['+ Player', 'Avg Pts', 'Avg Place', 'Best Time', "# Plays"]

        players_per_page = StatisticCommands.leaderboard_players_per_page
        num_pages = math.ceil(len(top_players) / players_per_page)

        def get_page_callback(page):
            table = tabulate(top_players[page*players_per_page: (page+1)*players_per_page],
                             headers, tablefmt="simple", floatfmt=".2f", colalign=["left"], stralign="right")

            message_title = f"Top Lounge {fixed_track_name} Players"
            message_title += filter_descriptor
            message_title += f' [Min {min_count} Plays]'

            return f'```diff\n- {message_title}\n\n{table}```'

        pages = [get_page_callback(page) for page in range(int(num_pages))]
        paginator = ComponentPaginator.MessagePaginator(pages, show_indicator=True, timeout=common.embed_page_time.seconds)
        await paginator.send(message)

    @staticmethod
    async def record_command(client: discord.Client, message: discord.Message, args: List[str], server_prefix: str, command:str):
        error_message = f"Usage: `{server_prefix}record player_name (num_days)`"

        if len(args) == 1:
            await message.channel.send(error_message)
            return
        else:
            command = " ".join(args[1:])

        days = None
        matches = [x[0] for x in re.findall('((^|\s)\d+d?($|\s))',command)]
        if len(matches) > 0:
            match = matches[-1].strip()
            if 'd' in match:
                match = match[:-1]
            days = int(match)
            command = command.replace(matches[-1],"")
        opponent_name = command.strip()

        if len(opponent_name) == 0:
            await message.channel.send("Please specify a player name. " + error_message)
            return

        opponent_did = UserDataProcessing.get_DiscordID_By_LoungeName(opponent_name)
        if not opponent_did:
            await message.channel.send(f"No player found with name {UtilityFunctions.process_name(opponent_name)}.\n" + error_message)
            return

        player_did = str(message.author.id)

        if player_did == opponent_did:
            await message.channel.send(f"You can not compare your record against yourself.\n" + error_message)
            return

        result = await DataTracker.DataRetriever.get_record(player_did,opponent_did,days)
        total, wins = result[0]
        if total == 0:
            await message.channel.send(f"You have played no races against {UtilityFunctions.process_name(opponent_name)}")
            return

        losses = total-wins
        await message.channel.send(f'{wins} Wins — {losses} Losses')


"""================== Other Commands ===================="""
#TODO: Refactor these - target the waterfall-like if-statements
class OtherCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains all of the non administrative "stateless" commands"""

    @staticmethod
    async def get_flag_command(message:discord.Message, server_prefix:str):
        to_load = SmartTypes.create_you_discord_id(message.author.id)
        args = message.content.split()
        if len(args) > 1:
            to_load = " ".join(args[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        await smart_type.lounge_api_update()
        descriptive, pronoun = smart_type.get_clean_smart_print(message)

        discord_id = smart_type.get_discord_id()
        if discord_id is None:
            await message.channel.send(f"Could not find a discord ID for {descriptive}, have {pronoun} verified an FC in Lounge?")
            return

        flag = smart_type.get_country_flag()
        if flag is None:
            await message.channel.send(f"{SmartTypes.capitalize(descriptive)} does not have a flag set. To set {SmartTypes.possessive(pronoun)} flag for tables, {descriptive} should use `{server_prefix}setflag flagcode`. Flagcodes can be found at: {common.LORENZI_FLAG_PAGE_URL_NO_PREVIEW}")
            return

        image_name = f"{flag}.png"
        if flag.startswith("cl_") and flag.endswith("u"): #Remap this specific flag code to a specific picture
            image_name += 'cl_C3B1u.png'

        embed = discord.Embed(title=f"{SmartTypes.capitalize(SmartTypes.possessive(descriptive))} flag", colour = discord.Colour.dark_blue())
        file = discord.File(f"{common.FLAG_IMAGES_PATH}{image_name}", filename=image_name)
        embed.set_thumbnail(url=f"attachment://{image_name}")
        await message.channel.send(file=file, embed=embed)

    @staticmethod
    async def set_flag_command(message:discord.Message, args:List[str], user_flag_exceptions:Set[int]):
        author_id = message.author.id
        if len(args) > 1:
            #if 2nd argument is numeric, it's a discord ID
            if args[1].isnumeric(): #This is an admin attempt
                if str(author_id) in common.botAdmins:
                    if len(args) == 2 or args[2] == "none":
                        UserDataProcessing.add_flag(args[1], "")
                        await message.channel.send(str(args[1] + "'s flag was successfully removed."))
                    else:
                        UserDataProcessing.add_flag(args[1], args[2].lower())
                        await message.channel.send(str(args[1] + "'s flag was successfully added and will now be displayed on tables."))
                elif author_id in user_flag_exceptions:
                    flag = UserDataProcessing.get_flag(int(args[1]))
                    if flag is None:
                        UserDataProcessing.add_flag(args[1], args[2].lower())
                        await message.channel.send(str(args[1] + "'s flag was successfully added and will now be displayed on tables."))
                    else:
                        await message.channel.send("This person already has a flag set.")
                else:
                    await message.channel.send("You are not a bot admin, nor do you have an exception for adding flags.")

            elif len(args) >= 2:
                if args[1].lower() not in UserDataProcessing.valid_flag_codes:
                    await message.channel.send(f"This is not a valid flag code. For a list of flags and their codes, please visit: {common.LORENZI_FLAG_PAGE_URL_NO_PREVIEW}")
                    return

                if args[1].lower() == "none":
                    UserDataProcessing.add_flag(author_id, "")
                    await message.channel.send(f"Your flag was successfully removed. If you want to add a flag again in the future, pick a flag code from this website: {common.LORENZI_FLAG_PAGE_URL_NO_PREVIEW}")
                    return

                UserDataProcessing.add_flag(author_id, args[1].lower())
                await message.channel.send("Your flag was successfully added and will now be displayed on tables.")
                return

        elif len(args) == 1:
            UserDataProcessing.add_flag(author_id, "")
            await message.channel.send(f"Your flag was successfully removed. If you want to add a flag again in the future, pick a flag code from this website: {common.LORENZI_FLAG_PAGE_URL_NO_PREVIEW}")


    @staticmethod
    async def log_feedback_command(message:discord.Message, args:List[str], command:str):
        if len(args) > 1:
            to_log = f"{message.author} - {message.author.id}: {command}"
            common.log_text(to_log, common.FEEDBACK_LOGGING_TYPE)
            await message.channel.send("Logged")

    @staticmethod
    async def lounge_name_command(message:discord.Message):
        to_load = SmartTypes.create_you_discord_id(message.author.id)
        args = message.content.split()
        if len(args) > 1:
            to_load = " ".join(args[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        await smart_type.lounge_api_update()
        lounge_name = smart_type.get_lounge_name()
        fcs = smart_type.get_fcs()
        descriptive, pronoun = smart_type.get_clean_smart_print(message)
        if fcs is None:
            await message.channel.send(f"Could not a lounge name for {descriptive}, have {pronoun} verified an FC in Lounge?")
            return
        await message.channel.send(f"{SmartTypes.possessive(SmartTypes.capitalize(descriptive))} Lounge name is: **{lounge_name}**")


    @staticmethod
    async def fc_command(message:discord.Message, args:List[str], old_command:str):
        to_load = SmartTypes.create_you_discord_id(message.author.id)
        args = old_command.split()
        if len(args) > 1:
            to_load = " ".join(old_command.split()[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        await smart_type.lounge_api_update()
        fcs = smart_type.get_fcs()
        if fcs is None:
            descriptive, pronoun = smart_type.get_clean_smart_print(message)
            await message.channel.send(f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?")
            return
        await message.channel.send(fcs[0])

    @staticmethod
    async def mii_command(message:discord.Message, args:List[str], old_command:str):
        if common.MII_COMMAND_DISABLED and not common.is_bad_wolf(message.author):
            await message.channel.send("To ensure Table Bot remains stable and can access the website, miis have been disabled at this time.")
            return
        await mkwx_check(message, "Mii command disabled.")

        to_load = SmartTypes.create_you_discord_id(message.author.id)
        if len(args) > 1:
            to_load = " ".join(old_command.split()[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        await smart_type.lounge_api_update()
        fcs = smart_type.get_fcs()
        descriptive, pronoun = smart_type.get_clean_smart_print(message)
        if fcs is None:
            await message.channel.send(f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?")
            return

        FC = fcs[0]
        mii_dict = await MiiPuller.get_miis([FC], str(message.id))
        if isinstance(mii_dict, str):
            await message.channel.send(mii_dict)
            return
        if mii_dict is None or (isinstance(mii_dict, dict) and FC not in mii_dict):
            await message.channel.send("There was a problem trying to get the mii. Try again later.")
            return
        mii = mii_dict[FC]
        if isinstance(mii, str):
            await message.channel.send(str)
        if isinstance(mii, type(None)):
            await message.channel.send("There was a problem trying to get the mii. Try again later.")
        try:
            file, embed = mii.get_mii_embed()
            embed.title = f"{SmartTypes.possessive(SmartTypes.capitalize(descriptive))} mii"
            await message.channel.send(file=file, embed=embed)
        finally:
            mii.clean_up()

    @staticmethod
    async def wws_command(client, this_bot:TableBot.ChannelBot, message:discord.Message, ww_type=Race.RT_WW_REGION):
        await mkwx_check(message, "WWs command disabled.")

        rlCooldown = this_bot.getRLCooldownSeconds()
        if rlCooldown > 0:
            await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.", delete_after=5)
            return

        this_bot.updateRLCoolDown()
        parser = WiimmfiSiteFunctions.WiimmfiParser.FrontPageParser(await WiimmfiSiteFunctions.get_mkwx_soup())
        rooms = []
        if ww_type == Race.RT_WW_REGION:
            rooms = parser.get_RT_WWs()
        elif ww_type == Race.CTGP_CTWW_REGION:
            rooms = parser.get_CTGP_WWs()
        elif ww_type == Race.BATTLE_REGION:
            rooms = parser.get_battle_WWs()
        elif ww_type == Race.UNKNOWN_REGION:
            rooms = parser.get_other_rooms()
        else:
            rooms = parser.get_private_rooms()

        if len(rooms) == 0:
            await message.channel.send(f"There are no {Race.Race.getWWFullName(ww_type)} rooms playing right now.")
            return
        
        room_texts = [WiimmfiSiteFunctions.WiimmfiParser.FrontPageParser.get_embed_text_for_race(rooms, page) for page in range(len(rooms))]
        paginator = ComponentPaginator.MessagePaginator(pages=room_texts, show_indicator=True, timeout=common.embed_page_time.seconds)
        await paginator.send(message)



    @staticmethod
    async def vr_command(this_bot:TableBot.ChannelBot, message:discord.Message, args:List[str], old_command:str):
        await mkwx_check(message, "VR command disabled.")
        rlCooldown = this_bot.getRLCooldownSeconds()
        if rlCooldown > 0:
            await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.", delete_after=5)
            return

        this_bot.updateRLCoolDown()
        message2 = await message.channel.send("Verifying room...")
        status = False
        front_race = None
        to_load = SmartTypes.create_you_discord_id(message.author.id)
        if len(args) > 1:
            to_load = " ".join(old_command.split()[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        status, front_race = await this_bot.verify_room_smart(smart_type)
        if not status:
            descriptive, pronoun = smart_type.get_clean_smart_print(message)
            failure_message = f"Could not find {descriptive} in a room, {pronoun} don't seem to be playing right now."
            if status.status is status.NO_KNOWN_FCS:
                failure_message = f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?"
            await message2.edit(failure_message)
            return

        last_match_str = front_race.last_start_str
        match_num = front_race.get_mkwx_race_number()
        match_num_str = '' if match_num is None else f"Match #{match_num} "
        str_msg =  f"""```diff\n- Room {front_race.get_room_name()}: {front_race.created_when_str} - {match_num_str}{'No Race Started Yet' if last_match_str is None else f'({last_match_str})'} -\n\n"""
        # str_msg += '+{:>3} {:<13}| {:<13}| {:<1}\n'.format("#.", "Lounge Name", "Mii Name", "FC")
        header = ["#.", "Lounge Name", "Mii Name", "FC"]
        rows = []
        for placement in front_race.getPlacements():
            placement:Placement
            FC, mii_name = placement.get_fc_and_name()
            lounge_name = UserDataProcessing.lounge_get(FC)
            if lounge_name == "":
                lounge_name = "UNKNOWN"
            rows.append([f'{placement.get_player().get_position()}Ø', lounge_name, mii_name, FC])
            # str_msg += "{:>4} {:<13}| {:<13}| {:<1}\n".format(str(place)+".",lounge_name, mii_name, FC)
        
        str_msg += tabulate(tabular_data=rows, headers=header, tablefmt="simple", colalign=["left"], stralign="left")
        str_msg = str_msg.replace("Ø", ".") # Single periods don't show up since tabulate treats it like a number column and auto formats it

        if last_match_str is not None:
            #go get races from room
            second_status, _, races = await WiimmfiSiteFunctions.get_races_for_rxx(front_race.get_rxx())
            races_str = Room.Room.get_race_names_abbreviated(races, 12)
            str_msg += "\n\nFailed" if races_str is None else f"\n\nRaces (Last 12): {races_str}"
        await message2.edit(f"{str_msg}```")



class LoungeCommands:

    @staticmethod
    def has_authority_in_server_check(author, failure_message, authority_check=common.author_is_lounge_staff):
        if not authority_check(author):
            raise TableBotExceptions.NotStaff(failure_message)
        return True


    @staticmethod
    def correct_server_check(guild, failure_message, server_id=common.MKW_LOUNGE_SERVER_ID):
        if guild.id != server_id or (common.running_beta and common.beta_is_real):
            raise TableBotExceptions.WrongServer(failure_message)
        return True

    @staticmethod
    def updater_channel_check(channel, failure_message, valid_channel_ids={common.MKW_LOUNGE_RT_UPDATER_CHANNEL, common.MKW_LOUNGE_CT_UPDATER_CHANNEL}):
        if channel.id not in valid_channel_ids:
            raise TableBotExceptions.WrongUpdaterChannel(failure_message)
        return True

    @staticmethod
    async def who_is_command(client, message:discord.Message, args:List[str]):
        if not common.author_is_lounge_staff(message.author):
            raise TableBotExceptions.NotLoungeStaff("Not staff in MKW Lounge")

        to_lookup = None
        lookup_limit = common.WHO_IS_LIMIT
        if len(args) > 1 and UtilityFunctions.isint(args[1]):
            to_lookup = int(args[1])

        if len(args) > 2 and common.is_bad_wolf(message.author) and args[2].lower() == "all":
            lookup_limit = None

        if to_lookup is None:
            await message.channel.send("To find a user, give their discord ID: `?whois DiscordID`")
            return

        to_delete = await message.channel.send("Looking up user, this may take a minute. Please wait...")
        all_commands = Stats.get_all_commands(to_lookup, lookup_limit)
        await to_delete.delete()
        if len(all_commands) > 0:
            total_message = "".join(all_commands)
            await UtilityFunctions.safe_send_file(message, total_message)
        else:
            await message.channel.send(f"The user ID {to_lookup} has never used MKW Table Bot.")


    @staticmethod
    async def lookup_command(client, message:discord.Message, args:List[str]):
        if not common.is_bad_wolf(message.author):
            raise TableBotExceptions.NotLoungeStaff("Not staff in MKW Lounge")

        if len(args) <= 1:
            await message.channel.send("Give something.")
            return
        full_lookup = message.content.strip("? ")[len(args[0]):].strip()

        to_delete = await message.channel.send("Looking up, please wait...")
        all_commands = Stats.hard_check(full_lookup, None)
        await to_delete.delete()
        if len(all_commands) > 0:
            total_message = "".join(all_commands)
            await UtilityFunctions.safe_send_file(message, total_message)
        else:
            await message.channel.send(f"The lookup {full_lookup} has nothing in MKW Table Bot.")





    #TODO: Refactor this - in an rushed effort to release this, the code is sloppy.
    #It should be refactored as this is some of the worst code in TableBot
    @staticmethod
    async def __mogi_update__(client, this_bot:TableBot.ChannelBot, message:discord.Message, args:List[str], lounge_server_updates:Lounge.Lounge, is_primary=True):
        command_incorrect_format_message = "The format of this command is: `?" + args[0] + " TierNumber RacesPlayed (TableText)`\n- **TierNumber** must be a number. For RTs, between 1 and 8. For CTs, between 1 and 7. If you are trying to submit a squadqueue table, **TierNumber** should be: squadqueue\n-**RacesPlayed** must be a number, between 1 and 32."
        cooldown = lounge_server_updates.get_user_update_submit_cooldown(message.author.id)
        updater_channel_id, updater_link, preview_link, type_text = lounge_server_updates.get_information(is_primary)

        if cooldown > 0:
            await message.channel.send("You have already submitted a table very recently. Please wait " + str(cooldown) + " more seconds before submitting another table.", delete_after=10)
            return

        if len(args) < 3:
            await message.channel.send(command_incorrect_format_message)
            return


        tier_number, summary_channel_id = MogiUpdate.get_tier_and_summary_channel_id(args[1], is_primary)
        if tier_number is None:
            await message.channel.send(command_incorrect_format_message)
            return

        races_played = args[2]
        if not races_played.isnumeric() or int(args[2]) < 1 or int(args[2]) > 32:
            await message.channel.send(command_incorrect_format_message)
            return
        races_played = int(args[2])

        table_text = ""
        #Used if using Table Bot table
        using_table_bot_table = False
        table_sorted_data = None

        if len(args) == 3:
            ensure_table_loaded_check(this_bot, '?', True, custom_message=f"Room is not loaded. You must have a room loaded if you do not give TableText to this command. Otherwise, do `?{args[0]} TierNumber RacesPlayed TableText`")
            table_text, table_sorted_data = SK.get_war_table_DCS(this_bot, use_lounge_otherwise_mii=True, use_miis=False, lounge_replace=True, missingRacePts=this_bot.dc_points, server_id=message.guild.id, discord_escape=True)
            table_text = table_text + this_bot.get_lorenzi_style_and_graph(prepend_newline=True)
            using_table_bot_table = True

        else:
            temp = message.content
            command_removed = temp[temp.lower().index(args[0])+len(args[0]):].strip("\n\t ")
            tier_number_removed = command_removed[command_removed.lower().index(args[1].lower())+len(args[1]):].strip("\n\t ")
            table_text = command_removed[tier_number_removed.lower().index(args[2].lower())+len(args[2]):].strip("\n\t ")


        lounge_server_updates.update_user_cooldown(message.author)
        delete_me = await message.channel.send("Submitting table... please wait...")


        error_code, newTableText, json_data = await MogiUpdate.textInputUpdate(table_text, tier_number, races_played, is_rt=is_primary)


        if error_code != MogiUpdate.SUCCESS_EC:
            if error_code is None:
                await message.channel.send("Couldn't submit table. An unknown error occurred.")
            elif error_code == MogiUpdate.PLAYER_NOT_FOUND_EC:
                missing_players = json_data
                await message.channel.send("Couldn't submit table. The following players could not be found: **" + "**, **".join(missing_players) + "**\nCheck your submission for correct names. If your table has subs, they must be in this format: Sarah(4)/Jacob(8)")
            else:
                await message.channel.send("Couldn't submit table. Reason: *" + MogiUpdate.table_text_errors[error_code] + "*")


        else:
            url_table_text = urllib.parse.quote(newTableText)
            image_url = common.base_url_lorenzi + url_table_text
            table_image_path = str(message.id) + ".png"
            image_download_success = await common.download_image(image_url, table_image_path)
            try:
                if not image_download_success:
                    await message.channel.send("Could not get image for table.")
                else:

                    if using_table_bot_table:
                        war_had_errors = len(this_bot.getWar().get_all_war_errors_players(this_bot.getRoom(), False)) > 0
                        tableWasEdited = len(this_bot.getWar().manualEdits) > 0 or len(this_bot.getRoom().dc_on_or_before) > 0 or len(this_bot.getRoom().forcedRoomSize) > 0 or this_bot.getRoom().had_positions_changed() or len(this_bot.getRoom().get_removed_races_string()) > 0 or this_bot.getRoom().had_subs()
                        header_combine_success = ImageCombine.add_autotable_header(errors=war_had_errors, table_image_path=table_image_path, out_image_path=table_image_path, edits=tableWasEdited)
                        footer_combine_success = True

                        if header_combine_success and this_bot.getWar().displayMiis:
                            footer_combine_success = ImageCombine.add_miis_to_table(this_bot, table_sorted_data, table_image_path=table_image_path, out_image_path=table_image_path)
                        if not header_combine_success or not footer_combine_success:
                            await common.safe_delete(delete_me)
                            await message.channel.send("Internal server error when combining images. Sorry, please notify BadWolf immediately.")
                            return

                    updater_channel = client.get_channel(updater_channel_id)
                    preview_link += urllib.parse.quote(json_data)
                    updater_link += urllib.parse.quote(json_data)


                    embed = discord.Embed(
                                        title = "",
                                        description="[Click to preview this update]("+ updater_link + ")",
                                        colour = discord.Colour.dark_red()
                                    )
                    file = discord.File(table_image_path)
                    lounge_server_updates.add_counter()
                    id_to_submit = lounge_server_updates.get_counter()
                    embed.add_field(name='Submission ID', value=str(id_to_submit))
                    embed.add_field(name="Tier", value=tier_number)
                    embed.add_field(name="Races Played", value=races_played)
                    summary_channel = client.get_channel(summary_channel_id)
                    embed.add_field(name="Approving to", value=(summary_channel.mention if summary_channel is not None else "Can't find channel"))
                    embed.add_field(name='Submitted from', value=message.channel.mention)
                    embed.add_field(name='Submitted by', value=message.author.mention)
                    embed.add_field(name='Discord ID', value=str(message.author.id))

                    shortened_admin_panel_link = "No Link"
                    try:
                        admin_link_tiny_url = await URLShortener.tinyurl_shorten_url(updater_link)
                        shortened_admin_panel_link = f"[Preview]({admin_link_tiny_url})"
                    except:
                        pass

                    embed.add_field(name='Short Preview Link:', value=shortened_admin_panel_link)

                    embed.set_image(url="attachment://" + table_image_path)
                    embed.set_author(name="Updater Automation", icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")

                    sent_message = await updater_channel.send(file=file, embed=embed)
                    lounge_server_updates.add_report(id_to_submit, sent_message, summary_channel_id, json_data)

                    other_matching_submission_id = lounge_server_updates.submission_id_of_last_matching_json(id_to_submit)
                    if other_matching_submission_id is not None:
                        await updater_channel.send(f"**Warning:** This submission ({id_to_submit}) matches a previous submission, which has the id {other_matching_submission_id}. It is extremely unlikely this is by chance. Investigate before approving/denying.")


                    file = discord.File(table_image_path)
                    embed = discord.Embed(
                                        title = "Successfully submitted to " + type_text + " Reporters and " + type_text + " Updaters",
                                        description="[Click to preview this update]("+ preview_link + ")",
                                        colour = discord.Colour.dark_red()
                                    )
                    embed.add_field(name='Submission ID', value=str(id_to_submit))
                    embed.add_field(name='Races Played', value=str(races_played))


                    shortened_preview_link = "No Link"
                    try:
                        if updater_link == preview_link:
                            shortened_preview_link = shortened_admin_panel_link
                        else:
                            preview_link_tiny_url = await URLShortener.tinyurl_shorten_url(preview_link)
                            shortened_preview_link = f"[Preview]({preview_link_tiny_url})"
                    except:
                        pass

                    embed.add_field(name='Short Preview Link:', value=shortened_preview_link)

                    embed.set_image(url="attachment://" + table_image_path)
                    embed.set_author(name="Updater Automation", icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")
                    embed.set_footer(text="Note: the actual update may look different than this preview if the Updaters need to first update previous mogis. If the link is too long, just hit the enter key.")

                    await message.channel.send(file=file, embed=embed)
            finally:
                if os.path.exists(table_image_path):
                    os.remove(table_image_path)
        lounge_server_updates.update_user_cooldown(message.author)
        await common.safe_delete(delete_me)

    @staticmethod
    async def ct_mogi_update(client, this_bot:TableBot.ChannelBot, message:discord.Message, args:List[str], lounge_server_updates:Lounge.Lounge):
        LoungeCommands.correct_server_check(message.guild, "cannot submit table update for CT mogi", lounge_server_updates.server_id)
        await LoungeCommands.__mogi_update__(client, this_bot, message, args, lounge_server_updates, is_primary=False)


    @staticmethod
    async def rt_mogi_update(client, this_bot:TableBot.ChannelBot, message:discord.Message, args:List[str], lounge_server_updates:Lounge.Lounge):
        LoungeCommands.correct_server_check(message.guild, "cannot submit table update for RT mogi", lounge_server_updates.server_id)
        await LoungeCommands.__mogi_update__(client, this_bot, message, args, lounge_server_updates, is_primary=True)


    @staticmethod
    async def __submission_action_command__(client, message:discord.Message, args:List[str], lounge_server_updates:Lounge.Lounge, is_approval=True):
        if len(args) < 2:
            await message.channel.send("The way to use this command is: ?" + args[0] + " submissionID")
            return

        submissionID = args[1]
        if submissionID.isnumeric():
            submissionID = int(submissionID)
            if lounge_server_updates.has_submission_id(submissionID):
                submissionMessageID, submissionChannelID, summaryChannelID, submissionStatus, submission_json = lounge_server_updates.get_submission_id(submissionID)
                submissionMessage = None

                try:
                    submissionChannel = client.get_channel(submissionChannelID)
                    if submissionChannel is None:
                        await message.channel.send("I cannot see the submission channels (or they changed). Get boss help.")
                        return
                    submissionMessage = await submissionChannel.fetch_message(submissionMessageID)
                except discord.errors.NotFound:
                    await message.channel.send("That submission appears to have been deleted on Discord. I have now removed this submission from my records.")
                    lounge_server_updates.remove_submission_id(submissionID)
                    return

                if is_approval:
                    submissionEmbed = submissionMessage.embeds[0]
                    submissionEmbed.remove_field(6)
                    submissionEmbed.remove_field(5)
                    submissionEmbed.set_field_at(3, name="Approved by:", value=message.author.mention)
                    submissionEmbed.set_field_at(4, name="Approval link:", value="[Message](" + submissionMessage.jump_url + ")")

                    summaryChannelRetrieved = True
                    if summaryChannelID is None:
                        summaryChannelRetrieved = False
                    summaryChannelObj = client.get_channel(summaryChannelID)
                    approval_message_warning = None

                    is_pending = lounge_server_updates.submission_id_is_pending(submissionID)
                    if not is_pending:
                        is_approved = lounge_server_updates.submission_id_is_approved(submissionID)
                        submission_status = "approved" if is_approved else "denied"
                        extra_message_text = f"**I went ahead and sent it to the summaries anyway**, but you should make sure you didn't just double approve {submissionID}." if is_approved else f"**I went ahead and sent it to the summaries anyway**, but you should make sure you didn't approve the submission {submissionID} that should have remained denied."
                        approval_message_warning = f"**Warning:** The submission ({submissionID}) was already **{submission_status}**. You might have made a typo for your submission ID. {extra_message_text}"



                    if summaryChannelObj is None:
                        summaryChannelRetrieved = False
                    if not summaryChannelRetrieved:
                        await message.channel.send("I cannot see the summary channels. Contact a boss.")
                        return

                    try:
                        await summaryChannelObj.send(embed=submissionEmbed)
                        lounge_server_updates.approve_submission_id(submissionID)
                    except discord.errors.Forbidden:
                        await message.channel.send("I'm not allowed to send messages in summary channels. Contact a boss.")
                        return

                    if approval_message_warning is not None:
                        await summaryChannelObj.send(approval_message_warning)
                        await submissionMessage.channel.send(approval_message_warning)

                    await submissionMessage.clear_reaction("\u274C")
                    await submissionMessage.add_reaction("\u2705")
                    await message.add_reaction(u"\U0001F197")
                else:
                    await submissionMessage.clear_reaction("\u2705")
                    await submissionMessage.add_reaction("\u274C")
                    is_pending = lounge_server_updates.submission_id_is_pending(submissionID)
                    if not is_pending:
                        is_denied = lounge_server_updates.submission_id_is_denied(submissionID)
                        submission_status = "denied" if is_denied else "approved"
                        extra_message_text = f"Double denying a submission doesn't do anything, so you don't need to worry. You simply might have made a typo for your submission ID, and you should deny the correct one." if is_denied else f"I've given it the X reaction anyway. Don't bother 'approving' it again if it was previously approved and sent to the correct summaries (as this will resend it to the summary channels). Simply check your `?deny` command for typos so you deny the right submission."
                        await submissionMessage.channel.send(f"**Warning:** The submission ({submissionID}) was already **{submission_status}**. {extra_message_text}")
                    lounge_server_updates.deny_submission_id(submissionID)
                    await message.add_reaction(u"\U0001F197")
            else:
                await message.channel.send("I couldn't find this submission ID. Make sure you have the right submission ID.")
        else:
            await message.channel.send("The way to use this command is: ?" + args[0] + " submissionID - submissionID must be a number")


    @staticmethod
    async def approve_submission_command(client, message:discord.Message, args:List[str], lounge_server_updates:Lounge.Lounge):
        LoungeCommands.correct_server_check(message.guild, "cannot approve table submission", lounge_server_updates.server_id)
        LoungeCommands.has_authority_in_server_check(message.author, "cannot approve table submission", authority_check=lounge_server_updates.report_table_authority_check)
        LoungeCommands.updater_channel_check(message.channel, "cannot approve table submission", lounge_server_updates.get_updater_channel_ids())
        await LoungeCommands.__submission_action_command__(client, message, args, lounge_server_updates, is_approval=True)


    @staticmethod
    async def deny_submission_command(client, message:discord.Message, args:List[str], lounge_server_updates:Lounge.Lounge):
        LoungeCommands.correct_server_check(message.guild, "cannot deny table submission", lounge_server_updates.server_id)
        LoungeCommands.has_authority_in_server_check(message.author, "cannot deny table submission", authority_check=lounge_server_updates.report_table_authority_check)
        LoungeCommands.updater_channel_check(message.channel, "cannot deny table submission", lounge_server_updates.get_updater_channel_ids())
        await LoungeCommands.__submission_action_command__(client, message, args, lounge_server_updates, is_approval=False)


    @staticmethod
    async def pending_submissions_command(message:discord.Message, lounge_server_updates:Lounge.Lounge):
        LoungeCommands.correct_server_check(message.guild, "cannot display pending table submissions", lounge_server_updates.server_id)
        LoungeCommands.has_authority_in_server_check(message.author, "cannot display pending table submissions", authority_check=lounge_server_updates.report_table_authority_check)

        to_send = ""
        for submissionID in lounge_server_updates.table_reports:
            _, submissionChannelID, summaryChannelID, submissionStatus, submission_json = lounge_server_updates.get_submission_id(submissionID)
            if submissionStatus == "PENDING":
                matching_other_id = lounge_server_updates.submission_id_of_last_matching_json(submissionID)
                matching_warning_str = ""
                if matching_other_id is not None:
                    matching_warning_str = f" - **Warning:** This submission matches a previous submission, which has the id {matching_other_id}"
                to_send += MogiUpdate.getTierFromChannelID(summaryChannelID) + f" - Submission ID: {submissionID}{matching_warning_str}\n"
        if to_send == "":
            to_send = "No pending submissions."
        await message.channel.send(to_send)




"""================== Server Administrator Settings Commands ==============="""
#TODO: Refactor these - target the waterfall-like if-statements
class ServerDefaultCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains all of the commands that server administrators can use to set defaults for their server"""

    @staticmethod
    def server_admin_check(author, failure_message):
        if not author.guild_permissions.administrator:
            raise TableBotExceptions.NotServerAdministrator(failure_message)
        return True
    
    @staticmethod
    async def show_settings_command(message: discord.Message, this_bot: ChannelBot, server_prefix: str):
        server_id = message.guild.id
        server_name = message.guild.name
        await message.channel.send(ServerFunctions.get_server_settings(server_name, server_id))


    @staticmethod
    async def large_time_setting_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str):
        if not common.running_beta or common.beta_is_real:
            ServerDefaultCommands.server_admin_check(message.author, "cannot change server default for hiding large times on tables")

        server_id = message.guild.id

        if len(args) == 1:
            await send_available_large_time_options(message, args, this_bot, server_prefix, server_wide=True)
            return

        elif len(args) > 1:
            setting = args[1:]
            if len(setting) > 1:
                setting = [e.strip(',') for e in setting]
            valid = False
            if any([('never' in entry and 'always' in entry) for entry in setting]):
                valid = False
            else:
                try:
                    setting = ','.join(setting).strip().lower()
                    setting = ServerFunctions.parse_ILT_setting(setting)
                    valid = True
                except (ValueError, IndexError):
                    valid = False

            if not valid:
                return await send_available_large_time_options(message, args, this_bot, server_prefix, server_wide=True)

            was_success = ServerFunctions.change_default_large_time_setting(server_id, setting)
            if was_success:
                await message.channel.send(f"Server setting changed to:\n{get_large_time_option(setting)}")
            else:
                await message.channel.send("Error changing default large time setting for this server. This is TableBot's fault. Try to set it again.")

    @staticmethod
    async def mii_setting_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str):
        if not common.running_beta or common.beta_is_real:
            ServerDefaultCommands.server_admin_check(message.author, "cannot change miis default for this server")

        server_id = message.guild.id

        if len(args) == 1:
            await send_available_mii_options(message, args, this_bot, server_prefix, server_wide=True)
            return

        elif len(args) > 1:
            setting = args[1]
            if setting not in ServerFunctions.bool_map:
                await message.channel.send(f"That is not a valid mii setting. To see valid settings, run the command `{server_prefix}{args[0]}` and read carefully.")
                return

            was_success = ServerFunctions.change_default_server_mii_setting(server_id, setting)
            if was_success:
                await message.channel.send(f"Server setting changed to:\n{get_mii_option(setting)}")
            else:
                await message.channel.send("Error changing mii on/off default for server. This is TableBot's fault. Try to set it again.")


    @staticmethod
    async def graph_setting_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str):
        if not common.running_beta or common.beta_is_real:
            ServerDefaultCommands.server_admin_check(message.author, "cannot change default graph for this server")

        server_id = message.guild.id
        if len(args) == 1:
            await send_available_graph_list(message, args, this_bot, server_prefix, server_wide=True)
            return

        if len(args) > 1:
            setting = args[1]
            if not this_bot.is_valid_graph(setting):
                await message.channel.send(f"That is not a valid graph setting. To see valid settings, run the command `{server_prefix}{args[0]}` and read carefully.")
                return

            was_success = ServerFunctions.change_default_server_graph(server_id, setting)
            if was_success:
                await message.channel.send(f"Default graph for server set to: **{this_bot.get_graph_name(setting)}**")
            else:
                await message.channel.send("Error setting default graph for server. This is TableBot's fault. Try to set it again.")

    @staticmethod
    async def theme_setting_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str):
        if not common.running_beta or common.beta_is_real:
            ServerDefaultCommands.server_admin_check(message.author, "cannot change default table theme for this server")

        server_id = message.guild.id
        if len(args) == 1:
            await send_table_theme_list(message, args, this_bot, server_prefix, server_wide=True)
            return
        if len(args) > 1:
            setting = args[1]
            if not this_bot.is_valid_style(setting):
                await message.channel.send(f"That is not a valid table theme setting. To see valid settings, run the command `{server_prefix}{args[0]}` and read carefully.")
                return

            was_success = ServerFunctions.change_default_server_table_theme(server_id, setting)
            if was_success:
                await message.channel.send(f"Default table theme for server set to: **{this_bot.get_style_name(setting)}**")
            else:
                await message.channel.send("Error setting default table theme for server. This is TableBot's fault. Try to set it again.")


    @staticmethod
    async def change_server_prefix_command(message:discord.Message, args:List[str]):
        ServerDefaultCommands.server_admin_check(message.author, "cannot change prefix")
        server_id = message.guild.id

        if len(args) < 2:
            await message.channel.send("Give a prefix. Prefix not changed.")
            return

        new_prefix = args[1]
        if len(new_prefix) < 1:
            await message.channel.send("Cannot set an empty prefix. Prefix not changed.")
            return
        if len(new_prefix) > common.MAX_PREFIX_LENGTH:
            await message.channel.send(f"Prefixes must be {common.MAX_PREFIX_LENGTH} characters or less.")
            return

        was_success = ServerFunctions.change_server_prefix(str(server_id), new_prefix)
        if was_success:
            await message.channel.send("Prefix changed to: " + new_prefix)
        else:
            await message.channel.send("Errors setting prefix. Prefix not changed.")


"""================== Tabling Commands =================="""
#TODO: Refactor these
class TablingCommands:

    @staticmethod
    async def reset_command(message:discord.Message, table_bots):
        server_id = message.guild.id
        channel_id = message.channel.id
        if server_id in table_bots and channel_id in table_bots[server_id]:
            table_bots[server_id][channel_id].reset()
            del(table_bots[server_id][channel_id])

        await message.channel.send("Reset successful.")

    @staticmethod
    async def display_races_played_command(message:discord.Message, this_bot:ChannelBot, server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        await message.channel.send(this_bot.getRoom().get_races_string())


    @staticmethod
    async def fcs_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        await message.channel.send(this_bot.getRoom().getFCPlayerListString())


    @staticmethod
    async def rxx_command(message:discord.Message, this_bot:ChannelBot, server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        await message.channel.send(this_bot.getRoom().getRXXText())

    @staticmethod
    async def team_penalty_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if this_bot.getWar().is_ffa():
            await message.channel.send("You can't give team penalties in FFAs. Do " + server_prefix + "penalty to give an individual player a penalty in an FFA.")
            return

        if len(args) == 1:
            teams = sorted(this_bot.getWar().getTags())
            to_send = ""
            for team_num, team in enumerate(teams, 1):
                to_send += UtilityFunctions.process_name(str(team_num)) + ". " + team + "\n"
            to_send += "\n**To give the 2nd team on the list a 15 point penalty:** *" + server_prefix + "teampenalty 2 15*"
            await message.channel.send(to_send)
            return

        if len(args) != 3:
            await message.channel.send(example_help(server_prefix, args[0]))
            return

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
            await message.channel.send(f"Both the team number and the penalty amount must be numbers. {example_help(server_prefix, args[0])}")
        elif teamNum < 1 or teamNum > len(teams):
            await message.channel.send(f"The team number must be on this list (between 1 and {len(teams)}). {example_help(server_prefix, args[0])}")
        else:
            this_bot.add_save_state(message.content)
            this_bot.getWar().addTeamPenalty(teams[teamNum-1], amount)
            await message.channel.send(UtilityFunctions.process_name(teams[teamNum-1] + " given a " + str(amount) + " point penalty."))


    @staticmethod
    async def disconnections_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, dont_send=False):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) == 1:
            had_DCS, DC_List_String = this_bot.getRoom().getDCListString(this_bot.getWar().getNumberOfGPS(), True)
            if had_DCS:
                DC_List_String += "\nIf the first disconnection on this list was on results: **" + server_prefix + "dc 1 onresults**\n" +\
                "If they were not on results, do **" + server_prefix + "dc 1 before**"
            await message.channel.send(DC_List_String)
            return

        if len(args) < 3:
            await message.channel.send("You must give a dc number on the list and if they were on results or not. Run " + server_prefix + "dcs for more information.")
            return

        missing_per_race = this_bot.getRoom().getMissingOnRace(this_bot.getWar().numberOfGPs, include_blank=False)
        merged = list(itertools.chain(*missing_per_race))
        disconnection_number = args[1]
        if not disconnection_number.isnumeric():
            await message.channel.send(UtilityFunctions.process_name(str(disconnection_number)) + " is not a number on the dcs list. Do " + server_prefix + "dcs for an example on how to use this command.")
            return
        if int(disconnection_number) > len(merged):
            await message.channel.send("There have not been this many DCs. Run " + server_prefix + "dcs to learn how to use this command.")
            return
        if int(disconnection_number) < 1:
            await message.channel.send("You must give a DC number on the list. Run " + server_prefix + "dcs to learn how to use this command.")
            return

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
        player_name = UtilityFunctions.process_name(str(missing_per_race[race-1][index][1]) + UserDataProcessing.lounge_add(player_fc))
        if on_or_before in ["on", "during", "midrace", "results", "onresults"]:
            this_bot.add_save_state(message.content)
            this_bot.getRoom().edit_dc_status(player_fc, race, 'on')
            mes = "Saved: " + player_name + ' was on results for race #' + str(race)       
            if not dont_send: await message.channel.send(mes)             
            return mes
        if on_or_before in ["before", "prior", "beforerace", "notonresults", "noresults", "off"]:
            this_bot.add_save_state(message.content)
            this_bot.getRoom().edit_dc_status(player_fc, race, 'before')
            mes = "Saved: " + player_name + ' was not on results for race #' + str(race)
            if not dont_send: await message.channel.send(mes)                  
            return mes 
        
        await message.channel.send('"' + UtilityFunctions.process_name(str(on_or_before)) + '" needs to be either "on" or "before". Do ' + server_prefix + "dcs for an example on how to use this command.")


    @staticmethod
    async def player_penalty_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) == 1:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += "\n**To give the 2nd player on the list a 15 point penalty:** *" + server_prefix + "penalty 2 15*"
            await message.channel.send(to_send)
            return

        if len(args) != 3:
            await message.channel.send(example_help(server_prefix, args[0]))
            return

        playerNum = args[1]
        amount = args[2]
        players = this_bot.getRoom().get_sorted_player_list()
        playerNum, playerErrorMessage = getPlayerIndexInRoom(args[1], this_bot.getRoom(), server_prefix, "pen")

        if UtilityFunctions.isint(amount):
            amount = int(amount)

        if not isinstance(amount, int):
            return await message.channel.send(f"The penalty amount must be a number. {example_help(server_prefix, args[0])}")
        elif playerNum is None:
            return await message.channel.send(playerErrorMessage)

        this_bot.add_save_state(message.content)
        this_bot.getRoom().addPlayerPenalty(players[playerNum-1][0], amount)
        await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + UserDataProcessing.lounge_add(players[playerNum-1][0]) + " given a " + str(amount) + " point penalty."))

    @staticmethod
    async def get_subs_command(message: discord.Message, this_bot: ChannelBot, server_prefix: str, is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        
        subs_string = this_bot.getRoom().get_room_subs()

        await message.channel.send(subs_string)

    @staticmethod
    async def substitute_player_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        example_error_message = f"Do `{server_prefix}sub` for an example of how to use this command."
        #Command information for user if command is run with no args
        if len(args) == 1:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += f"\n**Example:** If the 2nd player on the list subbed in on race 9 for the 1st player on the list, you would do: `{server_prefix}{args[0]} 2 1 9`"
            await message.channel.send(to_send)
            return

        #If they don't give the right number of arguments, send an error.
        if len(args) != 4:
            await message.channel.send(example_error_message)
            return

        subInNum, subInErrorMessage = getPlayerIndexInRoom(args[1], this_bot.getRoom(), server_prefix, "sub")
        subOutNum, subOutErrorMessage = getPlayerIndexInRoom(args[2], this_bot.getRoom(), server_prefix, "sub")

        #If race number isn't a valid number, send error message
        raceNum = args[3]
        if not UtilityFunctions.isint(raceNum):
            await message.channel.send(f"The race number must be a number. {example_error_message}")
            return
        raceNum = int(raceNum)

        if raceNum < 2:
            await message.channel.send(f"The race number that the sub began to play must be race 2 or later. {example_error_message}")
            return
        if raceNum > this_bot.getWar().getNumberOfRaces():
            await message.channel.send(f"Because your table was started as a {this_bot.getWar().getNumberOfGPS()} GP table, the last possible race someone can sub in is race #{this_bot.getWar().getNumberOfRaces()}")
            return

        if subInNum is None:
            await message.channel.send(subInErrorMessage)
            return
        if subOutNum is None:
            await message.channel.send(subOutErrorMessage)
            return

        if subInNum == subOutNum:
            await message.channel.send("Someone cannot sub in for themselves.")
            return

        subOutFC, subOutMiiName = this_bot.getRoom().getPlayerAtIndex(subOutNum-1)
        subInFC, subInMiiName = this_bot.getRoom().getPlayerAtIndex(subInNum-1)
        if this_bot.getRoom().fc_subbed_in(subInFC):
            await message.channel.send(f"The person you are trying to sub in has subbed in for someone else already on the table.")
            return
        if this_bot.getRoom().fc_subbed_out(subOutFC):
            await message.channel.send(f"The person you are trying to sub out has already subbed out on the table.")
            return
        if this_bot.getRoom().fc_subbed_in(subOutFC):
            await message.channel.send(f"Currently, MKW Table Bot does not support double subs. Maybe in the future!")
            return

        subOutStartRace = 1
        subOutEndRace = raceNum - 1
        subOutScores = SK.get_race_scores_for_fc(subOutFC, this_bot)[subOutStartRace-1:subOutEndRace]
        subOutName = UserDataProcessing.lounge_get(subOutFC)
        subOutTag = this_bot.getWar().getTeamForFC(subOutFC)
        if subOutName == "":
            subOutName = subOutMiiName
        subInStartRace = raceNum
        subInEndRace = this_bot.getWar().getNumberOfRaces()
        this_bot.add_save_state(message.content)
        this_bot.getRoom().add_sub(subInFC, subInStartRace, subInEndRace, subOutFC, subOutName, subOutStartRace, subOutEndRace, subOutScores)
        this_bot.getWar().setTeamForFC(subInFC, subOutTag)
        await message.channel.send(f"Got it. **{UtilityFunctions.process_name(subInMiiName + UserDataProcessing.lounge_add(subInFC))}** subbed in for **{UtilityFunctions.process_name(subOutMiiName + UserDataProcessing.lounge_add(subOutFC))}** on race #{subInStartRace}")


    @staticmethod
    async def change_player_score_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, command:str):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) == 1:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += "\n**To edit the GP3 score of the 7th player on the list to 37 points:** *" + server_prefix + "edit 7 3 37*"
            await message.channel.send(to_send)
            return

        if len(args) != 4:
            await message.channel.send("Do " + server_prefix + "edit for an example on how to use this command.")
            return


        playerNum = command.split()[1].strip()
        GPNum = args[2]
        amount = args[3]
        players = this_bot.getRoom().get_sorted_player_list()
        if not GPNum.isnumeric() or not amount.isnumeric():
            await message.channel.send("GP Number and amount must all be numbers. Do " + server_prefix + "edit for an example on how to use this command.")
            return

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
                await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + UserDataProcessing.lounge_add(players[playerNum-1][0]) + " GP" + str(GPNum) + " score edited to " + str(amount) + " points."))
        else:
            lounge_name = str(copy.copy(playerNum))
            loungeNameFCs = UserDataProcessing.getFCsByLoungeName(lounge_name)
            for _playerNum, (fc, _) in enumerate(players, 1):
                if fc in loungeNameFCs:
                    break
            else:
                _playerNum = None


            if _playerNum is None:
                await message.channel.send("Could not find Lounge name " + UtilityFunctions.process_name(str(lounge_name)) + " in this room.")
            else:
                this_bot.add_save_state(message.content)
                this_bot.getWar().addEdit(players[_playerNum-1][0], GPNum, amount)
                await message.channel.send(UtilityFunctions.process_name(players[_playerNum-1][1] + UserDataProcessing.lounge_add(players[_playerNum-1][0]) + " GP" + str(GPNum) + " score edited to " + str(amount) + " points."))



    #Code is quite similar to chane_player_tag_command, potential refactor opportunity?
    @staticmethod
    async def change_player_name_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, command:str):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) < 3:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += "\n**To change the name of the 8th player on the list to \"joe\", do:** *" + server_prefix + "changename 8 joe*"
            await message.channel.send(to_send)
            return


        playerNum = command.split()[1].strip()
        new_name = " ".join(command.split()[2:])
        players = this_bot.getRoom().get_sorted_player_list()
        if playerNum.isnumeric():
            playerNum = int(playerNum)
            if playerNum < 1 or playerNum > len(players):
                await message.channel.send("The player number must be on this list (between 1 and " + str(len(players)) + "). Do " + server_prefix + "changename for an example on how to use this command.")
            else:
                this_bot.add_save_state(message.content)
                this_bot.getRoom().setNameForFC(players[playerNum-1][0], new_name)
                await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + UserDataProcessing.lounge_add(players[playerNum-1][0])) + " name set to: " + UtilityFunctions.process_name(new_name))
        else:
            lounge_name = str(copy.copy(playerNum))
            loungeNameFCs = UserDataProcessing.getFCsByLoungeName(lounge_name)
            for _playerNum, (fc, _) in enumerate(players, 1):
                if fc in loungeNameFCs:
                    break
            else:
                _playerNum = None


            if _playerNum is None:
                await message.channel.send("Could not find Lounge name " + UtilityFunctions.process_name(str(lounge_name)) + " in this room.")
            else:
                this_bot.add_save_state(message.content)
                this_bot.getRoom().setNameForFC(players[_playerNum-1][0], new_name)
                await message.channel.send(UtilityFunctions.process_name(players[_playerNum-1][1] + UserDataProcessing.lounge_add(players[_playerNum-1][0])) + " name set to: " + UtilityFunctions.process_name(new_name))

    @staticmethod
    async def change_player_tag_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, command:str):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)


        if this_bot.getWar().is_ffa():
            to_send = "You cannot change a player's tag in an FFA. FFAs have no teams."
            await message.channel.send(to_send)
            return

        if len(args) < 3:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += "\n**To change the tag of the 8th player on the list to KG, do:** *" + server_prefix + "changetag 8 KG*"
            await message.channel.send(to_send)
            return

        elif len(args) >= 3:
            playerNum = command.split()[1].strip()
            new_tag = " ".join(command.split()[2:])
            players = this_bot.getRoom().get_sorted_player_list()
            if playerNum.isnumeric():
                playerNum = int(playerNum)
                if playerNum < 1 or playerNum > len(players):
                    await message.channel.send("The player number must be on this list (between 1 and " + str(len(players)) + "). Do " + server_prefix + "changetag for an example on how to use this command.")
                else:
                    this_bot.add_save_state(message.content)
                    this_bot.getWar().setTeamForFC(players[playerNum-1][0], new_tag)
                    await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + UserDataProcessing.lounge_add(players[playerNum-1][0])) + " tag set to: " + UtilityFunctions.process_name(new_tag))
            else:
                lounge_name = str(copy.copy(playerNum))
                loungeNameFCs = UserDataProcessing.getFCsByLoungeName(lounge_name)
                for _playerNum, (fc, _) in enumerate(players, 1):
                    if fc in loungeNameFCs:
                        break
                else:
                    _playerNum = None


                if _playerNum is None:
                    await message.channel.send("Could not find Lounge name " + UtilityFunctions.process_name(str(lounge_name)) + " in this room.")
                else:
                    this_bot.add_save_state(message.content)
                    this_bot.getWar().setTeamForFC(players[_playerNum-1][0], new_tag)
                    await message.channel.send(UtilityFunctions.process_name(players[_playerNum-1][1] + UserDataProcessing.lounge_add(players[_playerNum-1][0])) + " tag set to: " + UtilityFunctions.process_name(new_tag))


    #Refactor this method to make it more readable
    @staticmethod
    @TimerDebuggers.timer_coroutine
    async def start_war_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, command:str, permission_check:Callable):
        await mkwx_check(message, "Start war command disabled.")
        rlCooldown = this_bot.getRLCooldownSeconds()
        if rlCooldown > 0:
            await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.", delete_after=5.0)
            return


        server_id = message.guild.id
        author_id = message.author.id
        message_id = message.id
        author_name = message.author.display_name
        
        yes_terms = {'on', 'yes', 'true'}
        no_terms = {'off', 'no', 'false'}

        largetime_regex = f"(sui|psb|professionalseriesbagging)=({'|'.join(yes_terms | no_terms)})"
        ignoreLargeTimes = None
        if m := re.search(largetime_regex, command, re.IGNORECASE):
            ignoreLargeTimes = m.group(2).lower() in yes_terms
            command = re.sub(largetime_regex, "", command, flags=re.IGNORECASE)

        use_miis_regex = f"(usemiis|usemii|miis|mii|miinames|miiname|miiheads|miihead)=({'|'.join(yes_terms | no_terms)})"
        useMiis = None
        if m := re.search(use_miis_regex, command, re.IGNORECASE):
            useMiis = m.group(2).lower() in yes_terms
            command = re.sub(use_miis_regex, "", command, flags=re.IGNORECASE)

        num_gps_regex = f"(gp|gps|setgps)=(\d+)"
        numgps = 3
        if m := re.search(num_gps_regex, command, re.IGNORECASE):
            numgps = int(m.group(2))
            if numgps < 1:
                numgps = 1
            elif numgps > 15:
                numgps = 15
            command = re.sub(num_gps_regex, "", command, flags=re.IGNORECASE)

        args = command.split()
        if len(args) < 3:
            await message.channel.send(f"Do `{server_prefix}quickstart` for help on how to use this command.")
            return
        
        war_format_arg = args[1].lower()
        num_teams_arg = args[2]                
        warFormat = UtilityFunctions.convert_to_warFormat(war_format_arg)
        if useMiis is None:
            useMiis = ServerFunctions.get_server_mii_setting(server_id)
        if ignoreLargeTimes is None:
            ignoreLargeTimes = ServerFunctions.is_sui_from_format(server_id, warFormat)

        war = None
        try:
            war = War.War(warFormat, num_teams_arg, message.id, numgps, ignoreLargeTimes=ignoreLargeTimes, displayMiis=useMiis)
        except TableBotExceptions.InvalidWarFormatException:
            await message.channel.send("War format was incorrect. Valid options: FFA, 1v1, 2v2, 3v3, 4v4, 5v5, 6v6. War not created.")
            return
        except TableBotExceptions.InvalidNumberOfPlayersException:
            await message.channel.send("Too many players based on the teams and war format. War not created.")
            return
        except TableBotExceptions.InvalidNumPlayersInputException:
            await message.channel.send("Invalid number of players. The number of players must be an number.")
            return

        if len(args) > 3 and is_lounge_server and not permission_check(message.author) and common.is_prod:
            await message.channel.send(f"You can only load a room for yourself in Lounge. Do this instead: `{server_prefix}{args[0]} {war_format_arg} {num_teams_arg}`")
            return

        to_load = SmartTypes.create_you_discord_id(message.author.id)
        if len(args) > 3:
            to_load = " ".join(args[3:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.ROOM_LOOKUP_TYPES)

        message2 = await message.channel.send("Loading room...")
        this_bot.updateRLCoolDown()
        status = await this_bot.load_table_smart(smart_type, war, message_id=message_id, setup_discord_id=author_id, setup_display_name=author_name)
        if not status:
            descriptive, pronoun = smart_type.get_clean_smart_print(message)
            failure_message = f"Could not find {descriptive} in a room, **did {pronoun} finish the first race?**"
            if smart_type.get_type() is smart_type.RXX:
                f"Could not load the room for {descriptive}, {pronoun} may be more than 24 hours old, or **{pronoun} didn't finish the first race.**"
            if status.status is status.NO_KNOWN_FCS:
                failure_message = f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?"
            await message2.edit(failure_message)
            return


        this_bot.freeLock()
        this_bot.getRoom().setSetupUser(author_id,  message.author.display_name)
        if this_bot.getWar() is not None:
            players = list(this_bot.getRoom().getFCPlayerListStartEnd(1, numgps*4).items())
            tags_player_fcs = TagAIShell.determineTags(players, this_bot.getWar().playersPerTeam)
            this_bot.getWar().set_temp_team_tags(tags_player_fcs)

            if not this_bot.getWar().is_ffa():
                to_send = f"{this_bot.getWar().get_tags_str()}\n***Is this correct?***"
                view = Components.ConfirmView(this_bot, server_prefix, is_lounge_server)
                this_bot.prev_command_sw = True
                await message2.edit(to_send, view=view)
            else:
                dummy_teams = {}
                for teamNumber in range(0, min(this_bot.getWar().numberOfTeams, len(players))):
                    dummy_teams[players[teamNumber][0]] = str(teamNumber)
                this_bot.getWar().setTeams(dummy_teams)
                await message2.edit(this_bot.get_room_started_message(), view=Components.PictureView(this_bot, server_prefix, is_lounge_server))
                TableBot.last_wp_message[this_bot.channel_id] = message2
            this_bot.setShouldSendNotification(True)

            
    @staticmethod                  
    async def after_start_war_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server, custom_message="Unexpected error. Somehow, there is no room loaded. Recommend the command: {server_prefix}reset")

        if args[0].lower().strip() not in ['yes', 'no', 'y', 'n']:
            await message.channel.send(f"Respond `{server_prefix}yes` or `{server_prefix}no`. Were the teams I sent correct?")
            return

        this_bot.prev_command_sw = False
        this_bot.manualWarSetUp = False
        if args[0].lower().strip() in ['no', 'n']:
            this_bot.manualWarSetUp = True
            # view = Components.ManualTeamsView(this_bot, server_prefix, is_lounge_server)
            return await message.channel.send(content=f"***Input the teams in the following format: *** Suppose for a 2v2v2, tag A is 2 and 3 on the list, B is 1 and 4, and Player is 5 and 6, you would enter:  *{server_prefix}A 2 3 / B 1 4 / Player 5 6*")
            #return await message.channel.send(f"***Input the teams in the following format: *** Suppose for a 2v2v2, tag A is 2 and 3 on the list, B is 1 and 4, and Player is 5 and 6, you would enter:  `@MKW Table Bot A 2 3 / B 1 4 / Player 5 6` (**you must use my bot mention as the prefix or the `/raw` slash command**)")

        numGPS = this_bot.getWar().numberOfGPs
        players = list(this_bot.getRoom().getFCPlayerListStartEnd(1, numGPS*4).items())

        if len(players) != this_bot.getWar().get_num_players():
            await message.channel.send(f'''**Warning:** *the number of players in the room doesn't match your war format and teams. **Table started, but teams might be incorrect.***''')

        this_bot.getWar().setTeams(this_bot.getWar().getConvertedTempTeams())
        view = Components.PictureView(this_bot, server_prefix, is_lounge_server)
        await view.send(message, this_bot.get_room_started_message())
        TableBot.last_wp_message[this_bot.channel_id] = view.message

    @staticmethod
    @TimerDebuggers.timer_coroutine
    async def merge_room_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        rlCooldown = this_bot.getRLCooldownSeconds()
        if rlCooldown > 0:
            await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.", delete_after=5)
            return
        this_bot.updateRLCoolDown()

        to_load = SmartTypes.create_you_discord_id(message.author.id)
        if len(args) > 1:
            # await message.channel.send("Nothing given to mergeroom. No merges nor changes made.")
            # return
            to_load = ' '.join(args[1:])

        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.ROOM_LOOKUP_TYPES)
        descriptive, pronoun = smart_type.get_clean_smart_print(message)
        if to_load in this_bot.getRoom().rLIDs:
            await message.channel.send(f"The rxx number you gave is already merged for this room. I assume you know what you're doing, so I will allow this duplicate merge. If this was a mistake, do `{server_prefix}undo`.")

        
        status, rxx, room_races = await WiimmfiSiteFunctions.get_races_smart(smart_type, hit_lounge_api=True)
        if not status:
            failure_message = f"Could not find {descriptive} in a room. **Make sure the new room has finished the first race before using this command.**"
            if status.status is status.NO_KNOWN_FCS:
                failure_message = f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?"
            if smart_type.is_rxx():
                failure_message = f"Could not load the room for {descriptive}. **Make sure the new room has finished the first race before using this command.**"
            await message.channel.send(failure_message)
            return

        if not smart_type.is_rxx() and rxx in this_bot.getRoom().rLIDs:
            await message.channel.send(f"The room {descriptive} {SmartTypes.to_be_conjugation(descriptive)} currently in is already included in this table. No changes made.")
            return

        this_bot.add_save_state(message.content)
        success_status = await this_bot.add_room_races(rxx, room_races)
        if success_status:
            await message.channel.send(f"Successfully merged with this room: {this_bot.getRoom().getLastRXXString()} | Total number of races played: " + str(len(this_bot.getRoom().races)))
        else:
            this_bot.remove_last_save_state()
            await message.channel.send("An unknown error occurred when trying to merge rooms. No changes made.")


    @staticmethod
    async def table_theme_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) == 1:
            await send_table_theme_list(message, args, this_bot, server_prefix, server_wide=False)

        if len(args) > 1:
            setting = args[1]
            if this_bot.is_valid_style(setting):
                this_bot.add_save_state(message.content)
                this_bot.set_style(setting)
                await message.channel.send(f"Table theme set to: **{this_bot.get_style_name()}**")
            else:
                await message.channel.send(f"That is not a valid table theme setting. To see valid settings, run the command `{server_prefix}{args[0]}` and read carefully.")


    @staticmethod
    async def table_graph_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) == 1:
            await send_available_graph_list(message, args, this_bot, server_prefix, server_wide=False)
        elif len(args) > 1:
            setting = args[1]
            if this_bot.is_valid_graph(setting):
                this_bot.add_save_state(message.content)
                this_bot.set_graph(setting)
                await message.channel.send(f"Table graph set to: **{this_bot.get_graph_name()}**")
            else:
                await message.channel.send(f"That is not a valid graph setting. To see valid settings, run the command `{server_prefix}{args[0]}` and read carefully.")

    @staticmethod
    async def all_players_command(message:discord.Message, this_bot:ChannelBot, server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        await message.channel.send(this_bot.getRoom().get_players_list_string())

    @staticmethod
    async def set_war_name_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, old_command:str):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) < 2:
            await message.channel.send("No war name given. War name not set.")
        else:
            this_bot.add_save_state(message.content)
            this_bot.getWar().setWarName(old_command[len(server_prefix)+len("setwarname"):].strip())
            await message.channel.send("War name set!")
    @staticmethod
    async def get_undos_command(message: discord.Message, this_bot: ChannelBot, server_prefix: str, is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        undo_list = this_bot.get_undo_list()
        await message.channel.send(undo_list)

    @staticmethod
    async def get_redos_command(message: discord.Message, this_bot: ChannelBot, server_prefix: str, is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        
        redo_list = this_bot.get_redo_list()
        await message.channel.send(redo_list)

    @staticmethod
    async def undo_command(message:discord.Message, this_bot:ChannelBot, args: List[str], server_prefix:str, is_lounge_server:bool):   
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        do_all = True if (len(args)>1 and args[1].strip().lower() == "all") else False
    
        undone_command = this_bot.restore_last_save_state(do_all=do_all)
        if undone_command is False:
            await message.channel.send("No commands to undo.")
            return
        mes = "All possible commands have been undone." if do_all else f"The following command has been undone: `{UtilityFunctions.process_name(undone_command)}`"
        await message.channel.send(f"{mes}\nRun `{server_prefix}wp` to make sure table bot is fully refreshed.")

    @staticmethod
    async def redo_command(message: discord.Message, this_bot: ChannelBot, args: List[str], server_prefix: str, is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        do_all = True if (len(args)>1 and args[1].strip().lower() == "all") else False
        redone_command = this_bot.restore_last_redo_state(do_all=do_all)
        if redone_command is False:
            return await message.channel.send("No commands to redo.")

        mes = "All possible commands have been redone." if do_all else f"The following command has been redone: `{UtilityFunctions.process_name(redone_command)}`"
        await message.channel.send(f"{mes}\nRun `{server_prefix}wp` to make sure table bot is fully refreshed.")

    @staticmethod
    async def early_dc_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, dont_send=False): 
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) == 1:
            await message.channel.send("Specify a GP Number. Do: " + server_prefix + 'earlydc <gpNumber>')
            return

        roomSize = None
        if not args[1].isnumeric():
            await message.channel.send("gpNumber must be a number. Do: " + server_prefix + 'earlydc <gpNumber>')
            return

        gpNum = int(args[1])
        raceNum = (gpNum * 4) - 3
        if raceNum < 1 or raceNum > len(this_bot.getRoom().races):
            await message.channel.send("The room hasn't started GP" + str(gpNum) + " yet.")
            return

        if len(args) >= 3:
            if args[2] == 'before' or args[2] == 'notonresults':
                roomSize = this_bot.getRoom().races[raceNum-1].getNumberOfPlayers()

        if roomSize is None:
            roomSize = this_bot.getWar().get_num_players()

        this_bot.add_save_state(message.content)
        this_bot.getRoom().forceRoomSize(raceNum, roomSize)
        mes = "Changed room size to " + str(roomSize) + " players for race #" + str(raceNum) + "."
        if dont_send: return mes + " Make sure to give the correct DC points using `?edit`."
        await message.channel.send(mes)
    

    @staticmethod
    async def change_room_size_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, dont_send=False):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) < 3:
            await message.channel.send("Specify a race number. Do: " + server_prefix + 'changeroomsize <racenumber> <roomsize>')
            return

        if not args[1].isnumeric():
            await message.channel.send("racenumber must be a number. Do: " + server_prefix + 'changeroomsize <racenumber> <roomsize>')
            return
        if not args[2].isnumeric():
            await message.channel.send("roomsize must be a number. Do: " + server_prefix + 'changeroomsize <racenumber> <roomsize>')
            return

        raceNum = int(args[1])
        roomSize = int(args[2])
        if raceNum < 1 or raceNum > len(this_bot.getRoom().races):
            await message.channel.send("The room hasn't played race #" + str(raceNum) + " yet.")
        elif roomSize < 2 or roomSize > 12:
            await message.channel.send("Room size must be between 2 and 12 players. (24P support may come eventually).")
        else:
            this_bot.add_save_state(message.content)
            this_bot.getRoom().forceRoomSize(raceNum, roomSize)
            mes = "Changed room size to " + str(roomSize) + " players for race #" + str(raceNum) + "."
            if not dont_send: await message.channel.send(mes)
            return mes + " Make sure to give the missing players their DC points by using `?edit`."

    @staticmethod
    async def race_results_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) == 1:
            await message.channel.send(str(this_bot.getRoom().races[-1]))
        else:
            if args[1].isnumeric():
                raceNum = int(args[1])
                if raceNum < 1 or raceNum > len(this_bot.getRoom().races):
                    await message.channel.send("You haven't played that many races yet!")
                else:
                    await message.channel.send(str(this_bot.getRoom().races[raceNum-1]))
            else:
                await message.channel.send("That's not a race number!")

    @staticmethod
    @TimerDebuggers.timer_coroutine
    async def war_picture_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str,
                                  is_lounge_server:bool, requester: Union[discord.Member, discord.User, None] = None,
                                  prev_message=None):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        wpCooldown = this_bot.getWPCooldownSeconds()
        if wpCooldown > 0:
            await message.channel.send("Wait " + str(wpCooldown) + " more seconds before using this command.", delete_after=5.0)
            return

        server_id = message.guild.id
        should_send_notification = this_bot.shouldSendNoticiation()
        this_bot.updateWPCoolDown()
        await this_bot.clear_last_wp_button()
        this_bot.clear_last_sug_view()

        if prev_message:
            message2 = prev_message
            @TimerDebuggers.timer_coroutine
            async def prev_message_edit(p):
                await p.edit("Updating room", view=None)
            await prev_message_edit(prev_message)
        else:
            message2 = await message.channel.send("Updating room...")
        old_room_fcs = set(this_bot.getRoom().getFCPlayerListStartEnd(1, this_bot.getWar().numberOfGPs*4))
        update_status = await this_bot.update_table()
        if not update_status:
            await message2.edit(content=f"Room not updated. Please do {server_prefix}sw to load a different room.")
            return
    
        up_to = get_max_specified_race(args)
        include_up_to_str = up_to and up_to<len(this_bot.getRoom().getRaces())

        
        new_room_fcs = set(this_bot.getRoom().getFCPlayerListStartEnd(1, this_bot.getWar().numberOfGPs*4))
        added_fcs = new_room_fcs.difference(old_room_fcs)
        if added_fcs:
            await SmartTypes.SmartLookupTypes(added_fcs).lounge_api_update()

        await message2.edit(content=str(
                                "Room updated. Room has finished " + \
                                        str(len(this_bot.getRoom().getRaces())) +\
                                f" races{f' (showing {up_to} races)' if include_up_to_str else ''}. Last race: " +\
                                str(this_bot.getRoom().races[-1].getTrackNameWithoutAuthor()) +\
                                ((" (last shown: " + str(this_bot.getRoom().races[up_to-1].getTrackNameWithoutAuthor()) + ")") if include_up_to_str else "")
                                )
                            )

        message3 = await message.channel.send("Getting table...")
        usemiis, miiArgRequested, _ = getUseMiis(args)
        uselounge, loungeArgRequested = getUseLoungeNames(args)
        if miiArgRequested and not loungeArgRequested:
            uselounge = not usemiis
        if loungeArgRequested and not miiArgRequested:
            usemiis = not uselounge
        use_lounge_otherwise_mii = False

        if not miiArgRequested and not loungeArgRequested:
            use_lounge_otherwise_mii = True


        lounge_replace = False
        if uselounge:
            lounge_replace = True

        step = this_bot.get_race_size()
        output_gsc_table = False
        if len(args) > 1 and args[1] in {'byrace', 'race'} or (len(args)>2 and args[2] in {'byrace', 'race'}):
            step = 1
        if len(args) > 1 and args[1] in {'gsc'}:
            output_gsc_table = True
                            
        table_text, table_sorted_data = SK.get_war_table_DCS(this_bot, use_lounge_otherwise_mii=use_lounge_otherwise_mii, use_miis=usemiis, lounge_replace=lounge_replace, server_id=server_id, missingRacePts=this_bot.dc_points, step=step, up_to_race=up_to)
        if output_gsc_table:
            table_text = SK.format_sorted_data_for_gsc(table_sorted_data, this_bot.getWar().teamPenalties)
        table_text_with_style_and_graph = table_text + this_bot.get_lorenzi_style_and_graph(prepend_newline=True)
        display_url_table_text = urllib.parse.quote(table_text)
        true_url_table_text = urllib.parse.quote(table_text_with_style_and_graph)
        image_url = common.base_url_lorenzi + true_url_table_text
        table_image_path = str(message.id) + ".png"
        try:
            image_download_success = await common.download_image(image_url, table_image_path)
            if not image_download_success:
                await message.channel.send("Could not download table picture.")
                return
            #did the room have *any* errors? Regardless of ignoring any type of error
            war_had_errors = len(this_bot.getWar().get_all_war_errors_players(this_bot.getRoom(), False)) > 0
            tableWasEdited = len(this_bot.getWar().manualEdits) > 0 or len(this_bot.getRoom().dc_on_or_before) > 0 or len(this_bot.getRoom().forcedRoomSize) > 0 or this_bot.getRoom().had_positions_changed() or len(this_bot.getRoom().get_removed_races_string()) > 0 or this_bot.getRoom().had_subs()
            header_combine_success = ImageCombine.add_autotable_header(errors=war_had_errors, table_image_path=table_image_path, out_image_path=table_image_path, edits=tableWasEdited)
            footer_combine_success = True

            if header_combine_success and this_bot.getWar().displayMiis:
                footer_combine_success = ImageCombine.add_miis_to_table(this_bot, table_sorted_data, table_image_path=table_image_path, out_image_path=table_image_path)
            if not header_combine_success or not footer_combine_success:
                await common.safe_delete(message3)
                await message.channel.send("Internal server error when combining images. Sorry, please notify BadWolf immediately.")
            else:
                embed = discord.Embed(
                    title = "",
                    description="[Edit this table on Lorenzi's website](" + common.base_url_edit_table_lorenzi + display_url_table_text + ")",
                    colour = discord.Colour.dark_blue()
                )

                file = discord.File(table_image_path, filename=table_image_path)
                numRaces = 0
                if this_bot.getRoom() is not None and this_bot.getRoom().races is not None:
                    numRaces = min( (len(this_bot.getRoom().races), this_bot.getRoom().getNumberOfGPS()*4) )
                if up_to is not None:
                    numRaces = up_to
                embed.set_author(name=this_bot.getWar().getWarName(numRaces), icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")
                embed.set_image(url="attachment://" + table_image_path)
                
                temp, error_types = this_bot.getWar().get_war_errors_string_2(this_bot.getRoom(), this_bot.get_resolved_errors(), lounge_replace, up_to_race=up_to)

                error_message = "\nMore errors occurred. Embed only allows so many errors to display."
                #request_message = f"\n\nPicture requested by {requester}" if requester is not None else ''
                request_message = ""
                if len(temp) + len(error_message) + len(request_message) >= 2048:
                    temp = temp[:2048-len(error_message)-len(request_message)] + error_message + (request_message if request_message else '')
                embed.set_footer(text=temp+(request_message if request_message else ''))
                
                @TimerDebuggers.timer_coroutine
                async def pic_view_func(this_bot, server_prefix, is_lounge_server):
                    pic_view = Components.PictureView(this_bot, server_prefix, is_lounge_server)

                    # Lounge submission button
                    if not this_bot.has_been_lounge_submitted and len(this_bot.room.races) == 12 and message.channel.guild.id == common.MKW_LOUNGE_SERVER_ID:
                        type, tier = common.get_channel_type_and_tier(this_bot.channel_id, this_bot.room.races)
                        if type and tier:
                            pic_view.add_item(Components.SubmitButton(this_bot, type, tier, len(this_bot.room.races)))

                    await pic_view.send(message, file=file, embed=embed)
                    TableBot.last_wp_message[this_bot.channel_id] = pic_view.message

                await pic_view_func(this_bot, server_prefix, is_lounge_server)

                if error_types and len(error_types)>0:
                    # don't display large time suggestions if it's a 5v5 war
                    if this_bot.war.is_5v5():
                        error_types = [x for x in error_types if x['type'] != 'large_time']

                    if len(error_types) != 0:
                        sug_view = Components.SuggestionView(error_types, this_bot, server_prefix, is_lounge_server)
                        await sug_view.send(message)

                await common.safe_delete(message3)

                if should_send_notification and common.current_notification != "":
                    await message.channel.send(common.current_notification.replace("{SERVER_PREFIX}", server_prefix))
                    
        finally:
            if os.path.exists(table_image_path):
                os.remove(table_image_path)

    @staticmethod
    async def table_text_command(message:discord.Message, this_bot:ChannelBot, args: List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        server_id = message.guild.id
        up_to = get_max_specified_race(args)
        try:
            table_text, _ = SK.get_war_table_DCS(this_bot, use_lounge_otherwise_mii=True, use_miis=False, lounge_replace=True, server_id=server_id, missingRacePts=this_bot.dc_points, discord_escape=True, up_to_race=up_to)
            await message.channel.send(table_text)
        except AttributeError:
            common.log_traceback(traceback)
            common.log_error(f"rxx(s) that triggered traceback: {this_bot.getRoom().rLIDs}")
            await message.channel.send(f"Table Bot has a bug, and this mkwx room triggered it. I cannot tally your scores. You should join the Table Bot server by using the invite code *{common.TABLEBOT_SERVER_INVITE_CODE}* and tell developers what happened and for them to check error logs.")

    @staticmethod
    async def manual_war_setup(message:discord.Message, this_bot:ChannelBot, server_prefix:str, is_lounge_server:bool, command:str):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server, custom_message=f"Unexpected error. Somehow, there is no room loaded. Recommend the command: {server_prefix}reset")

        fc_tag = this_bot.getWar().getConvertedTempTeams()

        def setTeamTagAtIndex(index, teamTag):
            for cur_ind, fc in enumerate(fc_tag):
                if cur_ind == index:
                    fc_tag[fc] = teamTag
                    break

        teamBlob = command.split("/")
        for team in teamBlob:
            teamArgs = team.split()
            if len(teamArgs) < 2:
                await message.channel.send("Each team should have at least 1 player. Try putting the teams in again.")
                return

            teamTag = teamArgs[0]
            for pos in teamArgs[1:]:
                if not pos.isnumeric():
                    processed_team_name = UtilityFunctions.process_name(str(teamTag))
                    userinput_team_position = UtilityFunctions.process_name(str(pos))
                    await message.channel.send(f"On team {processed_team_name}, {userinput_team_position} isn't a number. Try putting in the teams again.")
                    return
                setTeamTagAtIndex(int(pos)-1, teamTag)
        else:
            this_bot.manualWarSetUp = False
            this_bot.getWar().setTeams(fc_tag)
            view = Components.PictureView(this_bot, server_prefix, is_lounge_server)
            await view.send(message, this_bot.get_room_started_message())
            TableBot.last_wp_message[this_bot.channel_id] = view.message

    @staticmethod
    async def remove_race_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) == 1:
            await message.channel.send("Here's how to do this command: " + server_prefix + "removerace <raceNumber>\nYou can do **" + server_prefix + "races** to see the races you've played.")
            return

        if not args[1].isnumeric():
            await message.channel.send("That's not a race number!")
            return

        raceNum = int(args[1])
        if raceNum < 1 or raceNum > len(this_bot.getRoom().races):
            await message.channel.send("You haven't played that many races yet!")
            return

        command, save_state = this_bot.get_save_state(message.content)
        success, removed_race = this_bot.getRoom().remove_race(raceNum)
        if not success:
            await message.channel.send("Removing this race failed.")
        else:
            this_bot.add_save_state(command, save_state)
            await message.channel.send(f"Removed race #{removed_race[0]+1}: {removed_race[1]}")

    @staticmethod
    async def gp_display_size_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) != 2:
            await message.channel.send(f"The syntax of this command is `{server_prefix}{args[0]} <displaySize>`")
            return

        new_size = args[1]
        if not new_size.isnumeric():
            await message.channel.send(f"displaySize must be a number. For example, `{server_prefix}{args[0]} 1`")
            return

        new_size = int(new_size)
        if new_size < 1 or new_size > 32:
            await message.channel.send(f"displaySize must be between 1 and 32. For example, `{server_prefix}{args[0]} 1`")
        else:
            this_bot.add_save_state(message.content)
            this_bot.set_race_size(new_size)
            await message.channel.send(f"Each section of the table will now be {new_size} races.")

    @staticmethod
    async def quick_edit_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, dont_send=False):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) == 1:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += "\n**To change the placement of the 8th player on the list for the 7th race to 4th place, do:** *" + server_prefix + "changeplace 8 7 4*"
            await message.channel.send(to_send)
        elif len(args) == 4:
            # playerNum = command.split()[1].strip()
            playerNum = args[1].strip()
            raceNum = args[2]
            placement = args[3]
            players = this_bot.getRoom().get_sorted_player_list()

            if not raceNum.isnumeric():
                await message.channel.send("The race number must be a number.")
            elif not placement.isnumeric():
                await message.channel.send("The placement number must be a number.")
            else:

                if not playerNum.isnumeric():
                    lounge_name = str(copy.copy(playerNum))
                    loungeNameFCs = UserDataProcessing.getFCsByLoungeName(lounge_name)
                    for _playerNum, (fc, _) in enumerate(players, 1):
                        if fc in loungeNameFCs:
                            break
                    else:
                        _playerNum = None


                    if _playerNum is None:
                        await message.channel.send("Could not find Lounge name " + UtilityFunctions.process_name(str(lounge_name)) + " in this room.")
                    playerNum = _playerNum
                else:
                    playerNum = int(playerNum)
                if playerNum is not None:
                    raceNum = int(raceNum)
                    placement = int(placement)
                    if playerNum < 1 or playerNum > len(players):
                        await message.channel.send("The player number must be on this list (between 1 and " + str(len(players)) + ").")
                    elif raceNum < 1 or raceNum > len(this_bot.getRoom().races):
                        await message.channel.send("The room hasn't played race #" + str(raceNum))
                    elif placement < 1 or placement > len(this_bot.getRoom().races[raceNum-1].placements):
                        await message.channel.send("Race #" + str(raceNum) + " only has " + str(len(this_bot.getRoom().races[raceNum-1].placements)) + "racers, cannot change their place.")
                    else:
                        playerFC = players[playerNum-1][0]
                        if this_bot.getRoom().races[raceNum-1].FCInPlacements(playerFC):
                            this_bot.add_save_state(message.content)
                            #TODO: This needs to call change placement on ROOM, not Race
                            this_bot.getRoom().changePlacement(raceNum, playerFC, placement)
                            mes = "Changed " + UtilityFunctions.process_name(players[playerNum-1][1] + UserDataProcessing.lounge_add(players[playerNum-1][0]) + " place to " + str(placement) + " for race #" + str(raceNum) + ".")
                            if not dont_send: await message.channel.send(mes)
                            return mes
                        else:
                            await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + UserDataProcessing.lounge_add(players[playerNum-1][0]) + " is not in race #" + str(raceNum)))

        else:
            await message.channel.send("Do " + server_prefix + "changeplace to learn how to use this command.")


    @staticmethod
    async def transfer_table_command(message: discord.Message, this_bot: ChannelBot, args: List[str], server_prefix: str, is_lounge_server: bool, table_bots, client):
        if len(args) == 1: #send usage
            return await message.channel.send(f"Usage: `{server_prefix}copyfrom [channelID] (guildID)`\nYou don't need to include the `guildID` if the channel you are transferring from is in this server, otherwise you must include it.")

        if len(args)==2: #copy within server
            channel = args[1]
            try:
                channel_id = int(channel.lstrip('<#').rstrip('>'))
            except:
                return await message.channel.send("Invalid channel.")
            
            if channel_id == message.channel.id:
                return await message.channel.send("You can't copy from the same channel.")

            channel = message.guild.get_channel(channel_id)
            if not channel:
                return await message.channel.send("The channel you provided could not be found.")

            try:
                copied_instance = copy.deepcopy(table_bots[message.guild.id][channel_id])
            except KeyError:
                return await message.channel.send("The table you are trying to copy has not been loaded.")

            ensure_table_loaded_check(copied_instance, server_prefix, is_lounge_server, custom_message="The table you are trying to copy has not been loaded.")

            copied_instance.lastWPTime = None
            copied_instance.channel_id = channel_id
            table_bots[message.guild.id][message.channel.id] = copied_instance #change this instance

            pic_view = Components.PictureView(copied_instance, server_prefix, is_lounge_server)
          
            return await pic_view.send(message, content=f"Table has been copied from <#{channel_id}>.")
        
        # copy from another server
        try:
            channel_id = int(args[1].lstrip('<#').rstrip('>'))
        except:
            return await message.channel.send("Invalid channel.")
        try:
            server_id = int(args[2])
        except:
            return await message.channel.send("Invalid server ID. Use the `Copy ID` function to get a server's ID.")

        guild = client.get_guild(server_id)
        if not guild:
            return await message.channel.send("The server you provided could not be found. *Am I added to the server you are trying to copy from, and do I have access to the channel you are trying to copy from?*")

        channel = guild.get_channel(channel_id)
        if not channel:
            return await message.channel.send("The channel you provided could not be found.")
        
        if channel_id == message.channel.id:
            return await message.channel.send("You can't copy from the same channel.")
        
        try:
            copied_instance = copy.deepcopy(table_bots[server_id][channel_id])
        except KeyError:
            return await message.channel.send("The table you are trying to copy has not been loaded.")

        ensure_table_loaded_check(copied_instance, server_prefix, is_lounge_server, custom_message="The table you are trying to copy has not been loaded.")

        copied_instance.lastWPTime = None
        copied_instance.channel_id = channel_id
        copied_instance.server_id = server_id
        copied_instance.set_style_and_graph(server_id)

        if message.guild.id not in table_bots:
            table_bots[message.guild.id] = {}
        
        table_bots[message.guild.id][message.channel.id] = copied_instance

        pic_view = Components.PictureView(copied_instance, server_prefix, is_lounge_server)
        await pic_view.send(message, content=f"Table has been copied from <#{channel_id}> in {guild.name}.")


#============== Helper functions ================

def get_suggestion(errors, last_race, bot):
    chosen_suggestion = None
    race, possible_suggestions = errors[-1]

    # pick only suggestions from the last race
    # if last_race != race:
    #     return None

    # mark all suggestions this race as resolved
    # for sug in possible_suggestions:
    #     bot.resolved_errors.add(sug['id'])

    for priorityType in ['tie', 'missing_player', 'blank_player', 'gp_missing_1', 'large_time', 'gp_missing']:
        for sug in possible_suggestions:
            if sug['type'] == priorityType:
                chosen_suggestion = sug
                # chosen_suggestion['race'] = race
                return chosen_suggestion  
    return None

async def paginate(message, num_pages, get_page_callback, client):
    authorized_user = message.author.id
    msg = await message.channel.send(get_page_callback(0))

    def check(reaction, user):
        return reaction.message.id == msg.id and authorized_user == user.id \
               and str(reaction.emoji) in {common.LEFT_ARROW_EMOTE, common.RIGHT_ARROW_EMOTE}

    embed_page_start_time = datetime.now()
    current_page = 0

    await msg.add_reaction(common.LEFT_ARROW_EMOTE)
    await msg.add_reaction(common.RIGHT_ARROW_EMOTE)
    while (datetime.now() - embed_page_start_time) < common.embed_page_time:

        timeout_time_delta = common.embed_page_time - (datetime.now() - embed_page_start_time)
        timeout_seconds = timeout_time_delta.total_seconds()
        if timeout_seconds <= 0:
            break

        try:
            reaction, user = await client.wait_for('reaction_add', timeout=timeout_seconds, check=check)
            if str(reaction.emoji) == common.LEFT_ARROW_EMOTE:
                current_page = max((current_page - 1), 0)
            else:
                current_page = min((current_page + 1), num_pages)

            curRoomTxt = get_page_callback(current_page)

            try:
                await msg.edit(content=curRoomTxt)
            except discord.errors.Forbidden:
                await send_missing_permissions(msg.channel)
            except discord.errors.NotFound:
                break
        except:
            pass

    try:
        await msg.clear_reaction(common.LEFT_ARROW_EMOTE)
        await msg.clear_reaction(common.RIGHT_ARROW_EMOTE)
    except:
        pass

valid_gp_flags = ["gp=", "gps=", "setgps="]
def getNumGPs(args, defaultGPs=3):
    if len(args) < 4:
        return -1, defaultGPs

    for valid_flag in valid_gp_flags:
        for index, arg in enumerate(args[3:], 3):
            temp_arg = arg.lower().strip()
            if len(temp_arg) > len(valid_flag) and temp_arg.startswith(valid_flag):
                numGPs = temp_arg[len(valid_flag):]
                if numGPs.isnumeric():
                    numGPs = int(numGPs)
                    if numGPs < 1:
                        return index, 1
                    elif numGPs > 15:
                        return index, 15
                    else:
                        return index, numGPs
    return -1, defaultGPs


valid_mii_flags = ["usemiis=", "usemii=", "miis=", "miinames=", "mii=", "miiname=", 'miiheads=']
def getUseMiis(args, default_use=False, default_start_arg=1):
    if len(args) < 2:
        return default_use, False, -1

    for valid_flag in valid_mii_flags:
        for ind, arg in enumerate(args[default_start_arg:], default_start_arg):
            temp_arg = arg.lower().strip()
            if len(temp_arg) > len(valid_flag) and temp_arg.startswith(valid_flag):
                use_miis_input = temp_arg[len(valid_flag):].strip()
                if use_miis_input in ["y", "yes", "t", "true", 'on']:
                    return True, True, ind
                elif use_miis_input in ["n", "no", "false", "f", 'off']:
                    return False, True, ind
                else:
                    return default_use, False, ind

    return default_use, False, -1

valid_use_lounge_name_flags = ["uselounges=", "uselounge=", "lounges=", "loungenames=", "lounge=", "loungename="]
def getUseLoungeNames(args, default_use=True):
    if len(args) < 2:
        return default_use, False

    for valid_flag in valid_use_lounge_name_flags:
        for arg in args[1:]:
            temp_arg = arg.lower().strip()
            if len(temp_arg) > len(valid_flag) and temp_arg.startswith(valid_flag):
                use_discords_input = temp_arg[len(valid_flag):].strip()
                if use_discords_input in ["y", "yes", "t", "true"]:
                    return True, True
                elif use_discords_input in ["n", "no", "false", "f"]:
                    return False, True
                else:
                    return default_use, False
    return default_use, False

valid_max_race_flags = {'upto=', 'max=', 'maxrace='}
def get_max_specified_race(args):
    '''
    Checks if the user included a maximum race specification and returns it if they did.
    '''
    if len(args) < 2:
        return None

    args = args[1:]

    for flag in valid_max_race_flags:
        for arg in args[::-1]:
            arg = arg.strip().lower()
            start = arg.find('=')+1
            max_race = arg[start:]
            if arg.startswith(flag) and len(arg)>len(flag) and UtilityFunctions.isint(max_race) and int(max_race)>0:
                return int(max_race)

    if UtilityFunctions.isint(args[0]) and int(args[0]) > 0: # if either the first or second argument is numeric, then assume that it is to specify a max race
        return int(args[0])
    
    if len(args)>1 and UtilityFunctions.isint(args[1]) and int(args[1]) > 0:
        return int(args[1])

    
    return None


async def send_table_theme_list(message:discord.Message, args:List[str], this_bot:TableBot.ChannelBot, server_prefix:str, server_wide=False):
    server_wide_or_table_str = "default theme used for tables in this server" if server_wide else 'theme for this table'
    to_send = f"To change the *{server_wide_or_table_str}*, choose a theme number from this list and do `{server_prefix}{args[0]} <themeNumber>`:\n"
    to_send += this_bot.get_style_list_text()
    return await message.channel.send(to_send)

async def send_available_graph_list(message:discord.Message, args:List[str], this_bot:TableBot.ChannelBot, server_prefix:str, server_wide=False):
    server_wide_or_table_str = "default graph used for tables in this server" if server_wide else 'graph for this table'
    to_send = f"To change the *{server_wide_or_table_str}*, choose a graph number from this list and do `{server_prefix}{args[0]} <graphNumber>`:\n"
    to_send += this_bot.get_graph_list_text()
    return await message.channel.send(to_send)

def get_mii_option(option_number) -> str:
    if option_number == "1" or option_number == 1:
        return "**Miis will be shown** at the bottom of the table by default for tables in this server."
    elif option_number == "2" or option_number == 2:
        return "**Miis will NOT be shown** at the bottom of the table by default for tables in this server."
    return "Unknown Option"

def get_large_time_option(option_number) -> str:
    return "Will ignore large times when: " + ServerFunctions.insert_formats(option_number)


async def send_available_mii_options(message:discord.Message, args:List[str], this_bot:TableBot.ChannelBot, server_prefix:str, server_wide=False):
    to_send = f"Choose an option from this list and do `{server_prefix}{args[0]} <optionNumber>`:\n"
    to_send += f"""`1.` {get_mii_option(1)}
`2.` {get_mii_option(2)}"""
    return await message.channel.send(to_send)

async def send_available_large_time_options(message:discord.Message, args:List[str], this_bot:TableBot.ChannelBot, server_prefix:str, server_wide=False):
    to_send = f"Choose an option from this list or comma-separate multiple options and do `{server_prefix}{args[0]} <option>`. (You can either input the number or the word):\n"
    for numVal, val, in LARGE_TIME_OPTIONS.items():
        to_send+="   - `{}` / `{}`\n".format(val, numVal)
    
    return await message.channel.send(to_send)

LARGE_TIME_OPTIONS = {
    '0': "Never",
    '1+': "Always",
    '1': "FFA",
    '2': "2v2",
    '2+': "2v2+",
    '3': "3v3",
    '3+': "3v3+",
    '4': "4v4",
    '4+': "4v4+",
    '5': "5v5",
    '5+': "5v5+",
    '6': "6v6"
}

def dump_vr_is_on():
    with open(common.VR_IS_ON_FILE, "wb") as pickle_out:
        try:
            pkl.dump(vr_is_on, pickle_out)
        except:
            print("Could not dump pickle for vr_is_on. Current state:", vr_is_on)

def load_vr_is_on():
    global vr_is_on
    if os.path.exists(common.VR_IS_ON_FILE):
        with open(common.VR_IS_ON_FILE, "rb") as pickle_in:
            try:
                vr_is_on = pkl.load(pickle_in)
            except:
                print(f"Could not read in '{common.VR_IS_ON_FILE}'")

def example_help(server_prefix:str, original_command:str):
    return f"Do {server_prefix}{original_command} for an example on how to use this command."
