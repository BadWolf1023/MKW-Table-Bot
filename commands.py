'''
Created on Jun 26, 2021

@author: willg
'''

#Bot internal imports - stuff I coded
import asyncio
import ComponentPaginator
from Placement import Placement
import WiimmfiSiteFunctions
import Room
import ServerFunctions
import ImageCombine
import War
import TagAIShell
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
import api.api_common
import Components
from data_tracking import DataTracker
import SmartTypes
import TimerDebuggers

#Other library imports, other people codes
import math
import time
from tabulate import tabulate
from typing import List, Set, Union, Tuple
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

async def send_missing_permissions(channel:discord.TextChannel, content=None, delete_after=7):
    try:
        return await channel.send("I'm missing permissions. Contact your admins. The bot needs these additional permissions:\n- Send Messages\n- Add Reactions (for pages)\n- Manage Messages (to remove reactions)", delete_after=delete_after)
    except discord.errors.Forbidden: #We can't send messages
        pass
#Method looks up the given name to see if any known FCs are on the table and returns the index of the player if it is found
#If the given name was a number, checks to see if the number is actually on the player list and returns the integer version of that index if it is found
#If no FCs of the given player were found on the table, or if the integer given is out of range, an error message is returned
#Returns playerNumber, errorMessage - errorMessage will be None is a playerNumber is found. playerNumber will be None if no playerNumber could be found.
def get_player_number_in_room(message: discord.Message, name: str, room: TableBot.Room.Room, server_prefix: str, command_name: str):
    players = room.get_sorted_player_list()
    playerNum = None

    to_find = SmartTypes.SmartLookupTypes(name, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)

    #If they gave us an integer and it is not a discord ID, check if it's on the list
    if not to_find.is_discord_id() and UtilityFunctions.isint(name):
        playerNum = int(name)
        if playerNum < 1 or playerNum > len(players):
            return None, f"The player number must be between 1 and {len(players)}. Do `{server_prefix}{command_name}` for an example on how to use this command."
        else:
            return playerNum, None

    descriptive, pronoun = to_find.get_clean_smart_print(message)
    player_fcs = to_find.get_fcs()
    if player_fcs is None:
        return None, f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?"

    for playerNum_, (fc, _) in enumerate(players, 1):
        if fc in player_fcs:
            playerNum = playerNum_
            break

    if playerNum is None:
        return None, f"""Could not find {descriptive} in this room."""
    return playerNum, None

    raise TableBotExceptions.UnreachableCode()


async def mkwx_check(message, error_message):
    if common.is_bot_owner(message.author):
        return True

    if common.DISABLE_MKWX_COMMANDS:
        raise TableBotExceptions.CommandDisabled(error_message)
    if common.LIMIT_MKWX_COMMANDS:
        if common.LIMITED_SERVER_IDS is not None and message.guild.id in common.LIMITED_SERVER_IDS:
            return True
        if common.LIMITED_CHANNEL_IDS is not None and message.channel.id in common.LIMITED_CHANNEL_IDS:
            return True
        raise TableBotExceptions.CommandDisabled(error_message)

def get_room_not_loaded_message(server_prefix: str, is_lounge_server=False, custom_message=None, incorrect_use=False):
    BULLET_POINT = '\u2022'
    ROOM_LOAD_EXAMPLES = [
            # Example goal: starting a table with teams, starting a table for yourself
            f"  {BULLET_POINT} Table a 2v2 room with 5 teams that you're in: `{server_prefix}sw 2v2 5`",
            # Example goal: starting an FFA table, starting a table for a player who isn't registered in Lounge
            f"  {BULLET_POINT} Table an FFA room with 12 players that the FC 1000-2010-9010 is in: `{server_prefix}sw FFA 12 1000-2010-9010`",
            # Example goal: starting a table for a player who is registered in Lounge, show that spaces are allowed, show that capitalization does not matter
            f"""  {BULLET_POINT} Table a 3v3 room with 2 teams that someone with the Lounge name "Jack Ryan" (mention them in the command if you don't know their Lounge name) is in: `{server_prefix}sw 3v3 2 Jack ryan`""",
            # Example goal: starting a table for a room that has ended
            f"  {BULLET_POINT} Has the room already ended? Use the `/page playername` command, find the room on the website that you want to table, then use the rxx number in the URL (eg r4203018): `{server_prefix}sw 2v2 6 r4203018`"
            ]
    example_str = "**Here are some examples to get you started:\n**" + "\n".join(ROOM_LOAD_EXAMPLES)
    if custom_message is not None:
        return custom_message.replace("{server_prefix}", server_prefix)
    elif incorrect_use:
        return f"Hmm, that's not how to use this command. {example_str}"
    elif is_lounge_server:
        return f"Table has not been started! Use the command `{server_prefix}sw mogiformat numberofteams` to start a table.\n\n{example_str}"
    else:
        return f"Table has not been started! Use the command `{server_prefix}sw warformat numberofteams (LoungeName/rxx/FC) (gps=numberOfGPs) (psb=on/off) (miis=yes/no)` to start a table.\n\n{example_str}"

def ensure_table_loaded_check(channel_bot: TableBot.ChannelBot, server_prefix: str, is_lounge_server=False, custom_message=None):
    if channel_bot.is_table_loaded():
        return True
    error_message = get_room_not_loaded_message(server_prefix, is_lounge_server, custom_message)
    raise TableBotExceptions.TableNotLoaded(error_message)

def lower_args(args: List[str]) -> List[str]:
    '''Takes a list of strings and returns a list with those strings in lower case form'''
    return [arg.lower() for arg in args]

"""============== Bot Owner only commands ================"""
#TODO: Refactor these - target the waterfall-like if-statements
class BotOwnerCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains all of the commands that are private and only available to me"""

    @staticmethod
    def is_bot_owner_check(author: discord.User, failure_message: str) -> bool:
        if not common.is_bot_owner(author):
            raise TableBotExceptions.NotBadWolf(failure_message)
        return True

    @staticmethod
    async def set_api_url(message: discord.Message, args: List[str]):
        BotOwnerCommands.is_bot_owner_check(message.author, "cannot set public API URL")
        if len(args) != 2:
            await message.channel.send(f"Here's how to use this command: `?{args[0]} public_api_url`")
            return
        public_api_url = args[1]
        common.modify_property({"public_api_url": public_api_url})
        await common.safe_send(message, f"Public API URL set to <{public_api_url}>")

    @staticmethod
    async def reload_properties(message: discord.Message):
        BotOwnerCommands.is_bot_owner_check(message.author, "cannot reload properties")
        common.reload_properties()
        api.api_common.reload_properties()
        await common.safe_send(message, "properties.json reloaded")
    

    @staticmethod
    async def get_logs_command(message: discord.Message):
        BotOwnerCommands.is_bot_owner_check(message.author, "cannot give logs")
        if os.path.exists(common.ERROR_LOGS_FILE):
            await message.channel.send(file=discord.File(common.ERROR_LOGS_FILE))
        if os.path.exists(common.MESSAGE_LOGGING_FILE):
            await message.channel.send(file=discord.File(common.MESSAGE_LOGGING_FILE))
        if os.path.exists(common.FULL_MESSAGE_LOGGING_FILE):
            await message.channel.send(file=discord.File(common.FULL_MESSAGE_LOGGING_FILE))

        Stats.save_metadata()
        await common.safe_send_file(message, '\n'.join([f'{k} {v}' for k,v in Stats.meta['command_count'].items()]))


    #Adds or removes a discord ID to/from the bot admins
    @staticmethod
    async def bot_admin_change(message: discord.Message, args: List[str], adding=True):
        if len(args) != 2:
            await message.channel.send(f"Here's how to use this command: `?{args[0]} discordID`")
            return

        admin_id = args[1]
        smart_type = SmartTypes.SmartLookupTypes(admin_id, allowed_types={SmartTypes.SmartLookupTypes.DISCORD_ID})
        if not smart_type.is_discord_id():
            await message.channel.send(f"{admin_id} is not a valid discord ID.")
            return
        admin_id = smart_type.modified_original
        success = UtilityFunctions.addBotAdmin(admin_id) if adding else UtilityFunctions.removeBotAdmin(admin_id)
        if success:
            add_or_remove = "Added" if adding else "Removed"
            await message.channel.send(f"{add_or_remove} discord ID {admin_id} as a bot admin.")
        else:
            await message.channel.send("Something went wrong. Try again.")


    @staticmethod
    async def add_bot_admin_command(message: discord.Message, args: List[str]):
        BotOwnerCommands.is_bot_owner_check(message.author, "cannot add bot admin")
        await BotOwnerCommands.bot_admin_change(message, args, adding=True)

    @staticmethod
    async def remove_bot_admin_command(message: discord.Message, args: List[str]):
        BotOwnerCommands.is_bot_owner_check(message.author, "cannot remove bot admin")
        await BotOwnerCommands.bot_admin_change(message, args, adding=False)

    @staticmethod
    async def server_process_memory_command(message: discord.Message):
        BotOwnerCommands.is_bot_owner_check(message.author, "cannot show server memory usage")
        command_output = subprocess.check_output('top -b -o +%MEM | head -n 22', shell=True, text=True)
        await message.channel.send(command_output)


    @staticmethod
    async def garbage_collect_command(message: discord.Message):
        BotOwnerCommands.is_bot_owner_check(message.author, "cannot garbage collect")
        gc.collect()
        await message.channel.send("Collected")


    @staticmethod
    async def total_clear_command(message: discord.Message, lounge_update_data: Lounge.Lounge):
        BotOwnerCommands.is_bot_owner_check(message.author, "cannot clear lounge table submission cooldown tracking")
        lounge_update_data.update_cooldowns.clear()
        await message.channel.send("Cleared.")

    @staticmethod
    async def dump_data_command(message: discord.Message, data_dump_function: Callable):
        BotOwnerCommands.is_bot_owner_check(message.author, "cannot dump data")
        successful = await UserDataProcessing.dump_data()
        data_dump_function()
        if successful:
            await message.channel.send("Completed.")
        else:
            await message.channel.send("Failed.")



"""================ Bot Admin Commands =================="""
class BotAdminCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains the commands that only Bot Admins can do"""

    @staticmethod
    async def add_sha_track(message: discord.Message, args: List[str]):
        BotAdminCommands.is_sha_adder_check(message.author, "cannot add sha track")
        if len(args) < 3:
            await message.channel.send("Requires 2 args `SHA, track_name`")
            return
        track_sha = args[1]
        given_track_name = " ".join(args[2:])
        if not UtilityFunctions.is_hex(track_sha):
            await message.channel.send(f"The given track is not an SHA: {track_sha}")
            return
        if track_sha in Race.sha_track_name_mappings:
            await message.channel.send(f"The given track is already in SHA mappings with the following name: {track_sha}\nOverwriting...")
        Race.sha_track_name_mappings[track_sha] = given_track_name
        await message.channel.send(f"Added: {track_sha} -> {given_track_name}")

    @staticmethod
    async def remove_sha_track(message: discord.Message, args: List[str]):
        BotAdminCommands.is_sha_adder_check(message.author, "cannot remove sha track")
        if len(args) != 2:
            await message.channel.send("Requires 1 args `SHA`")
            return
        track_sha = args[1]
        if not UtilityFunctions.is_hex(track_sha):
            await message.channel.send(f"The given track is not an SHA: {track_sha}")
            return
        if track_sha not in Race.sha_track_name_mappings:
            await message.channel.send(f"The given track is not in SHA mappings. Current mappings: {'  |  '.join([str(k)+' : '+str(v) for k,v in Race.sha_track_name_mappings.items()])}")
            return
        removed_track_name = Race.sha_track_name_mappings.pop(track_sha)
        await message.channel.send(f"Removed: {track_sha} -> {removed_track_name}")

    @staticmethod
    def is_bot_admin_check(author: discord.User, failure_message: str) -> bool:
        if not common.is_bot_admin(author):
            raise TableBotExceptions.NotBotAdmin(failure_message)
        return True

    @staticmethod
    def is_sha_adder_check(author: discord.User, failure_message: str) -> bool:
        if not (common.is_bot_admin(author) or common.is_sha_adder(author)):
            raise TableBotExceptions.NotBotAdmin(failure_message)
        return True

    @staticmethod
    async def blacklisted_word_change(message: discord.Message, args: List[str], adding=True):
        if len(args) < 2:
            to_send = "Give a word to blacklist." if adding else "Specify a word to remove from the blacklist."
            await message.channel.send(to_send)
            return
        if len(args) > 2:
            await message.channel.send("The given word cannot have spaces.")
            return

        word = args[1]
        success = UtilityFunctions.add_blacklisted_word(word) if adding else UtilityFunctions.remove_blacklisted_word(word)
        if success:
            to_send = f"Blacklisted the word: {word}" if adding else f"Removed this word from the blacklist: {word}"
            await message.channel.send(to_send)
        else:
            await message.channel.send("Something went wrong. Try again.")

    @staticmethod
    async def remove_blacklisted_word_command(message: discord.Message, args: List[str]):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot remove blacklisted word")
        await BotAdminCommands.blacklisted_word_change(message, args, adding=False)

    @staticmethod
    async def add_blacklisted_word_command(message: discord.Message, args: List[str]):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot add blacklisted word")
        await BotAdminCommands.blacklisted_word_change(message, args, adding=True)


    @staticmethod
    async def blacklist_user_command(message: discord.Message, args: List[str]):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot blacklist user")
        if len(args) < 2:
            await message.channel.send(f"Give a Discord ID to blacklist. If you do not specify a reason for blacklisting a user, the given discord ID will be **removed** from the blacklist. To blacklist a discord ID, give a reason. `?{args[0]} <discordID> (reason)`")
            return

        discord_id = args[1]
        reason = " ".join(args[2:])
        smart_type = SmartTypes.SmartLookupTypes(discord_id, allowed_types={SmartTypes.SmartLookupTypes.DISCORD_ID})
        if not smart_type.is_discord_id():
            await message.channel.send(f"{discord_id} is not a valid discord ID.")
            return
        discord_id = smart_type.modified_original
        success = UserDataProcessing.add_Blacklisted_user(discord_id, reason)
        if not success:
            await message.channel.send("Blacklist failed.")
            return
        if reason:
            await message.channel.send(f"Blacklisted the discord id {discord_id}")
        else:
            await message.channel.send(f"Removed the discord id {discord_id} from the blacklist")
            

    @staticmethod
    async def change_ctgp_region_command(message: discord.Message, args: List[str]):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot change CTGP CTWW region")
        if len(args) != 2:
            await message.channel.send(f"You must give a new CTGP region to use for displaying CTGP WWs. For example, `?{args[0]} vs_40`")
        else:
            new_ctgp_region = args[1]
            Race.set_ctgp_region(new_ctgp_region)
            await message.channel.send(f"CTGP WW Region set to: {new_ctgp_region}")

    @staticmethod
    async def global_vr_command(message: discord.Message, on=True):
        BotAdminCommands.is_bot_admin_check(message.author, "cannot change vr on/off")
        global vr_is_on
        vr_is_on = on
        dump_vr_is_on()
        await message.channel.send(f"Turned ?vr {'on' if on else 'off'}.")


"""================ Statistic Commands =================="""
class StatisticCommands:
    """This class houses all the commands relating to getting data for the meta and players"""

    valid_rt_options = {"rt","rts","regular","regulars","regulartrack","regulartracks"}
    valid_ct_options = {"ct","cts","custom","customs","customtrack","customtracks"}

    valid_rt_tiers = ["t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"]
    valid_ct_tiers = ["t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"]

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
    def validate_rts_cts_arg(arg: str) -> Union[Tuple[bool, None], Tuple[None, str]]:
        is_ct = None
        if arg.lower() in StatisticCommands.valid_rt_options:
            is_ct = False
        elif arg.lower() in StatisticCommands.valid_ct_options:
            is_ct = True

        if is_ct is None:
            return None, f"{UtilityFunctions.clean_for_output(arg)} is not a valid option. Put in **rt** or **ct**."
        return is_ct, None

    @staticmethod
    def validate_tier_arg(arg: str, is_ct: bool) -> Union[Tuple[int, None], Tuple[None, str]]:
        original_arg = arg
        rt_ct_error_string = "CT" if is_ct else "RT"
        arg = arg.lower()

        tier = None
        if not is_ct and arg in StatisticCommands.valid_rt_tiers:
            tier = int(arg.strip("t"))
        elif is_ct and arg in StatisticCommands.valid_ct_tiers:
            tier = int(arg.strip("t"))

        if tier is None:
            return None, f"{UtilityFunctions.clean_for_output(original_arg)} is not a valid {rt_ct_error_string} tier. Valid options for {rt_ct_error_string} tier are: {', '.join(StatisticCommands.valid_ct_tiers) if is_ct else ', '.join(StatisticCommands.valid_rt_tiers)}"
        return tier, None

    @staticmethod
    def validate_days_arg(arg: str) -> Union[Tuple[int, None], Tuple[None, str]]:
        original_arg = arg
        arg = arg.lower().replace("d", "")
        days = None
        if UtilityFunctions.isint(arg):
            days = int(arg)
            if days < 1:
                None, f"{UtilityFunctions.clean_for_output(original_arg)} was given as the number of days, but it must be 1 or more"
            else:
                return days, None
        return None, f"{UtilityFunctions.clean_for_output(original_arg)} must be the number of days"

    @staticmethod
    def validate_tracks_args(args: List[str]) -> Tuple:
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
                return is_ct, None, None, f"{UtilityFunctions.clean_for_output(args[2])} is not a tier nor is it a number of days."

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
    def parse_track_type(command: str) -> Tuple[Union[bool, None], str]:
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
    def parse_track_args(command: str, is_ct=False) -> Tuple[Union[int, None], Union[int, None], Union[int, None], Union[str, None]]:
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
    async def get_track_name(track_lookup):  # TODO: This method returns multiple types (Tuple and List) which is probably a mistake
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
    async def popular_tracks_command(message: discord.Message, args: List[str], server_prefix: str, is_top_tracks=True):
        error_message = f"""Here are 3 examples of how to use this command:
Most played CTs of all time: `{server_prefix}{args[0]} ct`
Most played RTs in the past week: `{server_prefix}{args[0]} rt 7d`
Most played RTs in tier 4 during the last 5 days: `{server_prefix}{args[0]} rt t4 5d`"""

        is_ct, tier, number_of_days, specific_error = StatisticCommands.validate_tracks_args(args)

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

        pages = [get_page_callback(page) for page in range(int(num_pages))]
        paginator = ComponentPaginator.MessagePaginator(pages, show_indicator=True, timeout=common.embed_page_time.seconds)
        await paginator.send(message)

    @staticmethod
    async def player_tracks_command(message: discord.Message, args: List[str], server_prefix: str, sort_asc=False):
        adjective = "worst" if sort_asc else "best"
        command_name = args[0]
        error_message = f"""Here are examples of how to use this command:
- Your {adjective} RTs: `{server_prefix}{command_name} rt`
- Somebody else's {adjective} RTs: `{server_prefix}{command_name} rt [player_name]`
- Your {adjective} RTs in the past week: `{server_prefix}{command_name} rt 7d`
- Your {adjective} RTs in Tier 4: `{server_prefix}{command_name} rt t4`
- Your {adjective} CTs with at least 10 plays: `{server_prefix}{command_name} ct min=10`
"""
        def get_full_error_message(specific_error: str) -> str:
            return f"**Error:** {specific_error}\n\n{error_message}"

        is_ct, rest = StatisticCommands.parse_track_type(" ".join(args).lower())
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
        if lounge_name is None:
            lounge_name = descriptive

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
            table = tabulate(best_tracks[page*tracks_per_page:(page+1)*tracks_per_page], headers, tablefmt="simple",floatfmt=".2f",colalign=["left"], stralign="right")

            message_title = f'{"Worst" if sort_asc else "Best"} {"CTs" if is_ct else "RTs"} for {lounge_name}'
            message_title += filter_descriptor
            message_title += f' [Min {min_count} Plays]'

            return f'```diff\n- {message_title}\n\n{table}```'


        pages = [get_page_callback(page) for page in range(int(num_pages))]

        paginator = ComponentPaginator.MessagePaginator(pages, show_indicator=True, timeout=common.embed_page_time.seconds)
        await paginator.send(message)

    @staticmethod
    async def top_players_command(message: discord.Message, args: List[str], server_prefix: str):
        command_name = args[0]
        error_message = f"""Here are examples of how to use this command:
- Top Maple Treeway players: `{server_prefix}{command_name} treeway`
- Top BC3 players in Tier 5: `{server_prefix}{command_name} bc3 t5`
- Top BC3 players with at least 20 plays: `{server_prefix}{command_name} bc3 min=20`
- Top BC3 players during the last week: `{server_prefix}{command_name} bc3 7d`
"""

        tier,number_of_days,min_count,track_lookup_name = StatisticCommands.parse_track_args(" ".join(args).lower())

        if not track_lookup_name:
            await message.channel.send(
                f"Please specify a track name. \n\n" + error_message)
            return

        track_name, fixed_track_name, is_ct = await StatisticCommands.get_track_name(track_lookup_name.lower().replace(" ", ""))

        if not track_name:
            await message.channel.send(f"No track named `{UtilityFunctions.clean_for_output(track_lookup_name)}` found. \n\n" + error_message)
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
    async def record_command(message: discord.Message, args: List[str], server_prefix: str):  # TODO: This might have broken with new case for args
        command_name = args[0]
        error_message = f"Usage: `{server_prefix}{command_name} player_name (num_days)`"

        if len(args) == 1:
            await message.channel.send(error_message)
            return

        command = " ".join(args[1:])
        days = None
        matches = [x[0] for x in re.findall(r'((^|\s)\d+d?($|\s))',command)]
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
            await message.channel.send(f"No player found with name {UtilityFunctions.clean_for_output(opponent_name)}.\n" + error_message)
            return

        player_did = str(message.author.id)

        if player_did == opponent_did:
            await message.channel.send(f"You can not compare your record against yourself.\n" + error_message)
            return

        result = await DataTracker.DataRetriever.get_record(player_did,opponent_did,days)
        total, wins = result[0]
        if total == 0:
            await message.channel.send(f"You have played no races against {UtilityFunctions.clean_for_output(opponent_name)}")
            return

        losses = total-wins
        await message.channel.send(f'{wins} Wins — {losses} Losses')


"""================== Other Commands ===================="""
#TODO: Refactor these - target the waterfall-like if-statements
class OtherCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains all of the non administrative "stateless" commands"""

    @staticmethod
    async def stats_command(message: discord.Message, client: common.client):
        num_wars = client.getNumActiveWars()
        stats_str = Stats.stats(num_wars, client)
        if stats_str is None:
            await message.channel.send("Error fetching stats. Try again.")
        else:
            await message.channel.send(stats_str)

    @staticmethod
    async def get_flag_command(message: discord.Message, args: List[str], server_prefix: str):
        to_load = SmartTypes.create_you_discord_id(message.author.id)
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
            adverb = "do not" if descriptive == 'you' else 'does not'
            await message.channel.send(f"{SmartTypes.capitalize(descriptive)} {adverb} have a flag set. To set {SmartTypes.possessive(pronoun)} flag for tables, {descriptive} should use `{server_prefix}setflag flagcode`. Flagcodes can be found at: {common.LORENZI_FLAG_PAGE_URL_NO_PREVIEW}")
            return

        image_name = f"{flag}.png"
        if flag.startswith("cl_") and flag.endswith("u"): #Remap this specific flag code to a specific picture
            image_name += 'cl_C3B1u.png'

        embed = discord.Embed(title=f"{SmartTypes.capitalize(SmartTypes.possessive(descriptive))} flag", colour = discord.Colour.dark_blue(), description=flag)
        file = discord.File(f"{common.FLAG_IMAGES_PATH}{image_name}", filename=image_name)
        embed.set_thumbnail(url=f"attachment://{image_name}")
        await message.channel.send(file=file, embed=embed)

    @staticmethod
    async def set_flag_command(message: discord.Message, args: List[str]):
        author_id = message.author.id
        flag_code = args[1].lower() if len(args) > 1 else None
        if flag_code is None or flag_code == "none":
            UserDataProcessing.add_flag(author_id, "")
            await message.channel.send(f"Your flag was successfully removed. If you want to add a flag again in the future, pick a flag code from this website: {common.LORENZI_FLAG_PAGE_URL_NO_PREVIEW}")
            return

        if flag_code not in UserDataProcessing.valid_flag_codes:
            await message.channel.send(f"This is not a valid flag code. For a list of flags and their codes, please visit: {common.LORENZI_FLAG_PAGE_URL_NO_PREVIEW}")
            return

        UserDataProcessing.add_flag(author_id, flag_code)
        await message.channel.send("Your flag was successfully added and will now be displayed on tables.")

        
    @staticmethod
    async def lounge_name_command(message: discord.Message, args: List[str]):
        to_load = SmartTypes.create_you_discord_id(message.author.id)
        if len(args) > 1:
            to_load = " ".join(args[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        await smart_type.lounge_api_update()
        lounge_name = smart_type.get_lounge_name()
        fcs = smart_type.get_fcs()
        descriptive, pronoun = smart_type.get_clean_smart_print(message)
        if fcs is None or lounge_name is None:
            await message.channel.send(f"Could not find a lounge name for {descriptive}, have {pronoun} verified an FC in Lounge?")
            return
        await message.channel.send(f"{SmartTypes.possessive(SmartTypes.capitalize(descriptive))} Lounge name is: **{lounge_name}**")


    @staticmethod
    async def fc_command(message: discord.Message, args: List[str]):
        to_load = SmartTypes.create_you_discord_id(message.author.id)
        if len(args) > 1:
            to_load = " ".join(args[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        await smart_type.lounge_api_update()
        fcs = smart_type.get_fcs()
        if fcs is None:
            descriptive, pronoun = smart_type.get_clean_smart_print(message)
            await message.channel.send(f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?")
            return
        await message.channel.send(fcs[0])

    @staticmethod
    async def player_page_command(message: discord.Message, args: List[str]):
        to_load = SmartTypes.create_you_discord_id(message.author.id)
        if len(args) > 1:
            to_load = " ".join(args[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        descriptive, pronoun = smart_type.get_clean_smart_print(message)
        await smart_type.lounge_api_update()
        fcs = smart_type.get_fcs()
        if fcs is None:
            await message.channel.send(f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?")
            return
        players_pages = [f"{WiimmfiSiteFunctions.SUB_MKWX_URL}p{MiiPuller.fc_to_pid(fc)}" for fc in fcs]
        player_pages_str = "\n".join(players_pages)
        if smart_type.is_fc():
            to_send = f"""{SmartTypes.capitalize(SmartTypes.possessive(descriptive))} player page:\n\n{player_pages_str}"""
        else:
            to_send = f"""{SmartTypes.capitalize(SmartTypes.possessive(descriptive))} player pages, sorted by most recent usage:\n\n{player_pages_str}"""
        await message.channel.send(to_send)
    

    @staticmethod
    async def mii_command(message: discord.Message, args: List[str]):
        if common.MII_COMMAND_DISABLED and not common.is_bot_owner(message.author):
            await message.channel.send("To ensure Table Bot remains stable and can access the website, miis have been disabled at this time.")
            return
        await mkwx_check(message, "Mii command disabled.")

        if cooldown:=mii_cooldown_check(message.author.id):
            return await message.channel.send(f"{message.author.mention}, wait {common.MII_COOLDOWN-cooldown:.1f} seconds before using this command again.")

        to_load = SmartTypes.create_you_discord_id(message.author.id)
        if len(args) > 1:
            to_load = " ".join(args[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        await smart_type.lounge_api_update()
        fcs = smart_type.get_fcs()
        # common.client.mii_cooldowns[message.author.id] = time.monotonic()

        descriptive, pronoun = smart_type.get_clean_smart_print(message)
        if fcs is None:
            await message.channel.send(f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?")
            return

        FC = fcs[0]
        mii_dict = await MiiPuller.get_miis([FC], str(message.id))
        common.client.mii_cooldowns[message.author.id] = time.monotonic()

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
    async def wws_command(message: discord.Message, this_bot: TableBot.ChannelBot, ww_type=Race.RT_WW_REGION):
        await mkwx_check(message, "WWs command disabled.")

        rlCooldown = this_bot.getRLCooldownSeconds()
        if rlCooldown > 0:
            await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.", delete_after=5)
            return

        this_bot.updateRLCoolDown()

        status, mkwx_soup = await WiimmfiSiteFunctions.get_mkwx_soup()
        if not status:
            failure_message = "General mkwx failure, wws command. Report this to a Table Bot developer if you see it."
            if status.status is status.FAILED_REQUEST:
                failure_message = TablingCommands.get_room_load_failure_message(message, None, status)
            await message.channel.send(failure_message)
            return

        parser = WiimmfiSiteFunctions.WiimmfiParser.FrontPageParser(mkwx_soup)
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
    async def vr_command(message: discord.Message, this_bot: TableBot.ChannelBot, args: List[str]):
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
            to_load = " ".join(args[1:])
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
        status, front_race = await this_bot.verify_room_smart(smart_type)
        if not status:
            failure_message = TablingCommands.get_room_load_failure_message(message, smart_type, status)
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
            _, _, races = await WiimmfiSiteFunctions.get_races_for_rxx(front_race.get_rxx())
            str_msg += f"\n\nRaces (Last 12): {Room.Room.get_race_names_abbreviated(races, 12)}"
        await message2.edit(f"{str_msg}```")


class LoungeCommands:

    @staticmethod
    def has_authority_in_server_check(author: discord.User, failure_message: str, authority_check) -> bool:
        if not authority_check(author):
            raise TableBotExceptions.NotStaff(failure_message)
        return True

    @staticmethod
    def correct_server_check(guild: discord.Guild, failure_message: str, server_id) -> bool:
        if guild.id != server_id:
            raise TableBotExceptions.WrongServer(failure_message)
        return True

    @staticmethod
    def updater_channel_check(channel: discord.TextChannel, failure_message: str, valid_channel_ids: Set[int]) -> bool:
        if channel.id not in valid_channel_ids:
            raise TableBotExceptions.WrongUpdaterChannel(failure_message)
        return True

    @staticmethod
    async def who_is_command(message: discord.Message, args: List[str]):
        if not common.is_prod or not common.author_is_lounge_staff(message.author):
            raise TableBotExceptions.NotLoungeStaff("Not staff in MKW Lounge")
        command_name = args[0]
        to_lookup = None
        lookup_limit = common.WHO_IS_LIMIT
        if len(args) > 1 and UtilityFunctions.isint(args[1]):
            to_lookup = int(args[1])

        if len(args) > 2 and common.is_bot_owner(message.author) and args[2].lower() == "all":
            lookup_limit = None

        if to_lookup is None:
            await message.channel.send(f"To find a user, give their discord ID: `?{command_name} DiscordID`")
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
    async def lookup_command(message: discord.Message, args: List[str]):
        if not common.is_bot_owner(message.author):
            raise TableBotExceptions.NotLoungeStaff("Not staff in MKW Lounge")

        if len(args) <= 1:
            await message.channel.send("Give something.")
            return
        full_lookup = " ".join(args[1:])
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
    @staticmethod  # TODO: It seems this method will break when slash commands try to use it with tabletext
    async def _mogi_update(client, message: discord.Message, this_bot: TableBot.ChannelBot, args: List[str], lounge_server_updates: Lounge.Lounge, is_primary=True):
        command_incorrect_format_message = "The format of this command is: `?" + args[0] + " TierNumber RacesPlayed (TableText)`\n- **TierNumber** must be a number. For RTs, between 1 and 8. For CTs, between 1 and 7. If you are trying to submit a squadqueue table, **TierNumber** should be: squadqueue\n-**RacesPlayed** must be a number, between 1 and 32."
        cooldown = lounge_server_updates.get_user_update_submit_cooldown(message.author.id)
        updater_channel_id, updater_link, preview_link, type_text = lounge_server_updates.get_information(is_primary)

        if cooldown > 0:
            await message.channel.send(f"You have already submitted a table very recently. Please wait {cooldown} more seconds before submitting another table.", delete_after=10)
            return

        if len(args) < 3:
            await message.channel.send(command_incorrect_format_message)
            return

        MogiUpdate.update_summary_channels(await message.guild.fetch_channels())
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
            temp = message.content.strip("\n\t ")
            command_removed = temp[temp.index(args[0])+len(args[0]):].strip("\n\t ")
            tier_number_removed = command_removed[command_removed.index(args[1])+len(args[1]):].strip("\n\t ")
            table_text = tier_number_removed[tier_number_removed.index(args[2])+len(args[2]):].strip("\n\t ")


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
                                        description=f"[Click to preview this update]({updater_link})",
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
                                        title=f"Successfully submitted to {type_text} Reporters and {type_text} Updaters",
                                        description=f"[Click to preview this update]({preview_link})",
                                        colour=discord.Colour.dark_red()
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

                    this_bot.has_been_lounge_submitted = True
                    await message.channel.send(file=file, embed=embed)
            finally:
                if os.path.exists(table_image_path):
                    os.remove(table_image_path)
        lounge_server_updates.update_user_cooldown(message.author)
        await common.safe_delete(delete_me)
        await TableBot.last_wp_button[this_bot.channel_id].on_timeout()

    @staticmethod
    async def ct_mogi_update(client, message: discord.Message, this_bot: TableBot.ChannelBot, args: List[str], lounge_server_updates: Lounge.Lounge):
        LoungeCommands.correct_server_check(message.guild, "cannot submit table update for CT mogi", lounge_server_updates.server_id)
        await LoungeCommands._mogi_update(client, message, this_bot, args, lounge_server_updates, is_primary=False)


    @staticmethod
    async def rt_mogi_update(client, message: discord.Message, this_bot: TableBot.ChannelBot, args: List[str], lounge_server_updates: Lounge.Lounge):
        LoungeCommands.correct_server_check(message.guild, "cannot submit table update for RT mogi", lounge_server_updates.server_id)
        await LoungeCommands._mogi_update(client, message, this_bot, args, lounge_server_updates, is_primary=True)


    @staticmethod
    async def _submission_action_command(client, message:discord.Message, args:List[str], lounge_server_updates:Lounge.Lounge, is_approval=True):
        if len(args) < 2:
            await message.channel.send(f"The way to use this command is: `/{args[0]} submissionID`.")
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
                    submissionEmbed.set_field_at(4, name="Approval link:", value=f"[Message]({submissionMessage.jump_url})")

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
                    if hasattr(message, 'is_proxy'): #it's a proxy message from a slash command - you can't react to a slash command
                        await message.channel.send(f"Approved `{submissionID}`") #so send a message instead
                    else:
                        await message.add_reaction(u"\U0001F197")
                else:
                    await submissionMessage.clear_reaction("\u2705")
                    await submissionMessage.add_reaction("\u274C")
                    is_pending = lounge_server_updates.submission_id_is_pending(submissionID)
                    if not is_pending:
                        is_denied = lounge_server_updates.submission_id_is_denied(submissionID)
                        submission_status = "denied" if is_denied else "approved"
                        extra_message_text = f"Double denying a submission doesn't do anything, so you don't need to worry. You simply might have made a typo for your submission ID, and you should deny the correct one." if is_denied else f"I've given it the X reaction anyway. Don't bother 'approving' it again if it was previously approved and sent to the correct summaries (as this will resend it to the summary channels). Simply check your `/deny` command for typos so you deny the right submission."
                        await submissionMessage.channel.send(f"**Warning:** The submission ({submissionID}) was already **{submission_status}**. {extra_message_text}")
                    lounge_server_updates.deny_submission_id(submissionID)

                    if hasattr(message, 'is_proxy'): #it's a proxy message from a slash command - you can't react to a slash command
                        await message.channel.send(f"Denied `{submissionID}`") #so send a message instead
                    else:
                        await message.add_reaction(u"\U0001F197")
            else:
                await message.channel.send("I couldn't find this submission ID. Make sure you have the right submission ID.")
        else:
            await message.channel.send(f"The way to use this command is: `/{args[0]} submissionID` - `submissionID` must be a number")


    @staticmethod
    async def approve_submission_command(client, message:discord.Message, args:List[str], lounge_server_updates:Lounge.Lounge):
        LoungeCommands.correct_server_check(message.guild, "cannot approve table submission", lounge_server_updates.server_id)
        LoungeCommands.has_authority_in_server_check(message.author, "cannot approve table submission", authority_check=lounge_server_updates.report_table_authority_check)
        LoungeCommands.updater_channel_check(message.channel, "cannot approve table submission", lounge_server_updates.get_updater_channel_ids())
        await LoungeCommands._submission_action_command(client, message, args, lounge_server_updates, is_approval=True)


    @staticmethod
    async def deny_submission_command(client, message:discord.Message, args:List[str], lounge_server_updates:Lounge.Lounge):
        LoungeCommands.correct_server_check(message.guild, "cannot deny table submission", lounge_server_updates.server_id)
        LoungeCommands.has_authority_in_server_check(message.author, "cannot deny table submission", authority_check=lounge_server_updates.report_table_authority_check)
        LoungeCommands.updater_channel_check(message.channel, "cannot deny table submission", lounge_server_updates.get_updater_channel_ids())
        await LoungeCommands._submission_action_command(client, message, args, lounge_server_updates, is_approval=False)


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
    async def show_settings_command(message: discord.Message):
        server_id = message.guild.id
        server_name = message.guild.name
        await message.channel.send(ServerFunctions.get_server_settings(server_name, server_id))


    @staticmethod
    async def large_time_setting_command(message: discord.Message, this_bot: ChannelBot, args: List[str], server_prefix: str):
        if not common.is_beta:
            ServerDefaultCommands.server_admin_check(message.author, "cannot change server default for hiding large times on tables")

        server_id = message.guild.id

        if len(args) == 1:
            await send_available_large_time_options(message, args, this_bot, server_prefix, server_wide=True)
            return

        elif len(args) > 1:
            setting = lower_args(args[1:])
            if len(setting) > 1:
                setting = [e.strip(',') for e in setting]
            valid = False
            if any([('never' in entry and 'always' in entry) for entry in setting]):
                valid = False
            else:
                try:
                    setting = ','.join(setting).strip()
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
        if not common.is_beta:
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
        if not common.is_beta:
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
        if not common.is_beta:
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
        await message.channel.send(this_bot.getRoom().get_sorted_player_list_string(include_fc=True))


    @staticmethod
    async def rxx_command(message:discord.Message, this_bot:ChannelBot, server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        await message.channel.send(f"{this_bot.getRoom().getRXXText()}\n{this_bot.getRoom().get_table_id_text()}")
    
    @staticmethod
    async def table_id_command(message:discord.Message, this_bot:ChannelBot, server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        await message.channel.send(this_bot.getRoom().get_event_id())

    @staticmethod
    async def predict_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix: str, lounge_server_updates: Lounge.Lounge):
        ensure_table_loaded_check(this_bot, server_prefix)

        table_text, _ = SK.get_war_table_DCS(this_bot,use_lounge_otherwise_mii=True,use_miis=False,
                                                            lounge_replace=True,missingRacePts=this_bot.dc_points,
                                                            server_id=message.guild.id,discord_escape=True)

        rt_ct, tier = common.get_channel_type_and_tier(this_bot.channel_id, this_bot.room.races)
        rt_ct, tier = rt_ct or 'rt', tier or 1
        is_primary = rt_ct == 'rt'

        updater_channel_id, updater_link, preview_link, type_text = lounge_server_updates.get_information(is_primary)
        error_code, newTableText, json_data = await MogiUpdate.textInputUpdate(table_text, str(tier), this_bot.war.numberOfGPs*4, is_rt=is_primary)

        if error_code != MogiUpdate.SUCCESS_EC:
            await message.channel.send(
                "Couldn't get prediction preview. Reason: *" + MogiUpdate.table_text_errors.get(error_code, "Unknown Error") + "*")
            return

        preview_link += urllib.parse.quote(json_data)
        preview_link_tiny_url = await URLShortener.tinyurl_shorten_url(preview_link)

        embedVar = discord.Embed(title="Prediction Link",url=preview_link_tiny_url,colour=discord.Color.blue())
        embedVar.set_author(
            name='MMR/LR Prediction',
            icon_url='https://www.mkwlounge.gg/images/logo.png'
        )
        await message.channel.send(embed=embedVar)

    @staticmethod
    async def team_penalty_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        command_name = args[0]
        if this_bot.getWar().is_ffa():
            await message.channel.send(f"You can't give team penalties in FFAs. Do `{server_prefix}pen` to give an individual player a penalty in an FFA.")
            return

        teams = sorted(this_bot.getWar().getTags())
        if len(args) == 1:
            to_send = ""
            for team_arg, team in enumerate(teams, 1):
                to_send += f"{team_arg}. {UtilityFunctions.clean_for_output(team)}\n"
            or_str = f" or `{server_prefix}{command_name} {UtilityFunctions.clean_for_output(teams[0])} 15`" if len(teams) > 0 else ''
            to_send += f"\n**To give the first tag on the list a 15 point penalty:** `{server_prefix}{command_name} 1 15`{or_str}"
            await message.channel.send(to_send)
            return
        if len(args) < 3:
            await message.channel.send(example_help(server_prefix, command_name))
            return

        team_arg = " ".join(args[1:-1])
        amount_arg = args[-1]
        cleaned_team_arg = UtilityFunctions.clean_for_output(team_arg)  
        cleaned_amount_arg = UtilityFunctions.clean_for_output(amount_arg)
        if UtilityFunctions.is_int(team_arg):
            team_num = int(team_arg)
        else:
            lowered_teams = [team.lower() for team in teams]

            team_num = (lowered_teams.index(team_arg.lower())+1) if team_arg.lower() in lowered_teams else None
        if team_num is None:
            await message.channel.send(f"The given tag `{cleaned_team_arg}` is neither a number nor the exact tag of a team. {example_help(server_prefix, command_name)}")
            return
        elif team_num < 1 or team_num > len(teams):
            await message.channel.send(f"The given tag number `{team_num}` is not on the tag list (it should be between 1 and {len(teams)}). {example_help(server_prefix, command_name)}")
            return

        if UtilityFunctions.is_int(amount_arg):
            amount = int(amount_arg)
        else:
            await message.channel.send(f"The penalty amount `{cleaned_amount_arg}` is not a number. {example_help(server_prefix, command_name)}")
            return

        this_bot.add_save_state(message.content)
        team_tag = teams[team_num-1]
        this_bot.getWar().addTeamPenalty(team_tag, amount)
        await message.channel.send(f"Tag **{UtilityFunctions.clean_for_output(team_tag)}** given a {amount} point penalty.")


    @staticmethod
    async def disconnections_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, dont_send=False):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        command_name = args[0]
        if len(args) == 1:
            had_DCS, DC_List_String = this_bot.getRoom().getDCListString(this_bot.getWar().getNumberOfGPS(), True)
            if had_DCS:
                DC_List_String += f"\nIf the first disconnection on this list was on results, do `{server_prefix}{command_name} 1 onresults`\nIf they were not on results, do `{server_prefix}{command_name} 1 before`"
            await message.channel.send(DC_List_String)
            return

        if len(args) < 3:
            await message.channel.send(example_help(server_prefix, 'dcs'))
            return

        missing_per_race = this_bot.getRoom().getMissingOnRace(this_bot.getWar().numberOfGPs, include_blank=False)
        merged = list(itertools.chain(*missing_per_race))
        disconnection_arg = args[1]
        if not UtilityFunctions.is_int(disconnection_arg):
            await message.channel.send(f"`{UtilityFunctions.clean_for_output(disconnection_arg)}` is not a number on the dcs list. {example_help(server_prefix, 'dcs')}")
            return
        disconnection_number = int(disconnection_arg)
        if disconnection_number < 1 or disconnection_number > len(merged):
            await message.channel.send(f"""The given DC number `{disconnection_number}` is not on the dcs list. {example_help(server_prefix, 'dcs')}""")
            return

        on_or_before = args[2].lower().strip("\n").strip()
        race, index = 0, 0  # TODO: This doesn't look very good
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
        mii_name = missing_per_race[race-1][index][1]
        player_name = UserDataProcessing.proccessed_lounge_add(mii_name, player_fc)
        if on_or_before in ["on", "during", "midrace", "results", "onresults"]:
            this_bot.add_save_state(message.content)
            this_bot.getRoom().edit_dc_status(player_fc, race, 'on')
            to_send = f"Saved: {player_name} was on results for race #{race}"
        elif on_or_before in ["before", "prior", "beforerace", "notonresults", "noresults", "off"]:
            this_bot.add_save_state(message.content)
            this_bot.getRoom().edit_dc_status(player_fc, race, 'before')
            to_send = f"Saved: {player_name} was not on results for race #{race}"
        else:
            await message.channel.send(f"""`{UtilityFunctions.clean_for_output(on_or_before)}` must be either `on` or `before`. {example_help(server_prefix, 'dcs')}""")
            return

        if dont_send:
            return to_send
        await message.channel.send(to_send) 


    @staticmethod
    async def player_penalty_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        command = args[0]

        if len(args) == 1:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += f"\n**To give the 2nd player on the list a 15 point penalty:** `{server_prefix}{command} 2 15` (negative number for bonuses)"
            await message.channel.send(to_send)
            return

        if len(args) < 3:
            await message.channel.send(example_help(server_prefix, command))
            return

        player_arg, amount_arg = " ".join(args[1:-1]), args[-1]
        players = this_bot.getRoom().get_sorted_player_list()
        player_num, error_message = get_player_number_in_room(message, player_arg, this_bot.getRoom(), server_prefix, command)
        if not UtilityFunctions.is_int(amount_arg) or int(amount_arg) == 0:
            await message.channel.send(f"The penalty amount must be a non-zero number. {example_help(server_prefix, command)}")
            return
        else:
            amount =  int(amount_arg)

        if player_num is None:
            await message.channel.send(error_message)
            return
        player_fc, mii_name = players[player_num-1]
        this_bot.add_save_state(message.content)
        this_bot.getRoom().addPlayerPenalty(player_fc, amount)
        player_name = UserDataProcessing.proccessed_lounge_add(mii_name, player_fc)
        await message.channel.send(f"{player_name} given a {abs(amount) if amount<0 else amount} point {'penalty' if amount>0 else 'bonus'}.")

    @staticmethod
    async def get_subs_command(message: discord.Message, this_bot: ChannelBot, server_prefix: str, is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        subs_string = this_bot.getRoom().get_room_subs()
        await message.channel.send(subs_string)

    @staticmethod
    async def substitute_player_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        command_name = args[0]
        example_error_message = f"Do `{server_prefix}{command_name}` for an example of how to use this command."
        #Command information for user if command is run with no args
        if len(args) == 1:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += f"\n**Example:** If the 1st player on the list subbed in for the 2nd player on the list on race 9, you would do: `{server_prefix}{command_name} 1 2 9`"
            await message.channel.send(to_send)
            return

        #If they don't give the right number of arguments, send an error.
        if len(args) != 4:
            await message.channel.send(example_error_message)
            return

        #If race number isn't a valid number, send error message
        _, sub_in_arg, sub_out_arg, race_num_arg = args
        if not UtilityFunctions.is_int(race_num_arg):
            await message.channel.send(f"The race number must be a number. {example_error_message}")
            return
        race_num = int(race_num_arg)

        if race_num < 2:
            await message.channel.send(f"The race number that the sub began to play must be race 2 or later. {example_error_message}")
            return
        if race_num > this_bot.getWar().getNumberOfRaces():
            await message.channel.send(f"Because your table was started as a {this_bot.getWar().getNumberOfGPS()} GP table, the last possible race someone can sub in is race #{this_bot.getWar().getNumberOfRaces()}")
            return

        sub_in_num, sub_in_error_message = get_player_number_in_room(message, sub_in_arg, this_bot.getRoom(), server_prefix, command_name)
        sub_out_num, sub_out_error_message = get_player_number_in_room(message, sub_out_arg, this_bot.getRoom(), server_prefix, command_name)
        if sub_in_num is None:
            await message.channel.send(sub_in_error_message)
            return
        if sub_out_num is None:
            await message.channel.send(sub_out_error_message)
            return

        if sub_in_num == sub_out_num:
            await message.channel.send("Someone cannot sub in for themselves.")
            return

        sub_out_fc, sub_out_mii_name = this_bot.getRoom().getPlayerAtIndex(sub_out_num-1)
        sub_in_fc, sub_in_mii_name = this_bot.getRoom().getPlayerAtIndex(sub_in_num-1)
        if this_bot.getRoom().fc_subbed_in(sub_in_fc):
            await message.channel.send(f"The person you are trying to sub in has subbed in for someone else already on the table.")
            return
        if this_bot.getRoom().fc_subbed_out(sub_out_fc):
            await message.channel.send(f"The person you are trying to sub out has already subbed out on the table.")
            return
        if this_bot.getRoom().fc_subbed_in(sub_out_fc):
            await message.channel.send(f"Currently, MKW Table Bot does not support double subs. Maybe in the future!")
            return

        sub_out_start_race = 1
        sub_out_end_race = race_num - 1
        sub_out_scores = SK.get_race_scores_for_fc(sub_out_fc, this_bot)[sub_out_start_race-1:sub_out_end_race]
        sub_out_name = UserDataProcessing.lounge_get(sub_out_fc)
        sub_out_tag = this_bot.getWar().getTeamForFC(sub_out_fc)
        if sub_out_name == "":
            sub_out_name = sub_out_mii_name
        sub_in_start_race = race_num
        sub_in_end_race = this_bot.getWar().getNumberOfRaces()
        this_bot.add_save_state(message.content)
        this_bot.getRoom().add_sub(sub_in_fc, sub_in_start_race, sub_in_end_race, sub_out_fc, sub_out_start_race, sub_out_end_race, sub_out_scores)
        this_bot.getWar().setTeamForFC(sub_in_fc, sub_out_tag)
        sub_in_player_name = UserDataProcessing.proccessed_lounge_add(sub_in_mii_name, sub_in_fc)
        sub_out_player_name = UserDataProcessing.proccessed_lounge_add(sub_out_mii_name, sub_out_fc)
        await message.channel.send(f"Got it. **{sub_in_player_name}** subbed in for **{sub_out_player_name}** on race #{sub_in_start_race}")


    @staticmethod
    async def change_player_score_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        command_name = args[0]
        if len(args) == 1:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += f"\n**To edit the GP3 score of the 7th player on the list to 37 points:** *{server_prefix}{command_name} 7 3 37*"
            await message.channel.send(to_send)
            return

        if len(args) < 4:
            await message.channel.send(example_help(server_prefix, command_name))
            return

        player_arg, gp_arg, amount_arg = " ".join(args[1:-2]), args[-2], args[-1]
        player_num, error_message = get_player_number_in_room(message, player_arg, this_bot.getRoom(), server_prefix, command_name)
        if player_num is None:
            await message.channel.send(error_message)
            return
        
        append = amount_arg[0] in "+-"

        if not UtilityFunctions.is_int(gp_arg) or not UtilityFunctions.is_int(amount_arg):
            await message.channel.send(f"GP Number and amount must all be numbers. {example_help(server_prefix, command_name)}")
            return
        else:
            gp_num = int(gp_arg)
            amount = int(amount_arg)


        table_gps = this_bot.getWar().numberOfGPs
        if gp_num < 1 or gp_num > table_gps:
            await message.channel.send(f"The current table is only set to {table_gps} GPs. Your GP number was: {gp_num}")
            return

        players = this_bot.getRoom().get_sorted_player_list()
        player_fc, mii_name = players[player_num-1]
        player_name = UserDataProcessing.proccessed_lounge_add(mii_name, player_fc)

        if append:
            if amount==0:
                return await message.channel.send(f"{player_name} GP{gp_num} score not changed.")
            player_gp_score = sum(SK.calculateGPScoresDCS(gp_num, this_bot.room, this_bot.war.missingRacePts, this_bot.server_id)[player_fc])
            amount += player_gp_score
            if amount<0:
                return await message.channel.send("That's an invalid edit. Players cannot have negative GP scores. Use `/pen` to penalize players.")

        this_bot.add_save_state(message.content)
        this_bot.getWar().addEdit(player_fc, gp_num, amount)
        await message.channel.send(f"{player_name} GP{gp_num} score edited to {amount} points.")

    @staticmethod
    async def change_all_player_score_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        command_name = args[0]

        players = this_bot.getRoom().get_sorted_player_list()

        if len(args) == 1:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            num_players = len(players)
            to_send += f"\n**To edit everyone's GP2 score, please enter the players' scores in the order they appear in the list above:\n** `{server_prefix}{command_name} 2 [#1's GP2 score] [#2's GP2 score] [#3's GP2 score]... [#{num_players}'s GP2 score]`"
            await message.channel.send(to_send)
            return

        if not all(UtilityFunctions.is_int(x) for x in args[1:]):
            await message.channel.send(f"GP Number and all scores must be numbers. {example_help(server_prefix, command_name)}")
            return
        
        gp_num, scores_arg = int(args[1]), [int(gp_score) for gp_score in args[2:]]

        table_gps = this_bot.getWar().numberOfGPs
        if int(args[1]) < 1 or int(args[1]) > table_gps: #didnt use variable to make code clearer
            await message.channel.send(f"GP number {gp_num} is invalid; the current table has {table_gps} GPs. {example_help(server_prefix, command_name)}")
            return

        if len(scores_arg) != len(players):
            descriptive = f"included {len(scores_arg)-len(players)} too many" if len(scores_arg)>len(players) else f"are missing {len(players)-len(scores_arg)}"
            await message.channel.send(f"You {descriptive} player scores. "+example_help(server_prefix, command_name))
            return

        this_bot.add_save_state(message.content)

        for x in range(0, len(scores_arg)):
            player_fc, mii_name = players[x]
            this_bot.getWar().addEdit(player_fc, gp_num, scores_arg[x])

        await message.channel.send(f"Edited all players' scores for GP{gp_num}.")

    #Code is quite similar to change_player_tag_command, potential refactor opportunity?
    @staticmethod
    async def change_player_name_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        command_name = args[0]
        
        if len(args) < 3:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += f"""\n**To change the name of the 8th player on the list to "Joe", do:** *{server_prefix}{command_name} 8 Joe*"""
            await message.channel.send(to_send)
            return

        player = args[1]
        new_name = " ".join(args[2:])
        players = this_bot.getRoom().get_sorted_player_list()
        player_num, error_message = get_player_number_in_room(message, player, this_bot.getRoom(), server_prefix, command_name)
        if player_num is None:
            await message.channel.send(error_message)
            return
        player_fc, mii_name = players[player_num-1]
        player_name = UserDataProcessing.proccessed_lounge_add(mii_name, player_fc)
        this_bot.add_save_state(message.content)
        this_bot.getRoom().setNameForFC(player_fc, new_name)
        await message.channel.send(f"{player_name} name set to: {UtilityFunctions.clean_for_output(new_name)}")

    @staticmethod
    async def change_player_tag_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        command_name = args[0]
        if this_bot.getWar().is_ffa():
            await message.channel.send("You cannot change a player's tag in an FFA. FFAs have no teams.")
            return

        if len(args) < 3:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += f"\n**To change the tag of the 8th player on the list to KG, do:** *{server_prefix}{command_name} 8 KG*"
            await message.channel.send(to_send)
            return

        player_arg, tag_arg = " ".join(args[1:-1]), args[-1]
        players = this_bot.getRoom().get_sorted_player_list()
        player_num, error_message = get_player_number_in_room(message, player_arg, this_bot.getRoom(), server_prefix, command_name)
        if player_num is None:
            await message.channel.send(error_message)
            return
        player_fc, mii_name = players[player_num-1]
        player_name = UserDataProcessing.proccessed_lounge_add(mii_name, player_fc)
        this_bot.add_save_state(message.content)
        new_tag = UtilityFunctions.clean_for_output(tag_arg)
        this_bot.getWar().setTeamForFC(player_fc, new_tag)
        await message.channel.send(f"{player_name} tag set to: {new_tag}")

    #Refactor this method to make it more readable
    @staticmethod
    @TimerDebuggers.timer_coroutine
    async def start_war_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, permission_check:Callable):
        await mkwx_check(message, "Start table command disabled.")
        rlCooldown = this_bot.getRLCooldownSeconds()
        if rlCooldown > 0:
            await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.", delete_after=5.0)
            return

        server_id = message.guild.id
        author_id = message.author.id
        message_id = message.id
        author_name = message.author.display_name
        command = " ".join(args)
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
            await message.channel.send(get_room_not_loaded_message(server_prefix, is_lounge_server, incorrect_use=True))
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
            await message.channel.send("Table format was incorrect. Valid options: FFA, 1v1, 2v2, 3v3, 4v4, 5v5, 6v6. Table not started.")
            return
        except TableBotExceptions.InvalidNumberOfPlayersException:
            await message.channel.send("Too many players based on the teams and table format. Table not started.")
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
            failure_message = TablingCommands.get_room_load_failure_message(message, smart_type, status)
            await message2.edit(failure_message)
            return
        
        this_bot.freeLock()
        this_bot.getRoom().setSetupUser(author_id,  message.author.display_name)
        if this_bot.getWar() is not None:
            players = list(this_bot.getRoom().get_fc_to_name_dict(1, numgps*4).items())
            tags_player_fcs = TagAIShell.determineTags(players, this_bot.getWar().playersPerTeam)
            this_bot.getWar().set_temp_team_tags(tags_player_fcs)

            if not this_bot.getWar().is_ffa():
                to_send = f"{this_bot.getWar().get_tags_str()}\n***Is this correct?***"
                view = Components.ConfirmView(message2, this_bot, server_prefix, is_lounge_server)
                this_bot.prev_command_sw = True
                await message2.edit(to_send, view=view)
            else:
                dummy_teams = {}
                for teamNumber in range(0, min(this_bot.getWar().numberOfTeams, len(players))):
                    dummy_teams[players[teamNumber][0]] = str(teamNumber)
                this_bot.getWar().setTeams(dummy_teams)
                # await message2.edit(this_bot.get_room_started_message(), view=Components.PictureView(this_bot, server_prefix, is_lounge_server))
                # TableBot.last_wp_message[this_bot.channel_id] = message2
                await message2.edit(content=this_bot.get_room_started_message())
                if this_bot.getWPCooldownSeconds() == 0:
                    await TablingCommands.war_picture_command(message2, this_bot, ['wp'], server_prefix, is_lounge_server)
            this_bot.setShouldSendNotification(True)

            
    @staticmethod                  
    async def after_start_war_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server, custom_message="Unexpected error. Somehow, there is no room loaded. Recommend the command: {server_prefix}reset")

        if args[0].lower().strip() not in ['yes', 'no', 'y', 'n']:
            await message.channel.send(f"Respond `{server_prefix}yes` or `{server_prefix}no`. Were the teams I sent correct?")
            return

        this_bot.prev_command_sw = False
        this_bot.manualWarSetUp = False
        this_bot.clear_all_components()
        if args[0].lower().strip() in ['no', 'n']:
            this_bot.manualWarSetUp = True
            # view = Components.ManualTeamsView(this_bot, server_prefix, is_lounge_server)
            return await message.channel.send(content=f"***Input the teams in the following format: *** Suppose for a 2v2v2, tag A is 2 and 3 on the list, B is 1 and 4, and Player is 5 and 6, you would enter:  *{common.client.user.mention} A 2 3 / B 1 4 / Player 5 6*")
            #return await message.channel.send(f"***Input the teams in the following format: *** Suppose for a 2v2v2, tag A is 2 and 3 on the list, B is 1 and 4, and Player is 5 and 6, you would enter:  `@MKW Table Bot A 2 3 / B 1 4 / Player 5 6` (**you must use my bot mention as the prefix or the `/raw` slash command**)")

        numGPS = this_bot.getWar().numberOfGPs
        players = list(this_bot.getRoom().get_fc_to_name_dict(1, numGPS*4).items())

        if len(players) != this_bot.getWar().get_num_players():
            await message.channel.send(f'''**Warning:** *the number of players in the room doesn't match your table format and teams. **Table started, but teams might be incorrect.***''')

        this_bot.getWar().setTeams(this_bot.getWar().getConvertedTempTeams())
        # view = Components.PictureView(this_bot, server_prefix, is_lounge_server)
        # await view.send(message, this_bot.get_room_started_message())
        # TableBot.last_wp_message[this_bot.channel_id] = view.message
        await message.channel.send(this_bot.get_room_started_message())
        message.content = '/wp (auto)'
        await TablingCommands.war_picture_command(message, this_bot, ['wp'], server_prefix, is_lounge_server)

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

        if to_load in this_bot.getRoom().rLIDs:
            await message.channel.send(f"The rxx number you gave is already merged for this room. I assume you know what you're doing, so I will allow this duplicate merge. If this was a mistake, do `/undo`.")
        
        smart_type = SmartTypes.SmartLookupTypes(to_load, allowed_types=SmartTypes.SmartLookupTypes.ROOM_LOOKUP_TYPES)
        status, rxx, _ = await WiimmfiSiteFunctions.get_races_smart(smart_type, hit_lounge_api=True)
        if not status:
            failure_message = TablingCommands.get_room_load_failure_message(message, smart_type, status)
            await message.channel.send(failure_message)
            return

        descriptive, _ = smart_type.get_clean_smart_print(message)
        if not smart_type.is_rxx() and rxx in this_bot.getRoom().rLIDs:
            await message.channel.send(f"The room {descriptive} {SmartTypes.to_be_conjugation(descriptive)} currently in is already included in this table. No changes made.")
            return

        this_bot.add_save_state(message.content)
        load_mes = await message.channel.send("Merging room...")
        success_status = await this_bot.add_room_races(rxx)
        if success_status:
            await load_mes.edit(content=f"Successfully merged with this room: {this_bot.getRoom().getLastRXXString()} | Total number of races played: " + str(len(this_bot.getRoom().races)))
        else:
            this_bot.remove_last_save_state()
            await load_mes.edit(content="An unknown error occurred when trying to merge rooms. No changes made.")

    @staticmethod
    def get_room_load_failure_message(message: discord.Message, smart_type: SmartTypes.SmartLookupTypes, status: WiimmfiSiteFunctions.RoomLoadStatus) -> str: 
        if status.status is status.FAILED_REQUEST:
            return "Couldn't access the Wiimmfi website. Wait a minute, then try again."
            
        descriptive, pronoun = smart_type.get_clean_smart_print(message)
        if status.status is status.NO_KNOWN_FCS:
            return f"Could not find any FCs for {descriptive}, have {pronoun} verified an FC in Lounge?"
        
        if status.status is status.NOT_ON_FRONT_PAGE:
            return f"Could not find {descriptive} in a room, {pronoun} don't seem to be playing right now."
        
        if status.status is status.HAS_NO_RACES:
            if smart_type.is_rxx():
                return f"Could not load the room for {descriptive}, {pronoun} may be more than 24 hours old, or **{pronoun} didn't finish the first race.**"
            return f"Found {descriptive} in a room, **but that room hasn't finished the first race.** Run this command again **after** {pronoun} have finished the first race."
        
        return "General room failure. Report this to a Table Bot developer if you see it."


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
        await message.channel.send(this_bot.getRoom().get_sorted_player_list_string())

    @staticmethod
    async def set_table_name_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        if len(args) < 2:
            await message.channel.send("No table name given. Table name not set.")
        else:
            this_bot.add_save_state(message.content)
            this_bot.getWar().setWarName(" ".join(args[1:]))
            await message.channel.send("Table name set!")

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
        undone_command = re.sub(r"<@!?(\d{15,20})>\s*", "/", undone_command)
        mes = "All possible commands have been undone." if do_all else f"The following command has been undone: `{UtilityFunctions.clean_for_output(undone_command)}`"
        await message.channel.send(f"{mes}\nRun `/wp` to make sure table bot is fully refreshed.")

    @staticmethod
    async def redo_command(message: discord.Message, this_bot: ChannelBot, args: List[str], server_prefix: str, is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        do_all = True if (len(args)>1 and args[1].strip().lower() == "all") else False
        redone_command = this_bot.restore_last_redo_state(do_all=do_all)
        if redone_command is False:
            return await message.channel.send("No commands to redo.")
        redone_command = re.sub(r"<@!?(\d{15,20})>\s*", "/", redone_command)
        mes = "All possible commands have been redone." if do_all else f"The following command has been redone: `{UtilityFunctions.clean_for_output(redone_command)}`"
        await message.channel.send(f"{mes}\nRun `/wp` to make sure table bot is fully refreshed.")

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
        mes = f"Changed room size to {roomSize} players for race #{raceNum}."
        if dont_send: return mes + " Give DC points with `/edit` if necessary."
        await message.channel.send(mes)
    

    @staticmethod
    async def change_room_size_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, dont_send=False):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)

        if len(args) < 3:
            await message.channel.send("Specify a race number. Do: /changeroomsize <racenumber> <roomsize>")
            return

        if not args[1].isnumeric():
            await message.channel.send("racenumber must be a number. Do: /changeroomsize <racenumber> <roomsize>")
            return
        if not args[2].isnumeric():
            await message.channel.send("roomsize must be a number. Do: /changeroomsize <racenumber> <roomsize>")
            return

        raceNum = int(args[1])
        roomSize = int(args[2])
        if raceNum < 1 or raceNum > len(this_bot.getRoom().races):
            await message.channel.send("The room hasn't played race #" + str(raceNum) + " yet.")
        elif roomSize < 2 or roomSize > 12:
            await message.channel.send("Room size must be between 2 and 12 players. (24P support may come eventually).")
        else:
            async def send_mes():
                mes = f"Changed room size to {roomSize} players for race #{raceNum}."
                if not dont_send: await message.channel.send(mes)
                return mes + " Give DC points with `/edit` if necessary."

            # if roomSize == this_bot.room.races[raceNum-1].get_race_size(): # roomSize is already that number
            #     return await send_mes()
            this_bot.add_save_state(message.content)
            this_bot.getRoom().forceRoomSize(raceNum, roomSize)
            return await send_mes()

    @staticmethod
    async def race_results_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        
        command = " ".join(args)
        race_num = 0
        show_team_points = False
        show_team_points_regex = r"(teampoints|points|showpoints|pts|showpts|teampts|showteampts)(=(yes|true|y))?"
        if re.search(show_team_points_regex, command, re.IGNORECASE):
            show_team_points = True
            command = re.sub(show_team_points_regex, "", command, flags=re.IGNORECASE)
        
        args = command.split()

        if len(args) > 1:
            if not UtilityFunctions.is_int(args[1]):
                return await message.channel.send("That's not a valid race number.")
            race_num = int(args[1])
            if race_num < 1 or race_num > len(this_bot.getRoom().races):
                return await message.channel.send("You haven't played that many races yet!")
            
        race = this_bot.getRoom().races[race_num-1]
        rr_str = str(race)
        if show_team_points and not this_bot.getWar().is_ffa():
            rr_str += race.get_team_points_string(this_bot.getWar().teams)
        
        await message.channel.send(rr_str)

    @staticmethod
    @TimerDebuggers.timer_coroutine
    async def war_picture_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str,
                                  is_lounge_server:bool, requester: Union[discord.Member, discord.User, None] = None,
                                  prev_message=None):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        
        wpCooldown = this_bot.getWPCooldownSeconds()
        if wpCooldown > 0:
            await message.channel.send(f"Wait {wpCooldown} more seconds before using this command.", delete_after=5.0)
            return

        server_id = message.guild.id
        should_send_notification = this_bot.shouldSendNotificiation()
        this_bot.updateWPCoolDown()
        await this_bot.clear_last_wp_button()
        this_bot.clear_last_sug_view()

        if prev_message:
            message2 = prev_message
            @TimerDebuggers.timer_coroutine
            async def prev_message_edit(p):
                await p.edit("Updating room...", view=None)
            await prev_message_edit(prev_message)
        else:
            message2 = await message.channel.send("Updating room...")
        old_room_fcs = set(this_bot.getRoom().get_fc_to_name_dict(1, this_bot.getWar().numberOfGPs*4))
        update_status = await this_bot.update_table()
        if not update_status:
            failure_message = "General room failure, table picture. Report this to a Table Bot developer if you see it."
            if update_status.status is update_status.HAS_NO_RACES:
                failure_message =  "The room has does not have any races, so I cannot give you a table."
            elif update_status.status is update_status.NO_ROOM_LOADED:
                failure_message = get_room_not_loaded_message(server_prefix, is_lounge_server)
            elif update_status.status is update_status.FAILED_REQUEST:
                failure_message = TablingCommands.get_room_load_failure_message(message, None, update_status)
            await message2.edit(content=failure_message)
            return
    
        up_to = get_max_specified_race(args)
        include_up_to_str = up_to and up_to<len(this_bot.getRoom().getRaces())

        new_room_fcs = set(this_bot.getRoom().get_fc_to_name_dict(1, this_bot.getWar().numberOfGPs*4))
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
            table_text = SK.format_sorted_data_for_gsc(table_sorted_data)
        table_text_with_style_and_graph = table_text + this_bot.get_lorenzi_style_and_graph(prepend_newline=True)
        display_url_table_text = urllib.parse.quote(table_text)
        true_url_table_text = urllib.parse.quote(table_text_with_style_and_graph)
        image_url = common.base_url_lorenzi + true_url_table_text
        temp_path = './temp/'
        table_image = f"{message.id}_picture.png"
        table_image_path=temp_path+table_image
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
            lorenzi_edit_link = common.base_url_edit_table_lorenzi + display_url_table_text
            full_lorenzi_edit_link = "[Edit this table on Lorenzi's website]({0})"

            if header_combine_success and this_bot.getWar().displayMiis:
                footer_combine_success = ImageCombine.add_miis_to_table(this_bot, table_sorted_data, table_image_path=table_image_path, out_image_path=table_image_path)
           
            if not header_combine_success or not footer_combine_success:
                await common.safe_delete(message3)
                await message.channel.send("Internal server error when combining images. Sorry, please notify BadWolf immediately.")
            else:
                if len(full_lorenzi_edit_link.format(lorenzi_edit_link))>=4000:
                    max_attempts = 2
                    for _ in range(max_attempts):
                        try:
                            lorenzi_edit_link = await URLShortener.tinyurl_shorten_url_special(lorenzi_edit_link)
                            break
                        except URLShortener.URLShortenFailure:
                            await asyncio.sleep(.5)

                full_lorenzi_edit_link = full_lorenzi_edit_link.format(lorenzi_edit_link)
                embed = discord.Embed(
                    title = "",
                    description = full_lorenzi_edit_link,
                    colour = discord.Colour.dark_blue()
                )

                file = discord.File(table_image_path, filename=table_image)
                numRaces = 0
                if this_bot.getRoom() is not None and this_bot.getRoom().races is not None:
                    numRaces = min((len(this_bot.getRoom().races), this_bot.getRoom().getNumberOfGPS()*4))
                if up_to is not None:
                    numRaces = up_to
                
                embed_title = this_bot.getWar().getWarName(numRaces)
                embed.set_author(name=embed_title, icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")
                embed.set_image(url="attachment://" + table_image)
                
                init_string, footer_string, error_types = this_bot.getWar().get_war_errors_string_2(this_bot.getRoom(), this_bot.get_all_resolved_errors(), lounge_replace, up_to_race=up_to)
                full_string = init_string+footer_string
                error_message = "(Too many errors - cannot show previous errors. Full list in file.)\n..."
                error_file = False
                footer_max = min(6000-len(embed_title+full_lorenzi_edit_link), 2048)
                if len(full_string) >= footer_max:
                    error_file = True
                    cutoff = len(full_string+error_message)-footer_max
                    full_string = init_string + error_message + footer_string[cutoff:]

                embed.set_footer(text=full_string)
                
                @TimerDebuggers.timer_coroutine
                async def pic_view_func(this_bot:ChannelBot, server_prefix, is_lounge_server):
                    pic_view = Components.PictureView(this_bot, server_prefix, is_lounge_server)

                    # Lounge submission button
                    if not this_bot.has_been_lounge_submitted and len(this_bot.room.races) == (this_bot.war.numberOfGPs*4) and is_lounge_server:
                        type, tier = common.get_channel_type_and_tier(this_bot.channel_id, this_bot.room.races)
                        if type and tier:
                            pic_view.add_item(Components.SubmitButton(this_bot, type, tier, len(this_bot.room.races)))

                    await pic_view.send(message, file=file, embed=embed)
                    TableBot.last_wp_button[this_bot.channel_id] = pic_view
                    if len(pic_view.message.embeds) == 1: #The embeds were sent successfully
                        this_bot.get_war().set_discord_picture_url(pic_view.message.embeds[0].image.url)     
                    
                await pic_view_func(this_bot, server_prefix, is_lounge_server)

                if error_file:
                    error_file_path = f'{message.id}_full_errors.txt'
                    error_file = common.create_temp_file(error_file_path, init_string+footer_string, dir=temp_path)
                    try:
                        os.remove(temp_path+error_file_path)
                    except Exception:
                        pass
                    
                    await message.channel.send(file=discord.File(fp=error_file, filename=error_file_path))

                if error_types and len(error_types)>0:
                    # don't display large time suggestions if it's a 5v5 war
                    if this_bot.war.is_5v5():
                        error_types = [e for e in error_types if e['type'] != 'large_time']

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
    async def manual_war_setup(message: discord.Message, this_bot: ChannelBot, args: List[str], server_prefix: str, is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server, custom_message=f"Unexpected error. Somehow, there is no room loaded. Recommend the command: {server_prefix}reset")

        fc_tag = this_bot.getWar().getConvertedTempTeams()

        def setTeamTagAtIndex(index, teamTag):
            for cur_ind, fc in enumerate(fc_tag):
                if cur_ind == index:
                    fc_tag[fc] = teamTag
                    break
        
        command = " ".join(args)
        teamBlob = command.split("/")
        for team in teamBlob:
            teamArgs = team.split()
            if len(teamArgs) < 2:
                await message.channel.send("Each team should have at least 1 player. Try putting the teams in again.")
                return

            teamTag = teamArgs[0]
            for pos in teamArgs[1:]:
                if not pos.isnumeric():
                    processed_team_name = UtilityFunctions.clean_for_output(str(teamTag))
                    userinput_team_position = UtilityFunctions.clean_for_output(str(pos))
                    await message.channel.send(f"On team {processed_team_name}, {userinput_team_position} isn't a number. Try putting in the teams again.")
                    return
                setTeamTagAtIndex(int(pos)-1, teamTag)
        else:
            this_bot.manualWarSetUp = False
            this_bot.getWar().setTeams(fc_tag)
            # view = Components.PictureView(this_bot, server_prefix, is_lounge_server)
            # await view.send(message, this_bot.get_room_started_message())
            # TableBot.last_wp_message[this_bot.channel_id] = view.message
            await message.channel.send(this_bot.get_room_started_message())
            await TablingCommands.war_picture_command(message, this_bot, ['wp'], server_prefix, is_lounge_server)


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

        if len(this_bot.getRoom().races) == 1:
            await message.channel.send("You cannot remove every race.")
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
            await message.channel.send(f"Here's how to use this command: `{server_prefix}{args[0]} races_per_gp`")
            return

        new_size = args[1]
        if not new_size.isnumeric():
            await message.channel.send(f"`races_per_gp` must be a number. For example, `{server_prefix}{args[0]} 1`")
            return

        new_size = int(new_size)
        if new_size < 1 or new_size > 32:
            await message.channel.send(f"`races_per_gp` must be between 1 and 32. For example, `{server_prefix}{args[0]} 1`")
        else:
            this_bot.add_save_state(message.content)
            this_bot.set_race_size(new_size)
            await message.channel.send(f"Each section of the table will now be {new_size} races.")

    @staticmethod
    async def race_edit_command(message: discord.Message, this_bot: ChannelBot, args: List[str], is_lounge_server: bool):
        ensure_table_loaded_check(this_bot, '/', is_lounge_server)

        command = args.pop(0)

        syntax = f"\n**Command syntax:** `/{command} [raceNumber] [1st name/number] [2nd name/number]...[last name/number]` (Lounge names with spaces must be entered as one word)"

        if len(args) == 0:
            return await message.channel.send(this_bot.room.get_sorted_player_list_string() + syntax)
        
        try:
            race_num = int(args[0])
            assert(0<race_num<=len(this_bot.room.races))
        except ValueError:
            return await message.channel.send("`raceNumber` must be a number"+syntax)
        except AssertionError:
            return await message.channel.send(f"Invalid `raceNumber`: `raceNumber` must be between 1 and {len(this_bot.room.races)}"+syntax)
        
        race = this_bot.room.races[race_num-1]
        placements = args[1:]
        
        diff = len(placements) - race.numRacers()
        if diff > 0:
            return await message.channel.send(f"You included {diff} too many placements.")
        elif diff < 0:
            return await message.channel.send(f"You are missing {abs(diff)} placements.")
        
        player_nums = list()
        errors = list()
        for player in placements:
            player_num, error_message = get_player_number_in_room(message, player, this_bot.getRoom(), '/', command)
            if player_num is None:
                errors.append(f'**Error:** Player `{player}` - '+error_message)
                continue
            player_nums.append(player_num)
        
        if len(errors):
            return await message.channel.send("\n".join(errors))
        
        players_in_race = {p.FC: p.get_full_display_name() for p in race.get_players_in_race()}

        sorted_list = this_bot.room.get_sorted_player_list()
        players = {sorted_list[num-1][0]: sorted_list[num-1][1] for num in player_nums}
        
        players_in_race_comp = set(players_in_race.keys())
        players_comp = set(players.keys())
        if missing:=players_in_race_comp.difference(players_comp): #they put incorrect players
            missing = [UserDataProcessing.lounge_name_or_mii_name(FC, players_in_race[FC]) for FC in missing]
            incorrect = players_comp.difference(players_in_race_comp)
            incorrect = [UserDataProcessing.lounge_name_or_mii_name(FC, players[FC]) for FC in incorrect]
            incorrect_str = (f"These players aren't in race {race_num}: "+', '.join(incorrect)) if incorrect else ''
            missing_str = (f"\nYou are missing these players in your command: "+', '.join(missing)) if missing else ''
            return await message.channel.send(incorrect_str+missing_str)

        # finally, input has been validated
        this_bot.add_save_state(message.content)

        this_bot.room.change_race_placements(race_num, list(players.keys()))
        await message.channel.send(f"Race {race_num} placements successfully edited.")


    @staticmethod
    async def quick_edit_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, dont_send=False):
        ensure_table_loaded_check(this_bot, server_prefix, is_lounge_server)
        command_name = args[0]
        if len(args) == 1:
            to_send = this_bot.getRoom().get_sorted_player_list_string()
            to_send += f"\n**To change the placement of the 8th player on the list for the 7th race to 4th place, do:** `{server_prefix}{command_name} 8 7 4`"
            await message.channel.send(to_send)
            return
        if len(args) < 4:
            await message.channel.send(example_help(server_prefix, command_name))
            return

        
        player_arg, race_arg, placement_arg = " ".join(args[1:-2]), args[-2], args[-1]
        player_num, error_message = get_player_number_in_room(message, player_arg, this_bot.getRoom(), server_prefix, command_name)
        if player_num is None:
            await message.channel.send(error_message)
            return

        if not UtilityFunctions.is_int(race_arg):
            await message.channel.send(f"The race number must be a number. {example_help(server_prefix, command_name)}")
            return
        if not UtilityFunctions.is_int(placement_arg):
            await message.channel.send(f"The placement number must be a number. {example_help(server_prefix, command_name)}")
            return
        race_num = int(race_arg)
        placement_num = int(placement_arg)
        
        players = this_bot.getRoom().get_sorted_player_list()
        player_fc, mii_name = players[player_num-1]
        player_name = UserDataProcessing.proccessed_lounge_add(mii_name, player_fc)
    
        if race_num < 1 or race_num > len(this_bot.getRoom().races):
            await message.channel.send(f"The room hasn't played race #{race_num}")
            return
        
        if placement_num < 1 or placement_num > len(this_bot.getRoom().races[race_num-1].placements):
            await message.channel.send(f"Race #{race_num} only has {len(this_bot.getRoom().races[race_num-1].placements)} racers, cannot change their place.")
            return

        if not this_bot.getRoom().races[race_num-1].FCInPlacements(player_fc):
            await message.channel.send(f"{player_name} is not in race #{race_num}")
            return

        this_bot.add_save_state(message.content)
        this_bot.getRoom().changePlacement(race_num, player_fc, placement_num)
        mes = f"Changed {player_name} place to {placement_num} for race #{race_num}"
        if not dont_send: await message.channel.send(mes)
        return mes


    @staticmethod
    async def transfer_table_command(message: discord.Message, this_bot: ChannelBot, args: List[str], server_prefix: str, is_lounge_server: bool, table_bots, client):
        if len(args) == 1: #send usage
            return await message.channel.send(f"Usage: `{server_prefix}copyfrom [channelID]`")

        # if len(args)==2: #copy within server
        channel = args[1]
        try:
            channel_id = int(channel.lstrip('<#').rstrip('>'))
        except:
            return await message.channel.send("Invalid channel. You must provide either the channel ID or the channel mention.")
        
        if channel_id == message.channel.id:
            return await message.channel.send("You can't copy from the same channel.")

        guild_id = None

        if channel_id in table_bots[message.guild.id]:
            guild_id = message.guild.id
        
        if not guild_id:
            for server_id, channels in table_bots.items():
                if channel_id in channels:
                    guild_id = server_id
        try:
            copied_instance = copy.deepcopy(table_bots[guild_id][channel_id])
        except KeyError:
            return await message.channel.send("The table you are trying to copy has not been loaded, or the channel couldn't be found. Make sure you enter the correct channel ID (and that I have access to that channel) and that a table is active in that channel.")

        ensure_table_loaded_check(copied_instance, server_prefix, is_lounge_server, custom_message="The table you are trying to copy has not been loaded.")

        copied_instance.lastWPTime = None
        copied_instance.channel_id = message.channel.id
        if guild_id != copied_instance.server_id:
            copied_instance.server_id = message.guild.id
            copied_instance.set_style_and_graph(message.guild.id)
            copied_instance.set_dc_points(message.guild.id)

        table_bots[message.guild.id][message.channel.id].reset() #need to kill the previous instance
        del table_bots[message.guild.id][message.channel.id]
        table_bots[message.guild.id][message.channel.id] = copied_instance #change current channel's instance

        pic_view = Components.PictureView(copied_instance, server_prefix, is_lounge_server)
        
        await pic_view.send(message, content=f"Table has been copied from <#{channel_id}>.")
        TableBot.last_wp_button[this_bot.channel_id] = pic_view


#============== Helper functions ================

def mii_cooldown_check(user):
    last_used = common.client.mii_cooldowns.get(user, None)
    if not last_used:
        return last_used
    interval = time.monotonic()-last_used

    if interval >= common.MII_COOLDOWN:
        return None
    
    return interval

def get_suggestion(errors, last_race, bot):
    chosen_suggestion = None
    race, possible_suggestions = errors[-1]

    for priorityType in ['tie', 'missing_player', 'blank_player', 'gp_missing_1', 'large_time', 'gp_missing']:
        for sug in possible_suggestions:
            if sug['type'] == priorityType:
                chosen_suggestion = sug
                return chosen_suggestion  
    return None

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

async def send_available_large_time_options(message:discord.Message, args:List[str], this_bot:TableBot.ChannelBot, server_prefix:str, server_wide=False):
    to_send = f"Choose an option from this list or comma-separate multiple options and do `{server_prefix}{args[0]} <option>`. (You can either input the number or the word):\n"
    for numVal, val, in LARGE_TIME_OPTIONS.items():
        to_send+="   - `{}` / `{}`\n".format(val, numVal)
    
    return await message.channel.send(to_send)

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
    return f"Do `{server_prefix}{original_command}` for an example on how to use this command."
