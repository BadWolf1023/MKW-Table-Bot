'''
Created on Oct 20, 2021

@author: willg

I don't want to make the AIs classes, so this module will be shared by all AIs for common functionality
'''
from typing import Dict, List

# Use the BAD_NAME_TAG constant if their name is garbage or blank (no length) or if you don't want to deal with their name
BAD_NAME_TAG = "Unknown"
# If their name is okay, but you don't know their tag, use this constant
UNKNOWN_TAG_NAME = "No Tag"
# If your AI determined that someone's tag should be Player, use this constant
PLAYER_TAG = "Player"

MAXIMUM_BRACKET_TAG_LEN = 4

OTHER_CHARS = "\u03A9\u038F"
VALID_CHARS = "/\\*^+abcdefghijklmnopqrstuvwxyz" + "abcdefghijklmnopqrstuvwxyz0123456789[]".upper() + OTHER_CHARS
UNICODE_MAPPINGS_TO_ALPHA = {"@": "A", "\u00A7": "S", "$": "S", "\u00A2": "c", "\u00A5": "Y", "\u20AC": "E", "\u00A3": "E", "\u00E0": "a", "\u00E1": "a", "\u00E2": "a", "\u00E4": "a", "\u00E5": "a", "\u00E6": "ae", "\u00E3": "a", "\u00E7": "c", "\u00E8": "e", "\u00E9": "e", "\u00EA": "e", "\u00EB": "e", "\u00EC": "i", "\u00ED": "i", "\u00EE": "i", "\u00EF": "i", "\u00F1": "n", "\u00F2": "o", "\u00F3": "o", "\u00F4": "o", "\u00F6": "o", "\u0153": "oe", "\u00F8": "o", "\u00F5": "o", "\u00DF": "B", "\u00F9": "u", "\u00FA": "u", "\u00FB": "u", "\u00FC": "u", "\u00FD": "y", "\u00FF": "y", "\u00C0": "A", "\u00C1": "A", "\u00C2": "A", "\u00C4": "A", "\u00C5": "A", "\u00C6": "AE", "\u00C3": "A", "\u00C7": "C", "\u00C8": "E", "\u00C9": "E", "\u00CA": "E", "\u00CB": "E", "\u00CC": "I", "\u00CD": "I", "\u00CE": "I", "\u00CF": "I", "\u00D1": "N", "\u00D2": "O", "\u00D3": "O", "\u00D4": "O", "\u00D6": "O", "\u0152": "OE", "\u00D8": "O", "\u00D5": "O", "\u00D9": "U", "\u00DA": "U", "\u00DB": "U", "\u00DC": "U", "\u00DD": "Y", "\u0178": "Y", "\u03B1": "a", "\u03B2": "B",
                             "\u03B3": "y", "\u03B4": "o", "\u03B5": "e", "\u03B6": "Z", "\u03B7": "n", "\u03B8": "O", "\u03B9": "i", "\u03BA": "k", "\u03BB": "A", "\u03BC": "u", "\u03BD": "v", "\u03BE": "E", "\u03BF": "o", "\u03C0": "r", "\u03C1": "p", "\u03C3": "o", "\u03C4": "t", "\u03C5": "u", "\u03C6": "O", "\u03C7": "X", "\u03C8": "w", "\u03C9": "W", "\u0391": "A", "\u0392": "B", "\u0393": "r", "\u0394": "A", "\u0395": "E", "\u0396": "Z", "\u0397": "H", "\u0398": "O", "\u0399": "I", "\u039A": "K", "\u039B": "A", "\u039C": "M", "\u039D": "N", "\u039E": "E", "\u039F": "O", "\u03A0": "N", "\u03A1": "P", "\u03A3": "E", "\u03A4": "T", "\u03A5": "Y", "\u03A6": "O", "\u03A7": "X", "\u03A8": "w", "\u0386": "A", "\u0388": "E", "\u0389": "H", "\u038A": "I", "\u038C": "O", "\u038E": "Y", "\u0390": "i", "\u03AA": "I", "\u03AB": "Y", "\u03AC": "a", "\u03AD": "E", "\u03AE": "n", "\u03AF": "i", "\u03B0": "u", "\u03C2": "c", "\u03CA": "i", "\u03CB": "u", "\u03CC": "o", "\u03CD": "u", "\u03CE": "w", "\u2122": "TM", "\u1D49": "e", "\u00A9": "C", "\u00AE": "R", "\u00BA": "o", "\u00AA": "a", "\u266D": "b"}
REMOVE_IF_START_WITH = "/\\*^+"

# Your AI must call this function if the format is FFA (or if your AI thinks the format is FFA)
# Give this function a list of whatever you'd normally return on a single team
def get_ffa_teams(items):
    return {UNKNOWN_TAG_NAME: [item for item in items]}


def get_alphabetical_tags(players, tagDeterminer: callable, players_per_team=2) -> Dict[str, List[int]]:
    if players_per_team is None:
        players_per_team = 2

    teams = {}
    for i, playerName in enumerate(players):
        playerTag = tagDeterminer(playerName)
        if playerTag not in teams:
            teams[playerTag] = []
        teams[playerTag].append(i)
    return teams


def get_tag_smart(name: str):
    bracket_tag = get_bracket_tag(name)
    if bracket_tag is not None:
        return bracket_tag

    name = stripBadChars(name)

    if name == "no name" or name.lower() == "player":
        return (PLAYER_TAG, PLAYER_TAG)

    if len(name) == 0:
        return (PLAYER_TAG, PLAYER_TAG)
    else:
        # Return the Alpha value (for sorting) in the first tuple index, and the actual tag as the 2nd index
        return (_get_tag_value(name[0]), name[0])


def _get_tag_value(tag):
    while len(tag) > 0:
        if tag[0] in REMOVE_IF_START_WITH:
            tag = tag[1:]
        else:
            break
    temp = ""
    for c in tag:
        if c in UNICODE_MAPPINGS_TO_ALPHA:
            temp += UNICODE_MAPPINGS_TO_ALPHA[c]
        elif c in VALID_CHARS:
            temp += c
    if temp.lower() == PLAYER_TAG.lower():
        return PLAYER_TAG
    return temp.upper()


def get_bracket_tag(name: str):
    # Handle stuff in brackets
    if "[" in name and "]" in name:
        startbracket_index = name.index("[")
        endbracket_index = name.index("]")
        if endbracket_index - startbracket_index - 1 >= 1:  # Something is in the brackets
            if endbracket_index - startbracket_index - 1 <= MAXIMUM_BRACKET_TAG_LEN:
                brackets_tag = name[startbracket_index+1:endbracket_index]
                return (_get_tag_value(brackets_tag), stripBadChars(brackets_tag))
    return None


def stripBadChars(tag):
    while len(tag) > 0:
        if tag[0] in REMOVE_IF_START_WITH:
            tag = tag[1:]
        else:
            break
    temp = ""
    for c in tag:
        if c in UNICODE_MAPPINGS_TO_ALPHA or c in VALID_CHARS:
            temp += c
    return temp
