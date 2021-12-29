'''
Created on Jul 25, 2020

@author: willg
'''
#DN = Discord Name
import asyncio
import os
from typing import Dict, Tuple
import common
from datetime import datetime, timedelta

from data_tracking import DataTracker

seperator = "="


FC_discord_id_file_is_open = False
discord_id_lounges_file_is_open = False
discordID_flags_file_is_open = False

FC_DiscordID = {}
discordID_Lounges = {}
discordID_Flags = {}
blacklisted_Users = {}

valid_flag_codes = set()


to_add_lounge = {}
to_add_fc = {}


#datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
DEFAULT_LAST_USED_DATE = datetime(year=2020,month=8,day=1, hour=1, minute=0, second=0, microsecond=1)

def lounge_add(fc, lounge_replace=True):
    if lounge_replace:
        fc_did = FC_DiscordID
        did_lounge = discordID_Lounges
        if fc in fc_did and fc_did[fc][0] in did_lounge:
            return " - (" + did_lounge[fc_did[fc][0]] + ")"
    return ""

def lounge_get(fc, lounge_replace=True):
    if lounge_replace:
        fc_did = FC_DiscordID
        did_lounge = discordID_Lounges
        if fc in fc_did and fc_did[fc][0] in did_lounge:
            return did_lounge[fc_did[fc][0]]
    return ""


def read_Blacklisted_file(filename=common.BLACKLISTED_USERS_FILE):
    common.check_create(filename)
    temp = {}
    with open(filename, "r", encoding="utf-8", errors="replace" ) as f:
        for line in f:
            DID, reason = line.split(seperator)
            temp[str(DID)] = reason.strip()
    return temp

def add_Blacklisted_user(discord_id, reason):
    global blacklisted_Users
    discord_id = str(discord_id)
    if discord_id in blacklisted_Users:
        del blacklisted_Users[discord_id]
        
        temp_file_name = f"{common.BLACKLISTED_USERS_FILE}_temp"
        with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.BLACKLISTED_USERS_FILE, "r", encoding="utf-8", errors="replace") as original:
            for line in original:
                if line.strip("\n").split(seperator)[0] != discord_id:
                    temp_out.write(line)
        
            if reason not in ["unban", "remove", "unblacklist", ""]:
                temp_out.write(discord_id + seperator + reason + "\n")
                blacklisted_Users[discord_id] = reason
                    
        os.remove(common.BLACKLISTED_USERS_FILE)
        os.rename(temp_file_name, common.BLACKLISTED_USERS_FILE)
    else:
        if reason not in ["unban", "remove", "unblacklist", ""]:
            with open(common.BLACKLISTED_USERS_FILE, "a", encoding="utf-8", errors="replace") as f:
                f.write(str(discord_id) + seperator + reason + "\n")
                blacklisted_Users[discord_id] = reason
    
    return True

   
def read_DiscordID_Flags_file(filename=common.DISCORD_ID_FLAGS_FILE):
    common.check_create(filename)
    temp = {}
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            DID, flag = line.split(seperator)
            temp[DID] = flag.strip()
    return temp

def add_flag(discord_id, flag):
    global discordID_flags_file_is_open
    
    discord_id = str(discord_id)
    if discordID_flags_file_is_open:
        return False
    else:
        discordID_flags_file_is_open = True
        
        #If their discord ID already has a flag.... go remove their flag, then add it
        if discord_id in discordID_Flags:
            del discordID_Flags[discord_id]
            
            temp_file_name = f"{common.DISCORD_ID_FLAGS_FILE}_temp"
            with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.DISCORD_ID_FLAGS_FILE, "r", encoding="utf-8", errors="replace") as original:
                for line in original:
                    if line.strip("\n").split(seperator)[0] != discord_id:
                        temp_out.write(line)
            
                if flag not in ["none", ""]:
                    temp_out.write(discord_id + seperator + flag + "\n")
                    discordID_Flags[discord_id] = flag
                        
            os.remove(common.DISCORD_ID_FLAGS_FILE)
            os.rename(temp_file_name, common.DISCORD_ID_FLAGS_FILE)
        else:
            if flag not in ["none", ""]:
                with open(common.DISCORD_ID_FLAGS_FILE, "a", encoding="utf-8", errors="replace") as f:
                    f.write(str(discord_id) + seperator + flag + "\n")
                    discordID_Flags[discord_id] = flag
        
        discordID_flags_file_is_open = False
        return True
     
def get_flag(discord_id):
    discord_id = str(discord_id)
    global discordID_Flags
    
    if discord_id in discordID_Flags:
        return discordID_Flags[discord_id]
    return None
    
def flag_exception(discord_id, add=True):
    common.check_create(common.FLAG_EXCEPTION_FILE)
    discord_id = str(discord_id)
    temp_file_name = f"{common.FLAG_EXCEPTION_FILE}_temp"
    with open(temp_file_name, "w+", encoding="utf-8", errors="replace") as temp_out, open(common.FLAG_EXCEPTION_FILE, "r+", encoding="utf-8", errors="replace") as original:
        for line in original:
            if line.strip("\n").split(seperator)[0] != discord_id:
                temp_out.write(line)
        if add:
            temp_out.write(str(discord_id) + "\n")
                
    os.remove(common.FLAG_EXCEPTION_FILE)
    os.rename(temp_file_name, common.FLAG_EXCEPTION_FILE)
   
    return True

def read_flag_exceptions():
    common.check_create(common.FLAG_EXCEPTION_FILE)
    flag_exceptions = set()
    with open(common.FLAG_EXCEPTION_FILE, "r+", encoding="utf-8", errors="replace") as original:
        for line in original:
            line = line.strip('\n').strip()
            if line.isnumeric():
                flag_exceptions.add(int(line))
    return flag_exceptions
 

def read_DiscordID_Lounges_file(filename=common.DISCORD_ID_LOUNGES_FILE):
    common.check_create(filename)
    temp = {}
    counter = 1
    with open(filename, "r", encoding="utf-8", errors="replace" ) as f:
        for line in f:
            counter += 1
            DID, lounge_name = line.split(seperator)
            temp[DID] = lounge_name.strip()
    return temp
 
def non_async_dump_data():
    global FC_discord_id_file_is_open
    global discord_id_lounges_file_is_open
    global FC_DiscordID
    global discordID_Lounges
    global to_add_lounge
    global to_add_fc

    
    
    if FC_discord_id_file_is_open or discord_id_lounges_file_is_open:
        return False
    else:
        FC_discord_id_file_is_open = True
        discord_id_lounges_file_is_open = True
        common.check_create(common.FC_DISCORD_ID_FILE)
        common.check_create(common.DISCORD_ID_LOUNGES_FILE)

        
        #Next, let's add all of the fc and lounge names to the file and dictionary
        temp_file_name = f"{common.DISCORD_ID_LOUNGES_FILE}_temp"
        with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.DISCORD_ID_LOUNGES_FILE, "r", encoding="utf-8", errors="replace") as original:
            for discord_id, lounge_name in discordID_Lounges.items():
                temp_out.write(discord_id + seperator + lounge_name + "\n")
                

        os.remove(common.DISCORD_ID_LOUNGES_FILE)
        os.rename(temp_file_name, common.DISCORD_ID_LOUNGES_FILE)
        
        
        
        temp_file_name = f"{common.FC_DISCORD_ID_FILE}_temp"
        with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.FC_DISCORD_ID_FILE, "r", encoding="utf-8", errors="replace") as original:
            for fc, (discord_id, last_used) in FC_DiscordID.items():
                temp_out.write(fc + seperator + discord_id + seperator + str(last_used) + "\n")
        
        os.remove(common.FC_DISCORD_ID_FILE)
        os.rename(temp_file_name, common.FC_DISCORD_ID_FILE)
        
        to_add_lounge.clear()
        to_add_fc.clear()
        
        FC_discord_id_file_is_open = False
        discord_id_lounges_file_is_open = False
        return True
    
async def dump_data():
    return non_async_dump_data()
    
def add_lounge(discord_id, lounge_name):
    global discord_id_lounges_file_is_open
    
    discord_id = str(discord_id)
    if discord_id_lounges_file_is_open:
        return False
    else:
        discord_id_lounges_file_is_open = True
        
        #If their discord ID already has a lounge name.... go remove their flag, then add it
        if discord_id in discordID_Lounges:
            del discordID_Lounges[discord_id]
            
            temp_file_name = f"{common.DISCORD_ID_LOUNGES_FILE}_temp"
            with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.DISCORD_ID_LOUNGES_FILE, "r", encoding="utf-8", errors="replace") as original:
                for line in original:
                    if line.strip("\n").split(seperator)[0] != discord_id:
                        temp_out.write(line)
            
                temp_out.write(discord_id + seperator + lounge_name + "\n")
                discordID_Lounges[discord_id] = lounge_name
                        
            os.remove(common.DISCORD_ID_LOUNGES_FILE)
            os.rename(temp_file_name, common.DISCORD_ID_LOUNGES_FILE)
        else:
            with open(common.DISCORD_ID_LOUNGES_FILE, "a", encoding="utf-8", errors="replace") as f:
                f.write(str(discord_id) + seperator + lounge_name + "\n")
                discordID_Lounges[discord_id] = lounge_name
        
        discord_id_lounges_file_is_open = False
        return True    



def get_lounge(discord_id):
    discord_id = str(discord_id)
    global discordID_Lounges   
    
    if discord_id in discordID_Lounges:
        return discordID_Lounges[discord_id]
    return None




def read_FC_DiscordID_file(filename=common.FC_DISCORD_ID_FILE):
    common.check_create(filename)
    temp = {}
    counter = 0
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            data = line.split(seperator)
            FC, DID = data[0], data[1].strip()
            offset = timedelta(seconds=counter)
            last_used = DEFAULT_LAST_USED_DATE - offset
            if len(data) == 3:
                last_used = convert_datetime_str(data[2].strip())
            else:
                counter += 1
            temp[FC] = (DID.strip(), last_used)
        
    return temp


def get_all_fcs(discord_id, FCDID=None):
    if discord_id is None:
        return []
    if FCDID is None:
        FCDID = FC_DiscordID
        
    discord_id = str(discord_id)
    FCs = []
    for fc, (dict_discord_id, last_used) in FCDID.items():
        if dict_discord_id == discord_id:
            FCs.append((fc, last_used))
            
    FCs.sort(key=lambda d:d[1], reverse=True)
    return [data[0] for data in FCs]

def get_DiscordID_By_LoungeName(lounge_name:str, DID_L=None):
    if lounge_name is None:
        return ''
    if DID_L is None:
        DID_L = discordID_Lounges
    
    lounge_name = lounge_name.lower()
    lounge_no_spaces = lounge_name.replace(" ", "")
    for discord_id, dict_lounge_name in DID_L.items():
        if dict_lounge_name.replace(" ", "").lower() == lounge_no_spaces:
            return discord_id
    return ''
        

def getFCsByLoungeName(lounge_name:str):
    if lounge_name is None:
        return []
    did = get_DiscordID_By_LoungeName(lounge_name)
    if did == '': #Couldn't look up their discord id by their lounge name
        return []
    return get_all_fcs(did)


def addIDsLounges(to_add: Dict[str,str]):
    global discordID_Lounges
    discordID_Lounges.update(to_add)
    to_add_lounge.update(to_add)
    

def addFCsIDs(to_add: Dict[str,Tuple[str,datetime]]):
    global FC_DiscordID
    FC_DiscordID.update(to_add)
    to_add_fc.update(to_add)
    asyncio.create_task(DataTracker.add_player_fcs(to_add))
    
def smartUpdate(id_lounge=None, fc_id=None):
    if id_lounge is not None:
        addIDsLounges(id_lounge)
    if fc_id is not None:
        addFCsIDs(fc_id)
        

def read_valid_flags_file(filename=common.FLAG_CODES_FILE):
    common.check_create(filename)
    flag_codes = set()
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            flag_codes.add(line.strip("\n").strip().lower())
    return flag_codes


def initialize():
    global discordID_Flags
    global discordID_Lounges
    global FC_DiscordID
    global valid_flag_codes
    global blacklisted_Users
    global tutorial_link
    discordID_Flags.clear()
    discordID_Flags.update(read_DiscordID_Flags_file())
    discordID_Lounges.clear()
    discordID_Lounges.update(read_DiscordID_Lounges_file())
    FC_DiscordID.clear()
    FC_DiscordID.update(read_FC_DiscordID_file())
    valid_flag_codes.clear()
    valid_flag_codes.update(read_valid_flags_file())
    blacklisted_Users.clear()
    blacklisted_Users.update(read_Blacklisted_file())
    
#2021-04-03 20:29:45.779373

def convert_datetime_str(datetime_str:str):
    return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')

