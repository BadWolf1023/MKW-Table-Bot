'''
Created on Jul 12, 2020

@author: willg
'''
from typing import Tuple
import UserDataProcessing
import UtilityFunctions
import Player
import re

DEBUGGING = False
DISCONNECTION_TIME = (999, 999, 999)
BOGUS_TIME_LIMIT = (5, 59, 999)
MINIMUM_DELTA_VALUE = -10
MAXIMUM_DELTA_VALUE = 10

NO_DELTA_DISPLAY_RANGE = (-.5, .5)


def is_valid_time_str(time_str):
    return re.match("^([\d]{1,3}:)?[\d]{1,3}\.[\d]{3}$", time_str.strip()) is not None

class Placement:

    def __init__(self, player: Player.Player, time, delta=None, is_wiimmfi_place=False):
        self._player = player
        self._place = -1
        self._time = Placement._create_time(time)
        self._delta = Placement._process_delta(delta)
        self._is_wiimmfi_place = is_wiimmfi_place

    def get_player(self) -> Player.Player:
        return self._player

    def get_place(self):
        return self._place

    def get_time(self)  -> Tuple[int, int, int]:
        return self._time

    def get_delta(self):
        return self._delta

    def is_from_wiimmfi(self):
        return self._is_wiimmfi_place

    def get_fc_and_name(self):
        return self.get_player().get_FC(), self.get_player().name

    def set_place(self, place: int):
        self._place = place

    @staticmethod
    def _create_time(time: str) -> Tuple[int, int, int]:
        minute = "-1"
        second = "-1"
        millisecond = "-1"
        if DEBUGGING:
            print(time)
        if time == Player.LONG_DASH:
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
    def _process_delta(delta):
        return float(delta) if UtilityFunctions.isfloat(delta) else float(0)

    def is_disconnected(self):
        return self.get_time() == DISCONNECTION_TIME

    def is_delta_unusual(self):
        if self.get_delta() is None:
            return False
        return self.get_delta() < MINIMUM_DELTA_VALUE or self.get_delta() > MAXIMUM_DELTA_VALUE

    def is_time_large(self):
        if self.is_disconnected():
            return False
        return self.get_time() > BOGUS_TIME_LIMIT

    def should_display_delta(self):
        return self.get_delta() < NO_DELTA_DISPLAY_RANGE[0] or self.get_delta() > NO_DELTA_DISPLAY_RANGE[1]

    def get_time_string(self):
        minutes = str(self.get_time()[0])
        seconds = str(self.get_time()[1])
        if len(seconds) == 1:
            seconds = "0" + seconds
        milliseconds = str(self.get_time()[2])
        if len(milliseconds) == 1:
            milliseconds = "00" + milliseconds
        elif len(milliseconds) == 2:
            milliseconds = "0" + milliseconds
        return minutes + ":" + seconds + "." + milliseconds

    def get_time_seconds(self) -> float:
        '''Returns the placement time as the total number of seconds, including milliseconds'''
        minutes, seconds, milliseconds = self.get_time()
        return minutes*60+seconds+milliseconds/1000

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
        to_return = f"{self.get_place()}. {UtilityFunctions.filter_text(self.get_player().name + UserDataProcessing.lounge_add(self.get_player().get_FC()))} - "
        if self.is_disconnected():
            to_return += "DISCONNECTED"
        else:
            to_return += self.get_time_string()

        if self.should_display_delta():
            to_return += f" - **{self.get_delta()}s lag start**"
        return to_return
