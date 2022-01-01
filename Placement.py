'''
Created on Jul 12, 2020

@author: willg
'''
import UserDataProcessing
import UtilityFunctions
import Player
import re

DEBUGGING = False
DISCONNECTION_TIME = (999,999,999)
BOGUS_TIME_LIMIT = (5,59,999)
MINIMUM_DELTA_VALUE = -10
MAXIMUM_DELTA_VALUE = 10

NO_DELTA_DISPLAY_RANGE = (-.5, .5)

def is_valid_time_str(time_str):
    return re.match("^([\d]{1,3}:)?[\d]{1,3}\.[\d]{3}$", time_str.strip()) is not None
    

class Placement:

    def _createTime_(self, time):
        temp = ""
        minute = "-1"
        second = "-1"
        millisecond = "-1"
        if DEBUGGING:
            print(time)
        if time == u'\u2014':
            return DISCONNECTION_TIME #Disconnection
        elif (":" in time):
            temp = time.split(":")
            minute = temp[0]
            temp2 = temp[1].split(".")
            second, millisecond = temp2[0], temp2[1]
        else:
            temp2 = time.split(".")
            minute = "0"
            second, millisecond = temp2[0], temp2[1]
            
        return (int(minute), int(second), int(millisecond))
    
    def _process_delta_(self, delta):
        new_delta = float(0)
        
        if delta is not None and UtilityFunctions.isfloat(delta):
            return float(delta)
        return new_delta
    
    def is_disconnected(self):
        return self.time == DISCONNECTION_TIME
    
    def is_delta_unlikely(self):
        if self.delta is None:
            return False
        return self.delta < MINIMUM_DELTA_VALUE or self.delta > MAXIMUM_DELTA_VALUE
    
    def is_bogus_time(self):
        if self.is_disconnected():
            return False
        return self.time > BOGUS_TIME_LIMIT
    
    def __init__(self, player, place, time, delta=None, is_wiimmfi_place=False):
        self.player = player
        self.place = place
        self.time = self._createTime_(time)
        self.delta = self._process_delta_(delta)
        self.is_wiimmfi_place = is_wiimmfi_place
    
    def __lt__(self, other):
        return self.time < other.time
    def __gt__(self, other):
        return self.time > other.time
    def __cmp__(self, other):
        if self.time < other.time:
            return -1
        if self.time > other.time:
            return 1
        return 0
    def __eq__(self, other):
        return self.time == other.time
    
    def get_fc_and_name(self):
        return self.player.FC, self.player.name
    
    def get_time(self):
        return self.time
    
    def get_place(self):
        return self.place
    
    def get_place_str(self):
        append = "th"
        if self.place%100 == 1:
            append = "st"
        elif self.place%100 == 2:
            append = "nd"
        elif self.place%100 == 3:
            append = "rd"
        
        return f"{self.place}{append}"
        
    def get_delta(self):
        return self.delta
    
    def getPlayer(self) -> Player.Player:
        return self.player

    def getFC(self):
        return self.player.FC
    
    def is_from_wiimmfi(self):
        return self.is_wiimmfi_place
    
    def should_display_delta(self):
        return self.delta < NO_DELTA_DISPLAY_RANGE[0] or self.delta > NO_DELTA_DISPLAY_RANGE[1]
    
    def get_time_string(self):
        minutes = str(self.time[0])
        seconds = str(self.time[1])
        if len(seconds) == 1:
            seconds = "0" + seconds
        milliseconds = str(self.time[2])
        if len(milliseconds) == 1:
            milliseconds = "00" + milliseconds
        elif len(milliseconds) == 2:
            milliseconds = "0" + milliseconds
        return minutes + ":" + seconds + "." + milliseconds

    def get_time_seconds(self):
        minutes = self.time[0]
        seconds = self.time[1]
        milliseconds = self.time[2]

        return minutes*60+seconds+milliseconds/1000
    
    def __str__(self):
        to_return = f"{self.place}. {UtilityFunctions.process_name(self.player.name + UserDataProcessing.lounge_add(self.player.FC))} - "
        if self.is_disconnected():
            to_return += "DISCONNECTED"
        else:
            to_return += self.get_time_string()
        
        if self.should_display_delta():
            to_return += f" - **{self.delta}s lag start**"
        return to_return
        
     
        