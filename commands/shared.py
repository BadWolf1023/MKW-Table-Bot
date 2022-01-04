import discord

import TableBotExceptions
import UserDataProcessing
import common


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


async def sendRoomWarNotLoaded(message: discord.Message, serverPrefix: str, is_lounge=False):
    if is_lounge:
        return await message.channel.send(
            f"Room is not loaded! Use the command `{serverPrefix}sw mogiformat numberOfTeams` to load a room."
        )
    else:
        return await message.channel.send(
            f"Room is not loaded! Use the command `{serverPrefix}sw warformat numberOfTeams (LoungeName/rxx/FC) (gps=numberOfGPs) (psb=on/off) (miis=yes/no)` to start a war."
        )


async def updateData(id_lounge, fc_id):
    UserDataProcessing.smartUpdate(id_lounge, fc_id)


valid_suppress_large_time_flags = ["largetime=off", "largetime=no","largetimes=off", "largetimes=no", "sui=yes","sui=on","sui=true", "lgt=no", "lgt=off", "psb=yes", "psb=on", "psb=true", "professionalseriesbagging=yes", "professionalseriesbagging=true"]
valid_unsuppress_large_time_flags = ["largetime=yes", "largetime=yes","largetimes=on", "largetimes=yes", "sui=no","sui=off","sui=false", "lgt=yes", "lgt=on", "psb=no", "psb=off", "psb=false", "professionalseriesbagging=no", "professionalseriesbagging=false"]


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
