'''
Created on Jun 26, 2021

@author: willg
'''
#Bot internal imports - stuff I coded
import WiimfiSiteFunctions
from WiimfiSiteFunctions import _is_rLID, _is_fc
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
from TableBot import ChannelBot
import UtilityFunctions
import MiiPuller
import SimpleRooms
import Race
import MogiUpdate
import help_documentation
import TableBotExceptions



from common import *

#Other library imports, other people codes
import discord
from typing import List, Set
import asyncio
from collections.abc import Callable
import urllib
import copy
import dill as pkl

vr_is_on = False




async def sendRoomWarNotLoaded(message: discord.Message, serverPrefix:str, is_lounge=False):
    if is_lounge:
        return await message.channel.send(f"Room is not loaded! Use the command `{serverPrefix}sw <format> <numberOfTeams>` to load a room.")  
    else:
        return await message.channel.send(f"Room is not loaded! Use the command `{serverPrefix}sw <format> <numberOfTeams> [LoungeName/rxx/FC] [gps=numberOfGPs] [psb=yes/no] [miis=yes/no]` to start a war.")  

async def updateData(id_lounge, fc_id):
    UserDataProcessing.smartUpdate(id_lounge, fc_id)
    
async def send_missing_permissions(channel:discord.TextChannel, content=None, delete_after=7):
    try:
        return await channel.send("I'm missing permissions. Contact your admins. The bot needs these additional permissions:\n- Send Messages\n- Add Reactions (for pages)\n- Manage Messages (to remove reactions)", delete_after=delete_after)
    except discord.errors.Forbidden: #We can't send messages
        pass
        
"""============== Bad Wolf only commands ================"""
#TODO: Refactor these - target the waterfall-like if-statements
class BadWolfCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains all of the commands that are private and only available to me"""
        
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
        await BadWolfCommands.bot_admin_change(message, args, adding=True)
        
    @staticmethod
    async def remove_bot_admin_command(message:discord.Message, args:List[str]):
        await BadWolfCommands.bot_admin_change(message, args, adding=False)
  
  
  
 
        
"""================ Bot Admin Commands =================="""
#TODO: Refactor these - target the waterfall-like if-statements
class BotAdminCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains the commands that only Bot Admins can do"""
    
    @staticmethod
    async def blacklisted_word_change(message:discord.Message, args:List[str], adding=True):
        author_id = message.author.id
        if str(author_id) not in UtilityFunctions.botAdmins:
            await message.channel.send("**This command is reserved for bot administrators only.**")
            return
        if len(args) <= 1:
            to_send = "Give a word to blacklist." if adding else "Specify a word to remove from the blacklist."
            await message.channel.send(to_send)
            return
        word = str(args[1].strip())
        success = UtilityFunctions.add_blacklisted_word(word) if adding else UtilityFunctions.remove_blacklisted_word(word)
        if success:
            to_send = f"Blacklisted the word: {word}" if adding else f"Removed this word from the blacklist: {word}"
        else:
            await message.channel.send("Something went wrong. Try again.")
            
    @staticmethod
    async def remove_blacklisted_word_command(message:discord.Message, args:List[str]):
        await BadWolfCommands.blacklisted_word_change(message, args, adding=False)
    
    @staticmethod
    async def add_blacklisted_word_command(message:discord.Message, args:List[str]):
        await BadWolfCommands.blacklisted_word_change(message, args, adding=True)
    
    @staticmethod
    async def change_flag_exception(message:discord.Message, args:List[str], user_flag_exceptions:Set[int], adding=True):
        author_id = message.author.id
        if str(author_id) not in UtilityFunctions.botAdmins:
            await message.channel.send("You are not a bot admin.")
            return
        
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
        await BadWolfCommands.change_flag_exception(message, args, user_flag_exceptions, adding=True)
    
    @staticmethod      
    async def remove_flag_exception_command(message:discord.Message, args:List[str], user_flag_exceptions:Set[int]):
        await BadWolfCommands.change_flag_exception(message, args, user_flag_exceptions, adding=False)
    
    @staticmethod
    async def change_ctgp_region_command(message:discord.Message, args:List[str]):
        author_id = message.author.id
        if str(author_id) not in UtilityFunctions.botAdmins:
            await message.channel.send("You are not a bot admin.")
        elif len(args) <= 1:
            await message.channel.send("You must give a new CTGP region to use for displaying CTGP WWs.")
        else:
            Race.set_ctgp_region(args[1])
            await message.channel.send(f"CTGP WW Region set to: {args[1]}")
    
    @staticmethod
    async def global_vr_command(message:discord.Message, on=True):
        global vr_is_on
        author_id = message.author.id
        if str(author_id) in UtilityFunctions.botAdmins:
            vr_is_on = on
            dump_vr_is_on()
            await message.channel.send(f"Turned !vr/?vr {'on' if on else 'off'}.")





"""================== Other Commands ===================="""
#TODO: Refactor these - target the waterfall-like if-statements
class OtherCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains all of the non administrative "stateless" commands"""
    
    @staticmethod
    async def fc_command(message:discord.Message, args:List[str], old_command:str):
        discordIDToLoad = None
        id_lounge = {}
        fc_id = {}
        
        if len(args) == 1:
            discordIDToLoad = str(message.author.id)
            id_lounge, fc_id = await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad])
            await updateData(id_lounge, fc_id)
        else:
            if len(message.raw_mentions) > 0:
                discordIDToLoad = str(message.raw_mentions[0])
                id_lounge, fc_id = await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad])  
            else:
                to_find_lounge = " ".join(old_command.split()[1:])
                id_lounge, fc_id = await LoungeAPIFunctions.getByLoungeNames([to_find_lounge])
                if id_lounge != None and len(id_lounge) == 1:
                    for this_id in id_lounge:
                        discordIDToLoad = this_id
                        break
                if discordIDToLoad == None:
                    discordIDToLoad = UserDataProcessing.get_DiscordID_By_LoungeName(to_find_lounge)
                    
        await updateData(id_lounge, fc_id)    
        FC = None
        if fc_id != None and id_lounge != None: #This would only occur it the API went down...
            for fc, _id in fc_id.items():
                if _id == discordIDToLoad:
                    FC = fc
                    break
        if FC == None:
            FCs = UserDataProcessing.get_all_fcs(discordIDToLoad)
            if len(FCs) > 0:
                FC = FCs[0]
    
        if FC == None:
            if len(args) == 1:
                await message.channel.send("You have not set an FC. (Use Friendbot to add your FC, then try this command later.")
            elif len(message.raw_mentions) > 0:
                lookup_name = UtilityFunctions.process_name(str(message.mentions[0].name))
                await message.channel.send(f"No FC found for {lookup_name}. Try again later.")                      
            else:
                lookup_name = UtilityFunctions.process_name(" ".join(old_command.split()[1:]))
                await message.channel.send(f"No FC found for {lookup_name}. Try again later.")                      
        else:
            await message.channel.send(FC)
      
    @staticmethod
    async def mii_command(message:discord.Message, args:List[str], old_command:str):
        if MIIS_DISABLED:
            await message.channel.send("This command is temporarily disabled.")
            return
        
        discordIDToLoad = None
        if len(args) == 1:
            discordIDToLoad = str(message.author.id)
        else:
            if len(message.raw_mentions) > 0:
                discordIDToLoad = str(message.raw_mentions[0])
            else:
                to_find_lounge = " ".join(old_command.split()[1:])
                discordIDToLoad = UserDataProcessing.get_DiscordID_By_LoungeName(to_find_lounge)
                if discordIDToLoad is None or discordIDToLoad == "":
                    discordIDToLoad = to_find_lounge
    
    
        FC = None
        if _is_fc(discordIDToLoad):
            FC = discordIDToLoad
        else:
            id_lounge, fc_id = await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad])
            await updateData(id_lounge, fc_id)
            FCs = UserDataProcessing.get_all_fcs(discordIDToLoad)
            if len(FCs) > 0:
                FC = FCs[0]
            
        if FC == None:
            if len(args) == 1:
                await message.channel.send("You have not set an FC. (Use Friendbot to add your FC, then try this command later.")
            elif len(message.raw_mentions) > 0:
                lookup_name = UtilityFunctions.process_name(str(message.mentions[0].name))
                await message.channel.send(f"No FC found for {lookup_name}, so cannot find the mii. Try again later.")                      
            else:
                lookup_name = UtilityFunctions.process_name(' '.join(old_command.split()[1:]))
                await message.channel.send(f"No FC found for {lookup_name}, so cannot find the mii. Try again later.")                      
        else:
            mii = await MiiPuller.get_mii(FC, str(message.id))
            if isinstance(mii, str):
                await message.channel.send(mii)
            else:
                try:
                    file, embed = mii.get_mii_embed()
                    await message.channel.send(file=file, embed=embed)
                finally:
                    mii.clean_up()
                    
    @staticmethod
    async def wws_command(client, this_bot:TableBot.ChannelBot, message:discord.Message, ww_type=Race.RT_WW_ROOM_TYPE):
        rlCooldown = this_bot.getRLCooldownSeconds()
        if rlCooldown > 0:
            delete_me = await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.")
            await delete_me.delete(delay=5)
        else:
            
            this_bot.updateRLCoolDown()
            sr = SimpleRooms.SimpleRooms()
            await sr.populate_rooms_information()
            rooms = []
            if ww_type == Race.RT_WW_ROOM_TYPE:
                rooms = sr.get_RT_WWs()
            elif ww_type == Race.CTGP_CTWW_ROOM_TYPE:
                rooms = sr.get_CTGP_WWs()
            elif ww_type == Race.BATTLE_ROOM_TYPE:
                rooms = sr.get_battle_WWs()
            elif ww_type == Race.UNKNOWN_ROOM_TYPE:
                rooms = sr.get_other_rooms()
            else:
                rooms = sr.get_private_rooms()
                
                
            if len(rooms) == 0:
                await message.channel.send(f"There are no {Race.Race.getWWFullName(ww_type)} rooms playing right now.")
                return
            
            def check(reaction, user):
                return user == message.author and str(reaction.emoji) in {LEFT_ARROW_EMOTE, RIGHT_ARROW_EMOTE}
        
            embed_page_start_time = datetime.now()
            sent_missing_perms_message = False
            current_page = 0
            curRoomTxt = SimpleRooms.SimpleRooms.get_embed_text_for_race(rooms, current_page)
            should_send_error_message = False
            msg = await message.channel.send(curRoomTxt)
            await msg.add_reaction(LEFT_ARROW_EMOTE)
            await msg.add_reaction(RIGHT_ARROW_EMOTE)
            while (datetime.now() - embed_page_start_time) < embed_page_time:
    
                timeout_time_delta = embed_page_time - (datetime.now() - embed_page_start_time)
                timeout_seconds = timeout_time_delta.total_seconds()
                if timeout_seconds <= 0:
                    break
    
                try:
                    reaction, user = await client.wait_for('reaction_add', timeout=timeout_seconds, check=check)
                    if(str(reaction.emoji) == LEFT_ARROW_EMOTE):
                        current_page = (current_page - 1) % (len(rooms))
                    else:
                        current_page = (current_page + 1) % (len(rooms))
    
                    curRoomTxt = SimpleRooms.SimpleRooms.get_embed_text_for_race(rooms, current_page)                
    
                    try:
                        await msg.edit(content=curRoomTxt)
                    except discord.errors.Forbidden:
                        should_send_error_message = True
                    except discord.errors.NotFound:
                        break
                    
                    if should_send_error_message:
                        send_missing_permissions(message.channel)
                        sent_missing_perms_message = True
                except asyncio.TimeoutError:
                    break
            
            try:
                await msg.clear_reaction(LEFT_ARROW_EMOTE)
                await msg.clear_reaction(RIGHT_ARROW_EMOTE)
            except discord.errors.Forbidden:
                try:
                    await msg.remove_reaction(LEFT_ARROW_EMOTE, client.user)
                    await msg.remove_reaction(RIGHT_ARROW_EMOTE, client.user)
                except:
                    pass
                if message.guild != None and not sent_missing_perms_message:
                    await send_missing_permissions(message.channel)
            except discord.errors.NotFound:
                pass
    
    @staticmethod           
    async def vr_command(this_bot:TableBot.ChannelBot, message:discord.Message, args:List[str], old_command:str):
        rlCooldown = this_bot.getRLCooldownSeconds()
        if rlCooldown > 0:
            delete_me = await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.")
            await delete_me.delete(delay=5)
            return
        
    
        this_bot.updateRLCoolDown()
        message2 = await message.channel.send("Verifying room...")
        #Case 1: No mention, get FCs for the user - this happens when len(args) = 3
        #Case 2: Mention, get FCs for the mentioned user, this happens when len(args) > 3 and len(mentions) > 1
        #Case 3: FC: No mention, len(args) > 3, and is FC
        #Case 4: rLID: No mention, len(args) > 3, is rLID
        #Case 5: Lounge name: No mention, len(args) > 3, neither rLID nor FC
        successful = False
        room_data = None
        rLID = None
        if len(args) == 1:
            discordIDToLoad = str(message.author.id)
            await updateData(* await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad]) )
            FCs = UserDataProcessing.get_all_fcs(discordIDToLoad)
            successful, room_data, last_match_str, rLID = await this_bot.verify_room([FCs])
            if not successful:
                await message.channel.send("Could not find you in a room. (This could be an error if I couldn't find your FC.)")
        elif len(args) > 1:
            if len(message.raw_mentions) > 0:
                discordIDToLoad = str(message.raw_mentions[0])
                await updateData(* await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad]))
                FCs = UserDataProcessing.get_all_fcs(discordIDToLoad)
                successful, room_data, last_match_str, rLID = await this_bot.verify_room([FCs])
                if not successful:
                    await message.channel.send(f"Could not find {UtilityFunctions.process_name(str(message.mentions[0].name))} in a room. (This could be an error if I couldn't find their FC in the database.)")                      
            elif _is_fc(args[1]):
                successful, room_data, last_match_str, rLID = await this_bot.verify_room([args[1]])
                if not successful:
                    await message.channel.send("Could not find this FC in a room.")
            else:
                await updateData( * await LoungeAPIFunctions.getByLoungeNames([" ".join(old_command.split()[1:])]))
                FCs = UserDataProcessing.getFCsByLoungeName(" ".join(old_command.split()[1:]))
                
                successful, room_data, last_match_str, rLID = await this_bot.verify_room([FCs])
                if not successful:
                    await message.channel.send(f"Could not find {UtilityFunctions.process_name(' '.join(old_command.split()[1:]))} in a room. (This could be an error if I couldn't their FC in the database.)")             
        
        if not successful or room_data == None or rLID == None:
            await message2.delete()
            return
        FC_List = [fc for fc in room_data]
        await updateData(* await LoungeAPIFunctions.getByFCs(FC_List))
    
        def get_data(data_piece):
            place = -1
            if data_piece[1][0].isnumeric():
                place = int(data_piece[1][0])
            return  place, data_piece[0], str(data_piece[1][1]), UserDataProcessing.lounge_get(data_piece[0])
        
        tuple_data = [get_data(item) for item in room_data.items()]
        tuple_data.sort()
        
        str_msg =  f"```diff\n- {last_match_str.strip()} -\n\n"
        str_msg += '+{:>3} {:<13}| {:<13}| {:<1}\n'.format("#.", "Lounge Name", "Mii Name", "FC") 
        for place, FC, mii_name, lounge_name in tuple_data:
            if lounge_name == "":
                lounge_name = "UNKNOWN"
            str_msg += "{:>4} {:<13}| {:<13}| {:<1}\n".format(str(place)+".",lounge_name, mii_name, FC)
        
        #string matching isn't the safest way here, but this is an add-on feature, and I don't want to change 
        #the verify_room function
        if "(last start" in last_match_str:
            #go get races from room
            races_str = await get_races(rLID)
            if races_str != None:
                str_msg += "\n\nRaces (Last 12): " + races_str
            else:
                str_msg += "\n\nFailed"
                
        await message.channel.send(f"{str_msg}```")
        await message2.delete()
             




"""================== Server Administrator Settings Commands ==============="""
#TODO: Refactor these - target the waterfall-like if-statements
class ServerDefaultCommands:
    """There is no point to this class, other than for organization purposes.
    This class contains all of the commands that server administrators can use to set defaults for their server"""
    @staticmethod
    async def large_time_setting_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str):
        server_id = message.guild.id
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Cannot change server default for hiding large times on tables because you're not an administrator in this server.")
        else:
            if len(args) == 1:
                await send_available_large_time_options(message, args, this_bot, server_prefix, server_wide=True)
            elif len(args) > 1:
                setting = args[1]
                if setting not in ServerFunctions.bool_map:
                    await message.channel.send(f"That is not a valid default large time setting. To see valid settings, run the command `{server_prefix}{args[0]}` and read carefully.")
                else:
                    was_success = ServerFunctions.change_default_large_time_setting(server_id, setting)
                    if was_success:
                        await message.channel.send(f"Server setting changed to:\n{get_large_time_option(setting)}")
                    else:
                        await message.channel.send("Error changing default large time setting for this server. This is TableBot's fault. Try to set it again.")
    @staticmethod              
    async def mii_setting_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str):
        server_id = message.guild.id
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Cannot change default for miis being on/off for tables for this server because you're not an administrator in this server.")
        else:
            if len(args) == 1:
                await send_available_mii_options(message, args, this_bot, server_prefix, server_wide=True)
            elif len(args) > 1:
                setting = args[1]
                if setting not in ServerFunctions.bool_map:
                    await message.channel.send(f"That is not a valid mii setting. To see valid settings, run the command `{server_prefix}{args[0]}` and read carefully.")
                else:
                    was_success = ServerFunctions.change_default_server_mii_setting(server_id, setting)
                    if was_success:
                        await message.channel.send(f"Server setting changed to:\n{get_mii_option(setting)}")
                    else:
                        await message.channel.send("Error changing mii on/off default for server. This is TableBot's fault. Try to set it again.")


    @staticmethod
    async def graph_setting_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str):
        server_id = message.guild.id
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Cannot change the default graph for tables for this server because you're not an administrator in this server.")
        else:
            if len(args) == 1:
                await send_available_graph_list(message, args, this_bot, server_prefix, server_wide=True)
            elif len(args) > 1:
                setting = args[1]
                if not this_bot.is_valid_graph(setting):
                    await message.channel.send(f"That is not a valid graph setting. To see valid settings, run the command `{server_prefix}{args[0]}` and read carefully.")
                else:
                    was_success = ServerFunctions.change_default_server_graph(server_id, setting)
                    if was_success:
                        await message.channel.send(f"Default graph for server set to: **{this_bot.get_graph_name(setting)}**")
                    else:
                        await message.channel.send("Error setting default graph for server. This is TableBot's fault. Try to set it again.")

    @staticmethod
    async def theme_setting_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str):
        server_id = message.guild.id
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Cannot change the default table theme for this server because you're not an administrator in this server.")
        else:   
            if len(args) == 1:
                await send_table_theme_list(message, args, this_bot, server_prefix, server_wide=True)
            elif len(args) > 1:
                setting = args[1]
                if not this_bot.is_valid_style(setting):
                    await message.channel.send(f"That is not a valid table theme setting. To see valid settings, run the command `{server_prefix}{args[0]}` and read carefully.")
                else:
                    was_success = ServerFunctions.change_default_server_table_theme(server_id, setting)
                    if was_success:
                        await message.channel.send(f"Default table theme for server set to: **{this_bot.get_style_name(setting)}**")
                    else:
                        await message.channel.send("Error setting default table theme for server. This is TableBot's fault. Try to set it again.")
             




"""================== Tabling Commands =================="""
#TODO: Refactor these - target the waterfall-like if-statements
class TablingCommands:
    
    #Code is quite similar to chane_player_tag_command, potential refactor opportunity?
    @staticmethod
    async def change_player_name_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, command:str):
    
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
    
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
                await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + lounge_add(players[playerNum-1][0])) + " name set to: " + UtilityFunctions.process_name(new_name))
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
                this_bot.getRoom().setNameForFC(players[_playerNum-1][0], new_name)
                await message.channel.send(UtilityFunctions.process_name(players[_playerNum-1][1] + lounge_add(players[_playerNum-1][0])) + " name set to: " + UtilityFunctions.process_name(new_name))

    @staticmethod
    async def change_player_tag_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, command:str):

        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
        

        if this_bot.getWar().is_ffa():
            to_send = "You cannot change a player's tag in an FFA. FFAs have no teams."
            await message.channel.send(to_send)
            return
        
        if len(args) == 1:
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
                    await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + lounge_add(players[playerNum-1][0])) + " tag set to: " + UtilityFunctions.process_name(new_tag))
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
                    this_bot.getWar().setTeamForFC(players[_playerNum-1][0], new_tag)
                    await message.channel.send(UtilityFunctions.process_name(players[_playerNum-1][1] + lounge_add(players[_playerNum-1][0])) + " tag set to: " + UtilityFunctions.process_name(new_tag))


    #Refactor this method to make it more readable
    @staticmethod
    async def start_war_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, command:str, permission_check:Callable):
        server_id = message.guild.id
        author_id = message.author.id
        if not is_lounge_server or permission_check(message.author) or (len(args) - command.count(" gps=") - command.count(" sui=") - command.count(" psb=")) <= 3:
            if len(args) < 3:
                #TODO: sui=yes = psb
                await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            else:
                rlCooldown = this_bot.getRLCooldownSeconds()
                if rlCooldown > 0:
                    delete_me = await message.channel.send(f"Wait {rlCooldown} more seconds before using this command.")
                    await delete_me.delete(delay=5)
                else:
                    this_bot.reset(server_id)
                    this_bot.updateRLCoolDown()
                    
                    warFormat = args[1]
                    numTeams = args[2]
                    numGPsPos, numgps = getNumGPs(args)
                    iLTPos, ignoreLargeTimes = getSuppressLargeTimes(args)
                    useMiis, _, miisPos = getUseMiis(args, True, 3)
                    if iLTPos >= 0 and 'sui=' in command:
                        await message.channel.send("*sui= will change to psb= in later updates. Use psb=yes or professionalseriesbagging=yes in the future*")
                    
                    if miisPos < 0:
                        useMiis = ServerFunctions.get_server_mii_setting(server_id)
                    if iLTPos < 0:
                        ignoreLargeTimes = ServerFunctions.get_server_large_time_setting(server_id)
                    
                    message2 = await message.channel.send("Loading room...")
                    #This is the background task for getting miis, it will be awaited once everything in ?sw finishes
                    populate_mii_task = None
                    #Case 1: No mention, get FCs for the user - this happens when len(args) = 3
                    #Case 2: Mention, get FCs for the mentioned user, this happens when len(args) > 3 and len(mentions) > 1
                    #Case 3: FC: No mention, len(args) > 3, and is FC
                    #Case 4: rLID: No mention, len(args) > 3, is rLID
                    #Case 5: Lounge name: No mention, len(args) > 3, neither rLID nor FC
                    successful = False
                    discordIDToLoad = None
                    if len(args) == 3 or (len(args) > 3 and (numGPsPos == 3 or iLTPos == 3 or miisPos == 3)):
                        discordIDToLoad = str(author_id)
                        await updateData(* await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad]) )
                        FCs = UserDataProcessing.get_all_fcs(discordIDToLoad)
                        successful = await this_bot.load_room_smart([FCs])
                        if not successful:
                            await message.channel.send("Could not find you in a room. **Did you finish the first race?**")
                    elif len(args) > 3:
                        if len(message.raw_mentions) > 0:
                            discordIDToLoad = str(message.raw_mentions[0])
                            await updateData(* await LoungeAPIFunctions.getByDiscordIDs([discordIDToLoad]))
                            FCs = UserDataProcessing.get_all_fcs(discordIDToLoad)
                            successful = await this_bot.load_room_smart([FCs])
                            if not successful:
                                lookup_name = UtilityFunctions.process_name(str(message.mentions[0].name))
                                await message.channel.send(f"Could not find {lookup_name} in a room. **Did they finish the first race?**")                      
                        elif _is_rLID(args[3]):
                            successful = await this_bot.load_room_smart([args[3]])
                            if not successful:
                                await message.channel.send("Could not find this rxx number. Is the room over 24 hours old?")                                            
                        elif _is_fc(args[3]):
                            successful = await this_bot.load_room_smart([args[3]])
                            if not successful:
                                await message.channel.send("Could not find this FC in a room. **Did they finish the first race?**")
                        else:
                            their_name = ""
                            for arg in command.split()[3:]:
                                if '=' in arg:
                                    break
                                their_name += arg + " "
                            their_name = their_name.strip()
                            await updateData( * await LoungeAPIFunctions.getByLoungeNames([their_name]))
                            FCs = UserDataProcessing.getFCsByLoungeName(their_name)
                            successful = await this_bot.load_room_smart([FCs])
                            if not successful:
                                processed_lookup_name = UtilityFunctions.process_name(their_name)
                                await message.channel.send(f"Could not find {processed_lookup_name} in a room. **Did they finish the first race?**")                      
                    if successful:
                        this_bot.freeLock()
                        this_bot.getRoom().setSetupUser(author_id,  message.author.display_name)
                        try:
                            this_bot.setWar(War.War(warFormat, numTeams, numgps, ignoreLargeTimes=ignoreLargeTimes, displayMiis=useMiis))
                        except TableBotExceptions.InvalidWarFormatException:
                            this_bot.setWar(None)
                            await message.channel.send("War format was incorrect. Valid options: FFA, 1v1, 2v2, 3v3, 4v4, 5v5, 6v6. War not created.")
                        except TableBotExceptions.InvalidNumberOfPlayersException:
                            this_bot.setWar(None)
                            await message.channel.send("Too many players based on the teams and war format. War not created.")
                        else:  
                        
                            if this_bot.getWar() != None:
                                populate_mii_task = asyncio.get_event_loop().create_task(this_bot.populate_miis(str(message.id)))
                                players = list(this_bot.getRoom().getFCPlayerListStartEnd(1, numgps*4).items())
                                player_fcs_tags, hasANoneTag = getTagsSmart(players, this_bot.getWar().playersPerTeam)
                                if hasANoneTag:
                                    player_fcs_tags = {}
                                    for fc_player in players:
                                        player_fcs_tags[fc_player] = getTagSmart(fc_player[1])
                                
                                #sort the fcs_tags by their tag
                                player_fcs_tags = sorted(player_fcs_tags.items(), key=lambda x: x[1])
                                if this_bot.getWar().formatting.lower() != "1v1" and this_bot.getWar().formatting.lower() != "ffa":
                                    teamTag = None
                                    to_print = ""
                                    previous_tags = []
                                    tag_counter = 0
                                    FC_List = [fc for fc, _ in players]
                                    await updateData(* await LoungeAPIFunctions.getByFCs(FC_List))
                                    for playerNum, ((fc, playerName), (_, playerTag)) in enumerate(player_fcs_tags):
                                        if len(playerTag.strip()) < 1:
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
                                            if playerTag == None:
                                                teamTag = f"**Team #{playerNum+1}\n**"
                                            cur_processed_team_tag = UtilityFunctions.process_name(teamTag)
                                            to_print += f"**Tag: {cur_processed_team_tag}** \n"
                                        temp_name = f"\t{playerNum+1}. {playerName}"
                                        if fc in UserDataProcessing.FC_DiscordID:
                                            DID = UserDataProcessing.FC_DiscordID[fc][0]
                                            if DID in UserDataProcessing.discordID_Lounges:
                                                lounge_name = UserDataProcessing.discordID_Lounges[DID]
                                                temp_name += f" - ({lounge_name})"
                                        
                                        to_print += UtilityFunctions.process_name(temp_name) + "\n"
                                        
                                    to_print += "\n***Is this correct?** (" + server_prefix + "yes or " + server_prefix + "no)*"
                                    
                                    await message.channel.send(to_print)
                                    this_bot.prev_command_sw = True
    
                                else:
                                    dummy_teams = {}
                                    
                                    for teamNumber in range(0, min(this_bot.getWar().numberOfTeams, len(players))):
                                        dummy_teams[players[teamNumber][0]] = str(teamNumber)
                                    this_bot.getWar().setTeams(dummy_teams)
                                    ffa_loaded_str = "FFA started. rxx: "
                                    if len(this_bot.getRoom().rLIDs) == 1:
                                        ffa_loaded_str += str(this_bot.getRoom().rLIDs[0])
                                    else:
                                        ffa_loaded_str += str(this_bot.getRoom().rLIDs)
                                        
                                    await message.channel.send(ffa_loaded_str)
                                
                                this_bot.setShouldSendNotification(True)
                    else:
                        this_bot.setWar(None)
                        this_bot.setRoom(None)
                    
                    await message2.delete()
                    if populate_mii_task is not None:
                        await populate_mii_task
        else:
            await message.channel.send(f"You can only load a room for yourself in Lounge. Do this instead: `{server_prefix}{args[0]} {args[1]} {args[2]}`")
     
    @staticmethod                  
    async def merge_room_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        if not this_bot.table_is_set() or not this_bot.getRoom().is_initialized():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return                  
    
        await message.channel.send("Feature under development. Please use with extreme caution.")
        if len(args) < 2:
            await message.channel.send("Nothing given to mergeroom. No merges nor changes made.") 
            return
        if _is_rLID(args[1]) and args[0] in this_bot.getRoom().rLIDs:
            await message.channel.send("The rLID you gave is already merged for this room. You can't merge a room with itself.") 
            return
    
        roomLink, rLID, rLIDSoup = await WiimfiSiteFunctions.getRoomDataSmart(args[1])
        rLIDSoupWasNone = rLIDSoup is None
        if not rLIDSoupWasNone:
            rLIDSoup.decompose()
            del rLIDSoup
            
        if roomLink is None or rLID is None or rLIDSoupWasNone:
            await message.channel.send("Either the FC given to mergeroom isn't in a room, or the rLID given to mergeroom doesn't exist. No merges nor changes made. **Make sure the new room has finished the first race before using this command.**") 
            return
        
        if rLID in this_bot.getRoom().rLIDs:
            await message.channel.send("The room you are currently in has already been merge in this war. No changes made.")  
            return
    
        this_bot.add_save_state(message.content)
        this_bot.getRoom().rLIDs.insert(0, rLID)
        updated = await this_bot.update_room()
        if updated:
            await message.channel.send("Rooms successfully merge. Number of races played: " + str(len(this_bot.getRoom().races)))
        else:
            this_bot.setWar(None)
            this_bot.setRoom(None)
            await message.channel.send("**Failed to merge. War has been stopped and room has unloaded**") 
    
    @staticmethod
    async def table_theme_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        if not this_bot.table_is_set() or not this_bot.getRoom().is_initialized():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
    
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
        if not this_bot.table_is_set() or not this_bot.getRoom().is_initialized():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
        else:
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
        if not this_bot.table_is_set() or not this_bot.getRoom().is_initialized():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
    
        players = list(this_bot.getRoom().getFCPlayerListStartEnd(1, len(this_bot.getRoom().races)).items())
        FC_List = [fc for fc, _ in players]
        await updateData(* await LoungeAPIFunctions.getByFCs(FC_List))
        await message.channel.send(this_bot.getRoom().get_players_list_string())
    
    @staticmethod
    async def set_war_name_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, old_command:str):
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
        elif len(args) < 2:
            await message.channel.send("No war name given. War name not set.") 
        else:
            this_bot.add_save_state(message.content)
            this_bot.getWar().setWarName(old_command[len(server_prefix)+len("setwarname"):].strip())
            await message.channel.send("War name set!")  
            
    @staticmethod
    async def undo_command(message:discord.Message, this_bot:ChannelBot, server_prefix:str, is_lounge_server:bool):   
        if not this_bot.table_is_set() or not this_bot.getRoom().is_initialized():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
    
        undone_command = this_bot.restore_last_save_state()
        if undone_command is False:
            await message.channel.send("There is nothing to undo.")
            return
        
        await message.channel.send(f"The following command has been undone: {UtilityFunctions.process_name(undone_command)}\nRun {server_prefix}wp to make sure table bot is fully refreshed.")
    
    @staticmethod
    async def early_dc_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool): 
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
    
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
        
        if roomSize == None:
            roomSize = this_bot.getWar().get_num_players()
        
        this_bot.add_save_state(message.content)
        this_bot.getRoom().forceRoomSize(raceNum, roomSize)
        await message.channel.send("Changed room size to " + str(roomSize) + " players for race #" + str(raceNum) + ".")      
    
    @staticmethod
    async def change_room_size_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
    
    
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
            await message.channel.send("Changed room size to " + str(roomSize) + " players for race #" + str(raceNum) + ".")      
    
    @staticmethod
    async def race_results_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
        else: 
            await updateData(* await LoungeAPIFunctions.getByFCs(this_bot.getRoom().getFCs()))
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
    async def war_picture_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        server_id = message.guild.id
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)                   
        else:
            populate_mii_task = asyncio.get_event_loop().create_task(this_bot.populate_miis(str(message.id)))
        
            should_send_notification = this_bot.shouldSendNoticiation()
            wpCooldown = this_bot.getWPCooldownSeconds()
            if wpCooldown > 0:
                delete_me = await message.channel.send("Wait " + str(wpCooldown) + " more seconds before using this command.")
                await delete_me.delete(delay=5)
            else:
                
                this_bot.updateWPCoolDown()
                message2 = await message.channel.send("Updating room...")
                players = list(this_bot.getRoom().getFCPlayerListStartEnd(1, this_bot.getWar().numberOfGPs*4).items())
                FC_List = [fc for fc, _ in players]
                
                await updateData(* await LoungeAPIFunctions.getByFCs(FC_List))
                
                updated = await this_bot.update_room()
                if not updated:
                    await message2.edit(content="Room not updated. Please do " + server_prefix + "sw to load a different room.")
                else:
                    await message2.edit(content=str("Room updated. Room has finished " + \
                                                    str(len(this_bot.getRoom().getRaces())) +\
                                                    " races. Last race: " +\
                                                    str(this_bot.getRoom().races[-1].getTrackNameWithoutAuthor())))
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
                    if len(args) > 1 and args[1] in {'byrace', 'race'}:
                        step = 1
                    table_text, table_sorted_data = SK.get_war_table_DCS(this_bot, use_lounge_otherwise_mii=use_lounge_otherwise_mii, use_miis=usemiis, lounge_replace=lounge_replace, server_id=server_id, step=step)
                    table_text_with_style_and_graph = table_text + this_bot.get_lorenzi_style_and_graph(prepend_newline=True)
                    display_url_table_text = urllib.parse.quote(table_text)
                    true_url_table_text = urllib.parse.quote(table_text_with_style_and_graph)
                    image_url = base_url_lorenzi + true_url_table_text
                    
                    table_image_path = str(message.id) + ".png"
                    image_download_success = await download_image(image_url, table_image_path)
                    try:
                        if not image_download_success:
                            await message.channel.send("Could not download table picture.")
                            await populate_mii_task
                            return
                        #did the room have *any* errors? Regardless of ignoring any type of error
                        war_had_errors = len(this_bot.getWar().get_all_war_errors_players(this_bot.getRoom(), False)) > 0
                        tableWasEdited = len(this_bot.getWar().manualEdits) > 0 or len(this_bot.getRoom().dc_on_or_before) > 0 or len(this_bot.getRoom().forcedRoomSize) > 0 or this_bot.getRoom().had_positions_changed() or len(this_bot.getRoom().get_removed_races_string()) > 0
                        header_combine_success = ImageCombine.add_autotable_header(errors=war_had_errors, table_image_path=table_image_path, out_image_path=table_image_path, edits=tableWasEdited)
                        footer_combine_success = True
            
                        if header_combine_success and this_bot.getWar().displayMiis:
                            footer_combine_success = ImageCombine.add_miis_to_table(this_bot, table_sorted_data, table_image_path=table_image_path, out_image_path=table_image_path)
                        if not header_combine_success or not footer_combine_success:
                            await message3.delete() 
                            await message.channel.send("Internal server error when combining images. Sorry, please notify BadWolf immediately.")  
                        else:
                            embed = discord.Embed(
                                title = "",
                                description="[Edit this table on Lorenzi's website](" + base_url_edit_table_lorenzi + display_url_table_text + ")",
                                colour = discord.Colour.dark_blue()
                            )
                            
                            file = discord.File(table_image_path, filename=table_image_path)
                            numRaces = 0
                            if this_bot.getRoom() != None and this_bot.getRoom().races != None:
                                numRaces = min( (len(this_bot.getRoom().races), this_bot.getRoom().getNumberOfGPS()*4) )
                            embed.set_author(name=this_bot.getWar().getWarName(numRaces), icon_url="https://64.media.tumblr.com/b0df9696b2c8388dba41ad9724db69a4/tumblr_mh1nebDwp31rsjd4ho1_500.jpg")
                            embed.set_image(url="attachment://" + table_image_path)
                            
                            temp = this_bot.getWar().get_war_errors_string_2(this_bot.getRoom(), lounge_replace)
                            error_message = "\n\nMore errors occurred. Embed only allows so many errors to display."
                            if len(temp) + len(error_message) >= 2048:
                                temp = temp[:2048-len(error_message)] + error_message
                            embed.set_footer(text=temp)
                            await message.channel.send(file=file, embed=embed)
                            await message3.delete()
                            if should_send_notification and current_notification != "":
                                await message.channel.send(current_notification)
                    finally:
                        if os.path.exists(table_image_path):
                            os.remove(table_image_path)
            await populate_mii_task
    
    @staticmethod
    async def table_text_command(message:discord.Message, this_bot:ChannelBot, server_prefix:str, is_lounge_server:bool):
        server_id = message.guild.id
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
        else:
            try:
                table_text, _ = SK.get_war_table_DCS(this_bot, use_lounge_otherwise_mii=True, use_miis=False, lounge_replace=True, server_id=server_id, discord_escape=True)
                await message.channel.send(table_text)
            except AttributeError:
                await message.channel.send("Table Bot has a bug, and this mkwx room triggered it. I cannot tally your scores.")
                await message.channel.send("rLID is " + str(this_bot.getRoom().rLIDs) )
                raise        
            
    @staticmethod
    async def manual_war_setup(message:discord.Message, this_bot:ChannelBot, command:str):
        this_bot.manualWarSetUp = False
        
        if this_bot.getRoom() == None or not this_bot.getRoom().is_initialized():
            await message.channel.send("Unexpected error. Somehow, there is no room loaded. Recommend the command: reset")
            this_bot.setWar(None)
            return
    
        numGPS = this_bot.getWar().numberOfGPs
        
        players = list(this_bot.getRoom().getFCPlayerListStartEnd(1, numGPS*4).items())
        player_fcs_tags, hasANoneTag = getTagsSmart(players, this_bot.getWar().playersPerTeam)
        if hasANoneTag:
            player_fcs_tags = {}
            for fc_player in players:
                player_fcs_tags[fc_player] = getTagSmart(fc_player[1])
    
        #sort the fcs_tags by their tag
        player_fcs_tags = sorted(player_fcs_tags.items(), key=lambda x: x[1])
    
        fc_tag = {} #FC is the key, and tag is the value
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
            fc_tag[fc] = teamTag
    
    
        teamBlob = command.split("/")
        
        
        for team in teamBlob:
            teamArgs = team.split()
            if len(teamArgs) < 2:
                await message.channel.send("Each team should have at least 1 player...")
                this_bot.setWar(None)
                return
            
            teamTag = teamArgs[0]
            for pos in teamArgs[1:]:
                if not pos.isnumeric():
                    processed_team_name = UtilityFunctions.process_name(str(teamTag))
                    userinput_team_position = UtilityFunctions.process_name(str(pos))
                    await message.channel.send(f"On team {processed_team_name}, {userinput_team_position} isn't a number. War stopped.")
                    this_bot.setWar(None)
                    return
                if int(pos) <= len(player_fcs_tags) and int(pos) >= 1:
                    fc_tag[player_fcs_tags[int(pos)-1][0][0]] = teamTag
             
                
        else:
            this_bot.getWar().setTeams(fc_tag)
            started_war_str = "Started war."
            if this_bot.getWar().ignoreLargeTimes:
                started_war_str += " (Ignoring errors for large finish times)"
                
            started_war_str += " rxx: "
            if len(this_bot.getRoom().rLIDs) == 1:
                started_war_str += str(this_bot.getRoom().rLIDs[0])
            else:
                started_war_str += str(this_bot.getRoom().rLIDs)
            await message.channel.send(started_war_str)
    
    @staticmethod
    async def remove_race_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
    
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
    
        await message.channel.send("Feature under development. Please use with caution as it may have unintended side effects on your table.")
        command, save_state = this_bot.get_save_state(message.content)
        success, removed_race = this_bot.getRoom().remove_race(raceNum-1)
        if not success:
            await message.channel.send("Removing this race failed. (I did say it was under development!)")
        else:
            this_bot.add_save_state(command, save_state)
            await message.channel.send(f"Removed race #{removed_race[0]+1}: {removed_race[1]}")
    
    @staticmethod     
    async def gp_display_size_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool):
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
            return
    
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
    async def quick_edit_command(message:discord.Message, this_bot:ChannelBot, args:List[str], server_prefix:str, is_lounge_server:bool, command:str):
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server)
        else:
            if len(args) == 1:
                to_send = this_bot.getRoom().get_sorted_player_list_string()
                to_send += "\n**To change the placement of the 8th player on the list for the 7th race to 4th place, do:** *" + server_prefix + "quickedit 8 7 4*"
                await message.channel.send(to_send)
            elif len(args) == 4:
                playerNum = command.split()[1].strip()
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
                            
                            
                        if _playerNum == None:
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
                                this_bot.getRoom().races[raceNum-1].changePlacement(playerFC, placement)
                                await message.channel.send("Changed " + UtilityFunctions.process_name(players[playerNum-1][1] + lounge_add(players[playerNum-1][0]) + " place to " + str(placement) + " for race #" + str(raceNum) + "."))
                            else:
                                await message.channel.send(UtilityFunctions.process_name(players[playerNum-1][1] + lounge_add(players[playerNum-1][0]) + " is not in race #" + str(raceNum)))           
                                
            else:
                await message.channel.send("Do " + server_prefix + "quickedit to learn how to use this command.")        
    
    @staticmethod
    async def current_room_command(message:discord.Message, this_bot:ChannelBot, server_prefix:str, is_lounge_server:bool):
        if not this_bot.table_is_set():
            await sendRoomWarNotLoaded(message, server_prefix, is_lounge_server) 
        elif len(this_bot.getRoom().races) >= 1:
            await updateData(* await LoungeAPIFunctions.getByFCs(this_bot.getRoom().getFCs()))
            await message.channel.send(this_bot.getRoom().races[-1].getPlayersByPlaceInRoomString())





#============== Helper functions ================
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
    if option_number == "1" or option_number == 1:
        return "**Show large times** by default for tables in this server."
    elif option_number == "2" or option_number == 2:
        return "**Hide large times** by default for tables in this server."
    return "Unknown Option"

async def send_available_mii_options(message:discord.Message, args:List[str], this_bot:TableBot.ChannelBot, server_prefix:str, server_wide=False):
    to_send = f"Choose an option from this list and do `{server_prefix}{args[0]} <optionNumber>`:\n"
    to_send += f"""`1.` {get_mii_option(1)}
`2.` {get_mii_option(2)}"""
    return await message.channel.send(to_send)

async def send_available_large_time_options(message:discord.Message, args:List[str], this_bot:TableBot.ChannelBot, server_prefix:str, server_wide=False):
    to_send = f"Choose an option from this list and do `{server_prefix}{args[0]} <optionNumber>`:\n"
    to_send += f"""`1.` {get_large_time_option(1)}
`2.` {get_large_time_option(2)}"""
    return await message.channel.send(to_send)


def dump_vr_is_on():
    with open(VR_IS_ON_FILE, "wb") as pickle_out:
        try:
            pkl.dump(vr_is_on, pickle_out)
        except:
            print("Could not dump pickle for vr_is_on. Current state:", vr_is_on)
            
def load_vr_is_on():
    global vr_is_on
    if os.path.exists(VR_IS_ON_FILE):
        with open(VR_IS_ON_FILE, "rb") as pickle_in:
            try:
                vr_is_on = pkl.load(pickle_in)
            except:
                print(f"Could not read in '{VR_IS_ON_FILE}'")
                