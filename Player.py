'''
Created on Jul 12, 2020

@author: willg
'''

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
BATTLE_ROOM_TYPE = 'bt'

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


    def __init__(self, FC, name, role, positionInRoom, vr, points=0, discord_name=None, lounge_name=None, driver_vehicle="", room_type=""):
        '''
        Constructor
        '''
        self.FC = str(FC)
        self.name = str(name)
        if self.name == "no name":
            self.name = "Player"
        self.role = str(role)
        
        self.points = str(points)
        self.positionInRoom = positionInRoom
        self.vr = vr
        self.discord_name = discord_name
        self.lounge_name = lounge_name
        self.driver = None
        self.vehicle = None
        self.input_driver_vehicle(driver_vehicle)
        self.room_type = room_type
    
    def input_driver_vehicle(self, driver_vehicle):
        if driver_vehicle is None:
            self.driver = None
            self.vehicle = None
            return
        if "@" not in driver_vehicle:
            return
        driver, vehicle = driver_vehicle.split('@', 1)
        driver = driver.strip()
        vehicle = vehicle.strip()
        if vehicle == "" or vehicle == LONG_DASH or driver == "" or driver == LONG_DASH:
            self.driver = None
            self.vehicle = None
        else:
            self.driver = driver
            self.vehicle = vehicle
            
    #Returns the player's skill rating based on their VR and vehicle combination
    def get_player_skill_rating(self):
        vehicle_rating = 0
        if self.vehicle in vehicle_ratings:
            vehicle_rating = vehicle_ratings[self.vehicle] / MAX_VEHICLE_RATING
        elif self.vehicle == LONG_DASH:
            vehicle_rating = .5
        elif self.room_type == BATTLE_ROOM_TYPE:
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
        