'''
Created on Oct 21, 2021

@author: willg

This module helps track and store data from Wiimmfi.

'''
import common
from collections import defaultdict
from datetime import datetime
import Race
from typing import List
import UtilityFunctions

#dict of channel IDs to tier numbers
RT_NAME = "rt"
CT_NAME = "ct"
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
for k,v in RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS.items():
    RT_REVERSE_TIER_MAPPINGS[v].add(k)
for k,v in CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS.items():
    CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS[v].add(k)
TABLE_BOT_CHANNEL_TIER_MAPPINGS = {RT_NAME:RT_TABLE_BOT_CHANNEL_TIER_MAPPINGS, CT_NAME:CT_TABLE_BOT_CHANNEL_TIER_MAPPINGS}

room_data = {RT_NAME:{},
             CT_NAME:{}
             }
#Need rxx -> [channel_id:channel_data:default_dict, room_data]

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
    def check_create_channel_data(self, channel_id, rxx, rxx_dict):
        if rxx not in rxx_dict:
            rxx_dict[rxx] = {}
        if channel_id not in rxx_dict[rxx]:
            rxx_dict[rxx][channel_id] = [RoomTracker.new_channel_data(channel_id), []]
    @staticmethod
    def add_race(channel_data_info, race:Race.Race):
        _, race_data = channel_data_info
        
    
    @staticmethod
    def update_channel_meta_data(channel_data_info):
        channel_meta_data, _ = channel_data_info
        channel_meta_data[2] = datetime.now()
        channel_meta_data[3] += 1
        
    @staticmethod
    def add_races(channel_id, channel_bot):
        races:List[Race.Race] = channel_bot.getRoom().getRaces()
        update_channel_data = True
        for race in races:
            if race.rxx is None or not UtilityFunctions.is_rLID(race.rxx):
                common.log_error(f"No rxx for this race: {race}")
                continue
            rxx_dict = room_data[CT_NAME] if race.isCustomTrack() else room_data[RT_NAME]
            RoomTracker.check_create_channel_data(channel_id, race.rxx, rxx_dict)
            if update_channel_data:
                update_channel_data = False
                RoomTracker.update_channel_meta_data(rxx_dict[race.rxx][channel_id])
            
            RoomTracker.add_race(rxx_dict[race.rxx][channel_id], race)
            
    #Greedily add all races
    @staticmethod
    def add_data(channel_bot):
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
    