'''
Created on Oct 20, 2021

@author: willg

I don't want to make the AIs classes, so this module will be shared by all AIs for common functionality
'''
#Use the BAD_NAME_TAG constant if their name is garbage or blank (no length) or if you don't want to deal with their name
BAD_NAME_TAG = "Unknown"
#If their name is okay, but you don't know their tag, use this constant
UNKNOWN_TAG_NAME = "No Tag"
#If your AI determined that someone's tag should be Player, use this constant
PLAYER_TAG = "Player"

#Your AI must call this function if the format is FFA (or if your AI thinks the format is FFA)
#Give this function a list of whatever you'd normally return on a single team
def get_ffa_teams(items):
    return {UNKNOWN_TAG_NAME:[item for item in items]}