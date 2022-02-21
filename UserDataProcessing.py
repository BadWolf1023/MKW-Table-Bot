'''
Created on Jul 25, 2020

@author: willg
'''
#DN = Discord Name
import asyncio
import os
from collections import defaultdict
from typing import Dict, Tuple, Union
import common
from datetime import datetime, timedelta

from data_tracking import DataTracker
import UtilityFunctions as UF

seperator = "="


fc_discord_id_file_is_open = False
discordId_lounges_file_is_open = False
discordId_flags_file_is_open = False

fc_discordId = {} # Contains friend codes mapped to a Tuple[associated discord id, datetime that the friend code was last used]
discordId_fc = {} # Contains discord ids codes mapped to a Tuple[associated friend code, datetime that the friend code was last used]

discordId_lounges = {}  # Contains discord IDs mapped to the correct capitalization and spacing of their Lounge name
lounges_discordId = {}  # Contains a lookup version of someone's Lounge name mapped to their discord ID

discordId_flags = {}  # Contains discord IDs mapped to the the flag code for that user
blacklisted_users = {}

valid_flag_codes = set()

#datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
DEFAULT_LAST_USED_DATE = datetime(year=2020,month=8,day=1, hour=1, minute=0, second=0, microsecond=1)

def proccessed_lounge_add(mii_name, fc, lounge_replace=True):
    '''Stars out blacklisted words in given mii name, escapes Discord markdown, and adds the lounge name for the given FC if one is found.
    (Also escapes markdown for the lounge addition to prevent clever syntax abused)'''
    lounge_addition = UF.escape_mentions(UF.escape_markdown(lounge_add(fc, lounge_replace)))
    return f"{UF.clean_for_output(mii_name)}{lounge_addition}"

def lounge_add(fc, lounge_replace=True):
    if lounge_replace:
        fc_did = fc_discordId
        did_lounge = discordId_lounges
        if fc in fc_did and fc_did[fc][0] in did_lounge:
            return " - (" + did_lounge[fc_did[fc][0]] + ")"
    return ""

def lounge_get(fc, lounge_replace=True):
    if lounge_replace:
        fc_did = fc_discordId
        did_lounge = discordId_lounges
        if fc in fc_did and fc_did[fc][0] in did_lounge:
            return did_lounge[fc_did[fc][0]]
    return ""

def lounge_name_or_mii_name(fc, name, lounge_replace=True):
    """Return lounge name if player has one"""
    loungeName = lounge_get(fc, lounge_replace)
    if loungeName=="":
        return name
    return loungeName

def process_lounge_name(name):
    return name.lower().replace(" ","").strip()

def read_Blacklisted_file(filename=common.BLACKLISTED_USERS_FILE):
    common.check_create(filename)
    temp = {}
    with open(filename, "r", encoding="utf-8", errors="replace" ) as f:
        for line in f:
            DID, reason = line.split(seperator)
            temp[str(DID)] = reason.strip()
    return temp

def add_Blacklisted_user(discord_id, reason):
    global blacklisted_users
    discord_id = str(discord_id)
    if discord_id in blacklisted_users:
        del blacklisted_users[discord_id]
        
        temp_file_name = f"{common.BLACKLISTED_USERS_FILE}_temp"
        with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.BLACKLISTED_USERS_FILE, "r", encoding="utf-8", errors="replace") as original:
            for line in original:
                if line.strip("\n").split(seperator)[0] != discord_id:
                    temp_out.write(line)
        
            if reason not in ["unban", "remove", "unblacklist", ""]:
                temp_out.write(discord_id + seperator + reason + "\n")
                blacklisted_users[discord_id] = reason
                    
        os.remove(common.BLACKLISTED_USERS_FILE)
        os.rename(temp_file_name, common.BLACKLISTED_USERS_FILE)
    else:
        if reason not in ["unban", "remove", "unblacklist", ""]:
            with open(common.BLACKLISTED_USERS_FILE, "a", encoding="utf-8", errors="replace") as f:
                f.write(str(discord_id) + seperator + reason + "\n")
                blacklisted_users[discord_id] = reason
    
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
    global discordId_flags_file_is_open
    
    discord_id = str(discord_id)
    if discordId_flags_file_is_open:
        return False
    else:
        discordId_flags_file_is_open = True
        
        #If their discord ID already has a flag.... go remove their flag, then add it
        if discord_id in discordId_flags:
            del discordId_flags[discord_id]
            
            temp_file_name = f"{common.DISCORD_ID_FLAGS_FILE}_temp"
            with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.DISCORD_ID_FLAGS_FILE, "r", encoding="utf-8", errors="replace") as original:
                for line in original:
                    if line.strip("\n").split(seperator)[0] != discord_id:
                        temp_out.write(line)
            
                if flag not in ["none", ""]:
                    temp_out.write(discord_id + seperator + flag + "\n")
                    discordId_flags[discord_id] = flag
                        
            os.remove(common.DISCORD_ID_FLAGS_FILE)
            os.rename(temp_file_name, common.DISCORD_ID_FLAGS_FILE)
        else:
            if flag not in ["none", ""]:
                with open(common.DISCORD_ID_FLAGS_FILE, "a", encoding="utf-8", errors="replace") as f:
                    f.write(str(discord_id) + seperator + flag + "\n")
                    discordId_flags[discord_id] = flag
        
        discordId_flags_file_is_open = False
        return True
     
def get_flag(discord_id):
    if discord_id is None:
        return None
    discord_id = str(discord_id)
    if discord_id in discordId_flags:
        return discordId_flags[discord_id]
    return None
    

def read_DiscordID_Lounges_file(filename=common.DISCORD_ID_LOUNGES_FILE):
    common.check_create(filename)
    did_lounges = {}
    lounges_did = {}
    counter = 1
    with open(filename, "r", encoding="utf-8", errors="replace" ) as f:
        for line in f:
            counter += 1
            DID, lounge_name = line.split(seperator)
            did_lounges[DID] = lounge_name.strip()

            lounge_name = process_lounge_name(lounge_name)
            if lounge_name in lounges_did:
                if get_last_used_fc_time(DID) > get_last_used_fc_time(lounges_did[lounge_name]):
                    lounges_did[lounge_name] = DID
            else:
                lounges_did[lounge_name] = DID

    return did_lounges, lounges_did


def read_FC_DiscordID_file(filename=common.FC_DISCORD_ID_FILE):
    common.check_create(filename)
    fc_did = {}
    did_fc = defaultdict(list)
    counter = 0
    with open(filename,"r",encoding="utf-8",errors="replace") as f:
        for line in f:
            data = line.split(seperator)
            FC,DID = data[0],data[1].strip()
            offset = timedelta(seconds=counter)
            last_used = DEFAULT_LAST_USED_DATE - offset
            if len(data) == 3:
                last_used = convert_datetime_str(data[2].strip())
            else:
                counter += 1
            fc_did[FC] = (DID.strip(),last_used)
            did_fc[DID].append([FC,last_used])

    return fc_did,did_fc
 
def non_async_dump_data():
    global fc_discord_id_file_is_open
    global discordId_lounges_file_is_open
    global fc_discordId
    global discordId_lounges
    
    if fc_discord_id_file_is_open or discordId_lounges_file_is_open:
        return False
    else:
        fc_discord_id_file_is_open = True
        discordId_lounges_file_is_open = True
        common.check_create(common.FC_DISCORD_ID_FILE)
        common.check_create(common.DISCORD_ID_LOUNGES_FILE)

        
        #Next, let's add all of the fc and lounge names to the file and dictionary
        temp_file_name = f"{common.DISCORD_ID_LOUNGES_FILE}_temp"
        with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.DISCORD_ID_LOUNGES_FILE, "r", encoding="utf-8", errors="replace") as original:
            for discord_id, lounge_name in discordId_lounges.items():
                temp_out.write(discord_id + seperator + lounge_name + "\n")
                

        os.remove(common.DISCORD_ID_LOUNGES_FILE)
        os.rename(temp_file_name, common.DISCORD_ID_LOUNGES_FILE)
        
        
        temp_file_name = f"{common.FC_DISCORD_ID_FILE}_temp"
        with open(temp_file_name, "w", encoding="utf-8", errors="replace") as temp_out, open(common.FC_DISCORD_ID_FILE, "r", encoding="utf-8", errors="replace") as original:
            for fc, (discord_id, last_used) in fc_discordId.items():
                temp_out.write(fc + seperator + discord_id + seperator + str(last_used) + "\n")
        
        os.remove(common.FC_DISCORD_ID_FILE)
        os.rename(temp_file_name, common.FC_DISCORD_ID_FILE)
        
        fc_discord_id_file_is_open = False
        discordId_lounges_file_is_open = False
        return True
    
async def dump_data():
    return non_async_dump_data()

def get_lounge(discord_id):
    discord_id = str(discord_id)
    global discordId_lounges
    
    if discord_id in discordId_lounges:
        return discordId_lounges[discord_id]
    return None

def get_discord_id_from_fc(fc: Union[str, None]) -> Union[str, None]:
    if fc is None or fc not in fc_discordId:
        return None
    return fc_discordId[fc][0]


def get_all_fcs(discord_id, include_time=False):
    if discord_id is None:
        return []
        
    discord_id = str(discord_id)
    if discord_id not in discordId_fc:
        return []

    fcs = discordId_fc[discord_id]
    fcs.sort(key=lambda d:d[1], reverse=True)

    if include_time:
        return [data for data in fcs]
    else:
        return [data[0] for data in fcs]

def get_last_used_fc_time(discord_id):
    fc_times = get_all_fcs(discord_id, include_time=True)
    if len(fc_times) == 0:
        return datetime.min
    return max([x[1] for x in fc_times])

def get_DiscordID_By_LoungeName(lounge_name:str):
    if lounge_name is None:
        return ''

    lounge_name = process_lounge_name(lounge_name)
    if lounge_name not in lounges_discordId:
        return ''
    return lounges_discordId[lounge_name]

def getFCsByLoungeName(lounge_name:str):
    if lounge_name is None:
        return []
    did = get_DiscordID_By_LoungeName(lounge_name)
    if did == '': #Couldn't look up their discord id by their lounge name
        return []
    return get_all_fcs(did)

def addIDsLounges(to_add: Dict[str,str]):
    global discordId_lounges
    discordId_lounges.update(to_add)

    for DID, lounge_name in to_add.items():
        lounges_discordId[process_lounge_name(lounge_name)] = DID

def addFCsIDs(to_add: Dict[str,Tuple[str,datetime]]):
    global fc_discordId
    fc_discordId.update(to_add)

    for fc, pair in to_add.items():
        did, time = pair

        for pair in discordId_fc[did]:
            if pair[0] == fc:
                pair[1] = time

        if fc not in [x[0] for x in discordId_fc[did]]:
            discordId_fc[did].append([fc,time])

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
    global discordId_flags
    global discordId_lounges
    global lounges_discordId
    global fc_discordId
    global discordId_fc
    global valid_flag_codes
    global blacklisted_users

    discordId_flags.clear()
    discordId_flags.update(read_DiscordID_Flags_file())

    fc_discordId,discordId_fc = read_FC_DiscordID_file()
    discordId_lounges,lounges_discordId = read_DiscordID_Lounges_file()

    valid_flag_codes.clear()
    valid_flag_codes.update(read_valid_flags_file())
    blacklisted_users.clear()
    blacklisted_users.update(read_Blacklisted_file())
    
#2021-04-03 20:29:45.779373
def convert_datetime_str(datetime_str:str):
    return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')

