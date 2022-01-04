import asyncio
from typing import List, Callable

import discord

import LoungeAPIFunctions
import ServerFunctions
import TableBotExceptions
import TagAIShell
import UserDataProcessing
import UtilityFunctions
import War
import common
from TableBot import ChannelBot
from commands.shared import mkwx_check, sendRoomWarNotLoaded, updateData


async def start_war_command(
        message: discord.Message,
        this_bot: ChannelBot,
        args: List[str],
        server_prefix: str,
        is_lounge_server: bool,
        command: str,
        permission_check: Callable
):
    await mkwx_check(message, "Start war command disabled.")
    server_id = message.guild.id
    author_id = message.author.id
    message_id = message.id
    author_name = message.author.display_name

    if is_lounge_server and not permission_check(message.author) and (
            len(args) - command.count(" gps=") - command.count(" sui=") - command.count(" psb=")) > 3:
        return await message.channel.send(
            f"You can only load a room for yourself in Lounge. Do this instead: `{server_prefix}{args[0]} {args[1]} {args[2]}`"
        )

    if len(args) < 3:
        # TODO: sui=yes = psb
        return await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)

    rlCooldown = this_bot.getRLCooldownSeconds()
    if rlCooldown > 0:
        delete_me = await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.")
        return await delete_me.delete(delay=5)

    this_bot.reset(server_id)
    warFormat = args[1]
    numTeams = args[2]
    numGPsPos, numgps = getNumGPs(args)
    iLTPos, ignoreLargeTimes = getSuppressLargeTimes(args)
    useMiis, _, miisPos = getUseMiis(args, True, 3)
    if iLTPos >= 0 and 'sui=' in command:
        await message.channel.send(
            "*sui= will change to psb= in later updates. Use psb=yes or professionalseriesbagging=yes in the future*")

    if miisPos < 0:
        useMiis = ServerFunctions.get_server_mii_setting(server_id)
    if iLTPos < 0:
        ignoreLargeTimes = ServerFunctions.get_server_large_time_setting(server_id)

    try:
        this_bot.setWar(
            War.War(warFormat, numTeams, message.id, numgps, ignoreLargeTimes=ignoreLargeTimes, displayMiis=useMiis))
    except TableBotExceptions.InvalidWarFormatException:
        await message.channel.send(
            "War format was incorrect. Valid options: FFA, 1v1, 2v2, 3v3, 4v4, 5v5, 6v6. War not created.")
        return
    except TableBotExceptions.InvalidNumberOfPlayersException:
        await message.channel.send("Too many players based on the teams and war format. War not created.")
        return

    # This is the background task for getting miis, it will be awaited once everything in ?sw finishes
    # Case 1: No mention, get FCs for the user - this happens when len(args) = 3
    # Case 2: Mention, get FCs for the mentioned user, this happens when len(args) > 3 and len(mentions) > 1
    # Case 3: FC: No mention, len(args) > 3, and is FC
    # Case 4: rLID: No mention, len(args) > 3, is rLID
    # Case 5: Lounge name: No mention, len(args) > 3, neither rLID nor FC
    successful = False
    try:
        this_bot.updateRLCoolDown()
        message2 = await message.channel.send("Loading room...")
        if len(args) == 3 or (len(args) > 3 and (numGPsPos == 3 or iLTPos == 3 or miisPos == 3)):
            discordIDToLoad = str(author_id)
            await updateData(*await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad]))
            FCs = UserDataProcessing.get_all_fcs(discordIDToLoad)
            successful = await this_bot.load_room_smart([FCs], message_id=message_id, setup_discord_id=author_id,
                                                        setup_display_name=author_name)
            if not successful:
                await message.channel.send("Could not find you in a room. **Did you finish the first race?**")
        elif len(args) > 3:
            if len(message.raw_mentions) > 0:
                discordIDToLoad = str(message.raw_mentions[0])
                await updateData(*await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad]))
                FCs = UserDataProcessing.get_all_fcs(discordIDToLoad)
                successful = await this_bot.load_room_smart([FCs], message_id=message_id, setup_discord_id=author_id,
                                                            setup_display_name=author_name)
                if not successful:
                    lookup_name = UtilityFunctions.process_name(str(message.mentions[0].name))
                    await message.channel.send(
                        f"Could not find {lookup_name} in a room. **Did they finish the first race?**")
            elif UtilityFunctions.is_rLID(args[3]):
                successful = await this_bot.load_room_smart([args[3]], message_id=message_id,
                                                            setup_discord_id=author_id, setup_display_name=author_name)
                if not successful:
                    await message.channel.send("Could not find this rxx number. Is the room over 24 hours old?")
            elif UtilityFunctions.is_fc(args[3]):
                successful = await this_bot.load_room_smart([args[3]], message_id=message_id,
                                                            setup_discord_id=author_id, setup_display_name=author_name)
                if not successful:
                    await message.channel.send("Could not find this FC in a room. **Did they finish the first race?**")
            else:
                their_name = ""
                for arg in command.split()[3:]:
                    if '=' in arg:
                        break
                    their_name += arg + " "
                their_name = their_name.strip()
                await updateData(*await LoungeAPIFunctions.getByLoungeNames([their_name]))
                FCs = UserDataProcessing.getFCsByLoungeName(their_name)
                successful = await this_bot.load_room_smart([FCs], message_id=message_id, setup_discord_id=author_id,
                                                            setup_display_name=author_name)
                if not successful:
                    processed_lookup_name = UtilityFunctions.process_name(their_name)
                    await message.channel.send(
                        f"Could not find {processed_lookup_name} in a room. **Did they finish the first race?**")
    finally:
        if not successful:
            this_bot.setWar(None)
    # Room loaded successfully
    if successful:
        this_bot.freeLock()
        this_bot.getRoom().setSetupUser(author_id, message.author.display_name)
        if this_bot.getWar() is not None:
            asyncio.create_task(this_bot.populate_miis())
            players = list(this_bot.getRoom().getFCPlayerListStartEnd(1, numgps * 4).items())
            await updateData(*await LoungeAPIFunctions.getByFCs([fc for fc, _ in players]))
            tags_player_fcs = TagAIShell.determineTags(players, this_bot.getWar().playersPerTeam)
            this_bot.getWar().set_temp_team_tags(tags_player_fcs)

            if not this_bot.getWar().is_ffa():
                to_send = f"{this_bot.getWar().get_tags_str()}\n***Is this correct?** Respond `{server_prefix}yes` or `{server_prefix}no`*"
                await message.channel.send(to_send)
                this_bot.prev_command_sw = True

            else:
                dummy_teams = {}

                for teamNumber in range(0, min(this_bot.getWar().numberOfTeams, len(players))):
                    dummy_teams[players[teamNumber][0]] = str(teamNumber)
                this_bot.getWar().setTeams(dummy_teams)
                await message.channel.send(this_bot.get_room_started_message())

            this_bot.setShouldSendNotification(True)
    else:
        this_bot.setWar(None)
        this_bot.setRoom(None)
    if message2 is not None:
        await common.safe_delete(message2)


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


valid_suppress_large_time_flags = ["largetime=off", "largetime=no", "largetimes=off", "largetimes=no", "sui=yes",
                                   "sui=on", "sui=true", "lgt=no", "lgt=off", "psb=yes", "psb=on", "psb=true",
                                   "professionalseriesbagging=yes", "professionalseriesbagging=true"]
valid_unsuppress_large_time_flags = ["largetime=yes", "largetime=yes", "largetimes=on", "largetimes=yes", "sui=no",
                                     "sui=off", "sui=false", "lgt=yes", "lgt=on", "psb=no", "psb=off", "psb=false",
                                     "professionalseriesbagging=no", "professionalseriesbagging=false"]


def getSuppressLargeTimes(args, default_use=False):
    if len(args) < 4:
        return -1, default_use

    for index, arg in enumerate(args[3:], 3):
        if arg.lower().strip() in valid_suppress_large_time_flags:
            return index, True
        if arg.lower().strip() in valid_unsuppress_large_time_flags:
            return index, False

    return -1, default_use


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
