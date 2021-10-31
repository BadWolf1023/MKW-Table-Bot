'''
Created on Jul 12, 2020

@author: willg
'''
from Race import BATTLE_REGION

vehicle_ratings = {"Mach Bike":10,
                  "Flame Runner":10,
                  "Bullet Bike":7,
                  "Flame Flyer": 5,
                  "Wild Wing":5,
                  "Mini Beast":4,
                  "Spear":3,
                  "Sneakster":3}
MAX_VR = 9999
MAX_VEHICLE_RATING = 10
VR_WEIGHT = .8
VEHICLE_WEIGHT = .2

LONG_DASH = "u\2014"
BATTLE_REGION = 'bt'

def get_scaled_rating(rating):
    if rating >= .9:
        return .7*rating + .3
    
    new_rating = 2*rating - .87
    if new_rating < 0:
        new_rating = 0
    return new_rating
    
class Player(object):
    '''
    classdocs
    '''


    def __init__(self, FC, playerPageLink, ol_status, roomPosition, playerRegion, playerConnFails, role, vr, character_vehicle, playerName, discord_name=None, lounge_name=None, mii_hex=None):
        '''
        Constructor
        '''
        self.FC = str(FC)
        self.playerPageLink = str(playerPageLink)
        self.pid = int(self.playerPageLink.split("/")[-1].strip('p'))
        self.ol_status = ol_status
        self.positionInRoom = roomPosition
        self.region = playerRegion
        self.playerConnFails = playerConnFails
        self.role = str(role)
        self.vr = vr
        self.character = None
        self.vehicle = None
        self.input_character_vehicle(character_vehicle)
        self.name = str(playerName)
        if self.name == "no name":
            self.name = "Player"
        self.discord_name = discord_name
        self.lounge_name = lounge_name
        self.mii_hex = mii_hex
    
    def set_mii_hex(self, mii_hex):
        self.mii_hex = mii_hex
    
    def get_mii_hex(self):
        return self.mii_hex
    def get_lounge_name(self):
        return self.lounge_name
    def get_discord_name(self):
        return self.discord_name
    def get_vehicle(self):
        return self.vehicle
    def get_character(self):
        return self.character
    def get_VR(self):
        return self.vr
    def get_role(self):
        return self.role
    def get_connection_fails(self):
        return self.playerConnFails
    def get_region(self):
        return self.region
    def get_position(self):
        return self.positionInRoom
    def get_ol_status(self):
        return self.ol_status
    def get_player_id(self):
        return self.pid
    def get_mkwx_url(self):
        return self.playerPageLink
    def get_name(self):
        return self.name
    def get_FC(self):
        return self.FC
    
    def set_name(self, new_name):
        self.name = new_name
        
        
        
        
    
    def input_character_vehicle(self, character_vehicle):
        if character_vehicle is None:
            self.character = None
            self.vehicle = None
            return
        if "@" not in character_vehicle:
            return

        character, vehicle = character_vehicle.split('@', 1)
        character = character.strip()
        vehicle = vehicle.strip()
        if vehicle == "" or vehicle == LONG_DASH or character == "" or character == LONG_DASH:
            self.character = None
            self.vehicle = None
        else:
            self.character = character
            self.vehicle = vehicle
            
    #Returns the player's skill rating based on their VR and vehicle combination
    def get_player_skill_rating(self):
        vehicle_rating = 0
        if self.vehicle in vehicle_ratings:
            vehicle_rating = vehicle_ratings[self.vehicle] / MAX_VEHICLE_RATING
        elif self.vehicle == LONG_DASH:
            vehicle_rating = .5
        elif self.region == BATTLE_REGION:
            vehicle_rating = 1
        
        temp_vr = 5000
        if isinstance(self.vr, str) and self.vr.isnumeric():
            temp_vr = int(self.vr)
        elif isinstance(self.vr, int):
            temp_vr = self.vr
            
        vr_scale_rating = temp_vr / MAX_VR
        if vr_scale_rating > 1:
            vr_scale_rating = 1
            
        return int(round(100*(get_scaled_rating(vehicle_rating * VEHICLE_WEIGHT + vr_scale_rating * VR_WEIGHT))))
        
            
            
    
    def __str__(self):
        return "Name: " + str(self.name) + " - FC: " + self.FC + " - Role: " + self.role
        
        