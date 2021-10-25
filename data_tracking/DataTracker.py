'''
Created on Oct 21, 2021

@author: willg

This module helps track and store data from Wiimmfi.

'''
import common
from collections import defaultdict
from datetime import datetime, timedelta
import Race as TableBotRace
from typing import List
import UtilityFunctions

#dict of channel IDs to tier numbers
RT_NAME = "rt"
CT_NAME = "ct"
RXX_LOCKER_NAME = "rxx_locker"
RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS = {
    843981870751678484:8,
    836652527432499260:7,
    747290199242965062:6,
    747290182096650332:5,
    873721400056238160:5,
    747290167391551509:4,
    801620685826818078:4,
    747290151016857622:3,
    801620818965954580:3,
    805860420224942080:3,
    747290132675166330:2,
    754104414335139940:2,
    801630085823725568:2,
    747289647003992078:1,
    747544598968270868:1,
    781249043623182406:1
    }

CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS = {
    875532532383363072:7,
    850520560424714240:6,
    801625226064166922:5,
    747290436275535913:4,
    879429019546812466:4,
    747290415404810250:3,
    747290383297282156:2,
    823014979279519774:2,
    747290363433320539:1,
    871442059599429632:1
    }

RT_REVERSE_TIER_MAPPINGS = defaultdict(set)
CT_REVERSE_TIER_MAPPINGS = defaultdict(set)
ALREADY_ADDED_ERROR = 11
FATAL_ERROR = 12
for k,v in RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS.items():
    RT_REVERSE_TIER_MAPPINGS[v].add(k)
for k,v in CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS.items():
    CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS[v].add(k)
TABLE_BOT_CHANNEL_TIER_MAPPINGS = {RT_NAME:RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS, CT_NAME:CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS}

room_data = {RT_NAME:{},
             CT_NAME:{},
             RXX_LOCKER_NAME:{}
             }
#Need rxx -> [channel_id:channel_data:default_dict, room_data]

from collections import namedtuple
Place = namedtuple('Place', ['fc', 'name', 'place', 'time', 'lagStart', 'playerURL', 'pid', 'ol_status', 'roomPosition', 'roomType', 'connectionFails', 'role', 'vr', 'character', 'vehicle', 'discord_name', 'lounge_name', 'mii_hex'])
Race = namedtuple('Race', ['timeAdded', 'tier', 'matchTime', 'id', 'raceNumber', 'roomID', 'rxx', 'trackURL', 'roomType', 'trackName', 'cc', 'placements', 'region', 'is_ct'])
Event = namedtuple('Event', ['races', 'name_changes', 'removed_races', 'placement_history', 'forcedRoomSize', 'playerPenalties', 'dc_on_or_before', 'set_up_user', 'sub_ins', 'playersPerTeam', 'numberOfTeams', 'defaultRoomSize', 'numberOfGPs', 'eventName', 'missingRacePts', 'manualEdits', 'ignoreLargeTimes', 'teamPenalties', 'forcedRoomSize', 'teams', 'miis'])

LOCK_OBTAINED = 0
NO_LOCK = 1
LOCK_IN_USE = 2
def obtain_rxx_lock(rxx):
    create_rxx_lock_if_needed()
    if rxx in room_data[RXX_LOCKER_NAME]:
        if not room_data[RXX_LOCKER_NAME][rxx][0]:
            room_data[RXX_LOCKER_NAME][rxx][0] = True
            room_data[RXX_LOCKER_NAME][rxx][1] = datetime.now()
            return LOCK_OBTAINED
        else:
            return LOCK_IN_USE
    else:
        return NO_LOCK
    
def create_rxx_lock_if_needed(rxx):
    if rxx in room_data[RXX_LOCKER_NAME]:
        return
    room_data[RXX_LOCKER_NAME][rxx] = [False, datetime.now()]

def release_rxx_lock(rxx):
    room_data[RXX_LOCKER_NAME][rxx][0] = False

def free_old_locks():
    MAX_LOCK_TIME = timedelta(seconds=15)
    for rxx_lock in room_data[RXX_LOCKER_NAME].values():
        cur_time = datetime.now()
        if rxx_lock[0] and (cur_time - MAX_LOCK_TIME) > rxx_lock[1]: #Assume we locked and didn't release somehow
            rxx_lock[0] = False
            

class RoomTracker(object):
    
    @staticmethod
    def new_channel_data(channel_id):
        lounge_tier = None
        if channel_id in RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS:
            lounge_tier = RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS[channel_id]
        if channel_id in CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS:
            lounge_tier = CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS[channel_id]
        #channelid, first command time, last command time, total commands sent, tier
        return [channel_id, datetime.now(), datetime.now(), 0, lounge_tier]
    
    @staticmethod
    def create_channel_data(channel_id, is_ct):
        return RoomTracker.new_channel_data(channel_id, is_ct)
    
    @staticmethod
    def check_create_channel_data(channel_id, rxx, rxx_dict, channel_bot):
        if rxx not in rxx_dict:
            rxx_dict[rxx] = {}
        if channel_id not in rxx_dict[rxx]:
            rxx_dict[rxx][channel_id] = [RoomTracker.new_channel_data(channel_id), []]
    
    @staticmethod
    def create_placement(placement:TableBotRace.Placement) -> Place:
        pass
    
    @staticmethod
    def create_race(race:TableBotRace.Race) -> Race:
        pass
    
    @staticmethod
    def create_event(channel_bot) -> Event:
        event = Event()
    
    @staticmethod
    def add_race(channel_data_info, race:TableBotRace.Race):
        _, race_data = channel_data_info
        for r in race_data:
            if r.rxx != race_data.rxx:
                common.log_error(f"rxx's didn't match in add_race:\n{race_data}\n{r}")
                return FATAL_ERROR
            if r.id == race.raceID:
                return ALREADY_ADDED_ERROR
        lock_status = obtain_rxx_lock(race.rxx)
        if lock_status != LOCK_OBTAINED: #in use
            return
        
        race_data.append()
        
        """
        {"r3560913":[internal_date_time_added,
             is_rt,
             tier,
             Room(roomID,
                  "r3560913",
                  [Race(track_name,
                        date_and_time_of_race,
                        roomID,
                        "r3560913",
                        cc,
                        [Placement(finish_time,
                                   lag_start,
                                   Player(FC,
                                          mii_name
                                         ),
                                   character,
                                   vehicle
                                   )
                        ]
                       )
                   ]
             ]
  ...
}```"""
        
    
    @staticmethod
    def update_channel_meta_data(channel_data_info):
        channel_meta_data, _ = channel_data_info
        channel_meta_data[2] = datetime.now()
        channel_meta_data[3] += 1
        
    @staticmethod
    def add_races(channel_id, channel_bot):
        races:List[TableBotRace.Race] = channel_bot.getRoom().getRaces()
        update_channel_data = True
        for race in races:
            if race.rxx is None or not UtilityFunctions.is_rLID(race.rxx):
                common.log_error(f"No rxx for this race: {race}")
                continue
            rxx_dict = room_data[CT_NAME] if race.isCustomTrack() else room_data[RT_NAME]
            RoomTracker.check_create_channel_data(channel_id, race.rxx, rxx_dict, channel_bot)
            if update_channel_data:
                update_channel_data = False
                RoomTracker.update_channel_meta_data(rxx_dict[race.rxx][channel_id])
            
            RoomTracker.add_race(rxx_dict[race.rxx][channel_id], race)
            
    #Greedily add all races
    @staticmethod
    def add_data(channel_bot):
        free_old_locks()
        pass
        
            
















            
def dump_room_data():
    common.dump_pkl(room_data, common.ROOM_DATA_TRACKER_FILE, "Could not dump pickle room data in data tracking.", display_data_on_error=True)

def load_room_data():
    room_data.clear()
    room_data.update(common.load_pkl(common.ROOM_DATA_TRACKER_FILE, "Could not load pickle for room data in data tracking, using empty data instead.", default=dict))

def initialize():
    load_room_data()

def on_exit():
    dump_room_data()
    