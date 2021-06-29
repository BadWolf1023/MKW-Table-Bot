'''
Created on Jul 12, 2020

@author: willg
'''
from UserDataProcessing import lounge_add
import UtilityFunctions

DEBUGGING = False
DISCONNECTION_TIME = (999,999,999)
BOGUS_TIME_LIMIT = (5,59,999)

class Placement(object):

    
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
    
    def is_disconnected(self):
        return self.time == DISCONNECTION_TIME
    
    def is_bogus_time(self):
        if self.is_disconnected():
            return False
        return self.time > BOGUS_TIME_LIMIT
    
    def __init__(self, player, place, time):
        self.player = player
        self.place = place
        self.time = self._createTime_(time)
        
    
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
    
    def __str__(self):
        if self.time == DISCONNECTION_TIME:
            return  str(self.place) +  ". " + UtilityFunctions.process_name(self.player.name + lounge_add(self.player.FC)) + " - " +"DISCONNECTED"
        return str(self.place) +  ". " + UtilityFunctions.process_name(self.player.name + lounge_add(self.player.FC)) + " - " + self.get_time_string() 
        
        