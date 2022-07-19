'''
Created on Jul 12, 2020

@author: willg
'''
import Mii
import UtilityFunctions
import UserDataProcessing

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
        if UtilityFunctions.isint(self.positionInRoom):
            self.positionInRoom = int(self.positionInRoom)
        else:
            self.positionInRoom = -1
        self.region = playerRegion
        self.playerConnFails = playerConnFails
        self.role = str(role)
        self.vr = vr
        self.character = None
        self.vehicle = None
        self.input_character_vehicle(character_vehicle)
        self.mii_name = str(playerName)
        if self.mii_name == "no name" or self.mii_name == "":
            self.mii_name = "Player"
        self.display_name = self.mii_name
        self.discord_name = discord_name
        self.lounge_name = lounge_name or UserDataProcessing.lounge_get(self.FC)
        self.mii_hex = mii_hex
    
    def set_mii_hex(self, mii_hex):
        self.mii_hex = mii_hex
    
    def get_mii_hex(self):
        if isinstance(self.mii_hex, Mii.Mii):
            return self.mii_hex.mii_data_hex_str
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
    def get_FC(self):
        return self.FC
    
    @property
    def name(self):
        return self.get_name()

    def get_name(self):
        return self.get_full_display_name()

    def get_display_name(self, for_table=False):
        if for_table:
            if self.subbed_out() and not self.display_name.strip().startswith('#'):
                return '#' + self.display_name
        return self.display_name
    
    def set_name(self, new_name, change_type):
        self.change_type = change_type
        if not new_name:
            return
        self.display_name = new_name
    
    def name_is_changed(self):
        return self.display_name != self.mii_name or self.subbed_out()
    
    def subbed_out(self):
        try: 
            return 'sub' in self.change_type
        except AttributeError:
            return False

    def get_sub_out_name(self):
        name = self.display_name
        use_lounge = self.change_type == 'sub' # name not changed
        if use_lounge:
            # name = UserDataProcessing.lounge_name_or_mii_name(self.FC, name)
            name = self.lounge_name or name
        if name.startswith('#'): # if the sub out's name starts with a hashtag, the entire line would be excluded from table, so add an invisible character so line still displays
            name = '\u200b' + name
        
        return name
    
    def get_full_display_name(self):
        change_info = ""
        try:
            if self.change_type == 'change_sub':
                change_info = " (Name Changed & Subbed Out)"
            elif self.change_type == 'sub':
                change_info = " (Subbed Out)"
            else:
                change_info = " (Name Changed)"
        except AttributeError: # name hasn't been changed
            pass

        return self.display_name + change_info

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
        
    # def __eq__(self, o: object) -> bool:
    #     if not isinstance(o, Player):
    #         return False
    #     return o.FC == self.FC
    
    # def __hash__(self) -> int:
    #     return hash(self.FC)

    def __str__(self):
        return "Name: " + str(self.display_name) + " - FC: " + self.FC + " - Role: " + self.role
        
        