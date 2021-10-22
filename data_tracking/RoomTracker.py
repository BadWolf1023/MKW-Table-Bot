'''
Created on Oct 21, 2021

@author: willg

This module helps track and store data from Wiimmfi.

'''
import common
#dict of channel IDs to tier numbers
TABLE_BOT_CHANNEL_TIER_MAPPINGS = {}

room_data = {}
















            
def dump_room_data():
    common.dump_pkl(room_data, common.ROOM_DATA_TRACKER_FILE, "Could not dump pickle room data in data tracking.", display_data_on_error=True)

def load_room_data():
    room_data.clear()
    room_data.update(common.load_pkl(common.ROOM_DATA_TRACKER_FILE, "Could not load pickle for room data in data tracking, using empty data instead.", default=dict))

def initialize():
    load_room_data()

def on_exit():
    dump_room_data()
    