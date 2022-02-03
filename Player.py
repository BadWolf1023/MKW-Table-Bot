'''
Created on Jul 12, 2020

@author: willg
'''
from typing import Union
import UtilityFunctions

vehicle_ratings = {"Mach Bike": 10,
                   "Flame Runner": 10,
                   "Bullet Bike": 7,
                   "Flame Flyer": 5,
                   "Wild Wing": 5,
                   "Mini Beast": 4,
                   "Spear": 3,
                   "Sneakster": 3}
MAX_VR = 9999
MAX_VEHICLE_RATING = 10
VR_WEIGHT = .8
VEHICLE_WEIGHT = .2

WIIMMFI_LONG_DASH = "\u2014"
BATTLE_REGION = 'bt'


def get_scaled_rating(rating):
    if rating >= .9:
        return .7*rating + .3

    new_rating = 2*rating - .87
    if new_rating < 0:
        new_rating = 0
    return new_rating

# TODO: Add get_player_page(fc) function


class Player(object):
    '''
    classdocs
    '''

    def __init__(self, FC: str, player_url: str, ol_status: str, room_position: int, region: str, connection_fails: float, role: str, vr: Union[None, int], character_vehicle: Union[None, str], mii_name: str, mii_hex=None):
        '''
        Constructor
        '''
        self._FC = FC
        self._url = player_url
        self._pid = int(self.get_url().split("/")[-1].strip('p'))
        self._ol_status = ol_status
        self._room_position = int(room_position) if UtilityFunctions.is_int(room_position) else -1
        self._region = region
        self._connection_fails = connection_fails
        self._role = role
        self._vr = vr
        self._character = None
        self._vehicle = None
        self._set_character_and_vehicle(character_vehicle)
        self._mii_name = "Player" if mii_name in {"", "no name"} else mii_name
        self._mii_hex = mii_hex
        self._validate_data()

    def get_FC(self) -> str:  # Guaranteed to be a str
        return self._FC

    def get_url(self) -> str:  # Guaranteed to be a str
        return self._url

    def get_player_id(self) -> int:  # Guaranteed to be an int
        return self._pid

    def get_ol_status(self) -> str:  # Guaranteed to be a str
        return self._ol_status

    def get_room_position(self) -> int:  # Guaranteed to be an int
        return self._room_position

    def get_region(self) -> str:  # Guaranteed to be a str
        return self._region

    def get_connection_fails(self) -> float:  # Guaranteed to be a float
        return self._connection_fails

    def get_role(self) -> str:  # Guaranteed to be a str
        return self._role

    # Guaranteed to be an int or None
    def get_versus_rating(self) -> Union[int, None]:
        return self._vr

    # Guaranteed to be a str or None
    def get_character(self) -> Union[str, None]:
        return self._character

    def _set_character(self, character: Union[str, None]):
        self._character = character

    # Guaranteed to be a str or None
    def get_vehicle(self) -> Union[str, None]:
        return self._vehicle

    def _set_vehicle(self, vehicle: Union[str, None]):
        self._vehicle = vehicle

    def get_mii_name(self) -> str:  # Guaranteed to be a str
        return self._mii_name

    def set_mii_name(self, mii_name: str):
        self._mii_name = mii_name

    # Legacy for backward compatibility for database
    def get_lounge_name(self) -> None:
        return None

    # Legacy for backward compatibility for database
    def get_discord_name(self) -> None:
        return None

    # Guaranteed to be a str or None
    def get_mii_hex(self) -> Union[str, None]:
        return self._mii_hex

    def set_mii_hex(self, mii_hex: Union[str, None]):
        self._mii_hex = mii_hex

    def _set_character_and_vehicle(self, character_vehicle: Union[None, str]):
        if character_vehicle is None:
            return
        if "@" not in character_vehicle:
            return

        character, vehicle = character_vehicle.split('@', 1)
        character = character.strip()
        vehicle = vehicle.strip()
        if vehicle != "" and vehicle != WIIMMFI_LONG_DASH and character != "" and character != WIIMMFI_LONG_DASH:
            self._set_character(character)
            self._set_vehicle(vehicle)

    # Returns the player's skill rating based on their VR and vehicle combination
    def get_player_skill_rating(self) -> int:
        vehicle_rating = 0
        if self.get_vehicle() in vehicle_ratings:
            vehicle_rating = vehicle_ratings[self.get_vehicle(
            )] / MAX_VEHICLE_RATING
        elif self.get_vehicle() == WIIMMFI_LONG_DASH:
            vehicle_rating = .5
        elif self.get_region() == BATTLE_REGION:
            vehicle_rating = 1

        temp_vr = 5000 if self.get_versus_rating() is None else self.get_versus_rating()

        vr_scale_rating = temp_vr / MAX_VR
        if vr_scale_rating > 1:
            vr_scale_rating = 1

        return int(round(100*(get_scaled_rating(vehicle_rating * VEHICLE_WEIGHT + vr_scale_rating * VR_WEIGHT))))

    def _validate_data(self):
        validations = [[self.get_FC, "FC", (str,)],
                       [self.get_url, "player_url", (str,)],
                       [self.get_player_id, "pid", (int,)],
                       [self.get_ol_status, "ol_status", (str,)],
                       [self.get_room_position, "room_position", (int,)],
                       [self.get_region, "region", (str,)],
                       [self.get_connection_fails, "connection_fails", (float,)],
                       [self.get_role, "role", (str,)],
                       [self.get_versus_rating, "vr", (int, type(None))],
                       [self.get_character, "character_vehicle", (str, type(None))],
                       [self.get_vehicle, "character_vehicle", (str, type(None))],
                       [self.get_mii_name, "mii_name", (str,)],
                       [self.get_mii_hex, "mii_hex", (str, type(None))]]
        for call, var_name, valid_types in validations:
            if not isinstance(call(), valid_types):
                raise TypeError(
                    f'''The given '{var_name}' of type '{type(call()).__name__}' is not any of the allowed types: {", ".join(t.__name__ for t in valid_types)}''')

    def __str__(self):
        return "Name: " + str(self.get_mii_name()) + " - FC: " + self.get_FC() + " - Role: " + self.get_role()

