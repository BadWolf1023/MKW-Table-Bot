'''
Created on Jul 12, 2020

@author: willg
'''
from typing import Tuple, Union
import UserDataProcessing
import UtilityFunctions
import Player
import re


DISCONNECTION_TIME = (999, 999, 999)
BOGUS_TIME_LIMIT = (5, 59, 999)
MINIMUM_DELTA_VALUE = -10
MAXIMUM_DELTA_VALUE = 10

NO_DELTA_DISPLAY_RANGE = (-.5, .5)


def is_valid_time_str(time_str: str) -> bool:
    return re.match("^([\d]{1,3}:)?[\d]{1,3}\.[\d]{3}$", time_str.strip()) is not None

class Placement:

    def __init__(self, player: Player.Player, time: str, delta:Union[float, None]=None, is_wiimmfi_place=False):
        self._validate_data(player, time, delta, is_wiimmfi_place)
        self._player = player
        self._place = -1
        self._time = Placement._create_time(time)
        self._delta = Placement._process_delta(delta)
        self._is_wiimmfi_place = is_wiimmfi_place

    def get_player(self) -> Player.Player:
        return self._player

    def get_place(self) -> int:
        return self._place

    def get_time(self) -> Tuple[int, int, int]:
        return self._time

    def get_delta(self) -> float:
        return self._delta

    def is_from_wiimmfi(self) -> bool:
        return self._is_wiimmfi_place

    def get_fc_and_name(self) -> Tuple[str, str]:
        '''Returns the player's FC and mii name that this placement is for'''
        return self.get_player().get_FC(), self.get_player().get_mii_name()

    def set_place(self, place: int):
        if not isinstance(place, int):
            raise TypeError(f'''The given 'place' of type '{type(place).__name__}' is not any of the allowed types: {int.__name__}''')
        self._place = place

    @staticmethod
    def _create_time(time: str) -> Tuple[int, int, int]:
        minute = "-1"
        second = "-1"
        millisecond = "-1"
        if time == Player.WIIMMFI_LONG_DASH:
            return DISCONNECTION_TIME  # Disconnection
        elif (":" in time):
            digits = time.split(":")
            minute = digits[0]
            second, millisecond = digits[1].split(".")
        else:
            minute = "0"
            second, millisecond = time.split(".")

        return (int(minute), int(second), int(millisecond))

    @staticmethod
    def _process_delta(delta: Union[str, None]) -> float:
        return float(delta) if UtilityFunctions.is_float(delta) else float(0)

    def is_disconnected(self) -> bool:
        return self.get_time() == DISCONNECTION_TIME

    def is_delta_unusual(self) -> bool:
        if self.get_delta() is None:
            return False
        return self.get_delta() < MINIMUM_DELTA_VALUE or self.get_delta() > MAXIMUM_DELTA_VALUE

    def is_time_large(self) -> bool:
        if self.is_disconnected():
            return False
        return self.get_time() > BOGUS_TIME_LIMIT

    def should_display_delta(self) -> bool:
        return self.get_delta() <= NO_DELTA_DISPLAY_RANGE[0] or self.get_delta() >= NO_DELTA_DISPLAY_RANGE[1]

    def get_time_string(self) -> str:
        '''Returns the placement time as a string. Useful for display purposes.'''
        minutes, seconds, milliseconds = self.get_time()
        return f"{minutes}:{seconds:02}.{milliseconds:03}"

    def get_time_seconds(self) -> float:
        '''Returns the placement time as the total number of seconds, including milliseconds'''
        minutes, seconds, milliseconds = self.get_time()
        return minutes*60 + seconds + milliseconds/1000

    def __eq__(self, other):
        return self.get_time() == other.get_time()

    def __lt__(self, other):
        return self.get_time() < other.get_time()

    def __gt__(self, other):
        return self.get_time() > other.get_time()

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def __str__(self):
        to_return = f"{self.get_place()}. {UtilityFunctions.filter_text(self.get_player().get_mii_name() + UserDataProcessing.lounge_add(self.get_player().get_FC()))} - "
        if self.is_disconnected():
            to_return += "DISCONNECTED"
        else:
            to_return += self.get_time_string()

        if self.should_display_delta():
            to_return += f" - **{self.get_delta()}s lag start**"
        return to_return

    def _validate_data(self, player: Player.Player, time: str, delta: Union[float, None], is_wiimmfi_place: bool):
        validations = [[lambda: player, "player", (Player.Player,)],
                       [lambda: time, "time", (str,)],
                       [lambda: delta, "delta", (float, type(None))],
                       [lambda: is_wiimmfi_place, "is_wiimmfi_place", (bool,)]]
        for call, var_name, valid_types in validations:
            if not isinstance(call(), valid_types):
                raise TypeError(f'''The given '{var_name}' of type '{type(call()).__name__}' is not any of the allowed types: {", ".join(t.__name__ for t in valid_types)}''')
        
        try:
            Placement._create_time(time)
        except:
            raise TypeError(f'''The given 'time' '{time}' was not in the correct format. Valid format examples: 1:01.912 and 54.019''')


if __name__ == "__main__":
    Placement(Player.get_dummy_player(), "0.0", 0.0, False)
