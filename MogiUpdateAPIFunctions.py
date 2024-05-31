'''
Created on Sep 23, 2020

@author: willg
'''

from typing import List, Dict, Tuple
import aiohttp
import UtilityFunctions

lounge_mmr_api_url = 'https://www.mkwlounge.gg/api/ladderplayer.php'


async def getJSONData(full_url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url) as r:
                if r.status == 200:
                    js = await r.json()
                    return js
    except:
        return None
            
def addFilter(url, filter_type, data):
    result = url
    if len(result) < 1:
        return result
    if '?' not in result: #URL has no args, prepare is for args
        result += '?'
    elif result[-1] == '?': #URL is prepared for args already
        pass
    else: #URL already has args, add to them
        result += '&'
    
    result += filter_type + "="
    
    if isinstance(data, str):
        result += data
    elif isinstance(data, list):
        result += ",".join(data)
    else:
        raise TypeError("Filter data is not a string or list of strings.")
    #result = urllib.parse.quote(result)
    return result


def getLookup(name:str):
    return name.replace(" ", "").lower().strip("\n\t")

def _reverseEngineerResults(lounge_names_mapping: List[Tuple[str, str, int]], json_data) -> Dict[str, int]:
    """lounge_names_mapping is a list of players. The data in the tuples is:
    Index 0: A "mapping" version of a players name
    Index 1: The player's original name given to getPlayerIDs
    Index 2: The player's score
    
    Returns a tuple of (None, []) if the JSON data was corrupt/unexpected format
    Upon success, returns a tuple of (matched_players, unmatched_players)
    """
    try:
        if len(json_data) != len(lounge_names_mapping):
            pass
    #I'm not going to bother specifying specific exceptions since this is a simple test for corrupt data
    #A few different exception types could be thrown here, like the data type doesn't have len, but they mean the same thing: corrupt data
    except:
        return None, [] #Corrupt data
        
    mappings = {}
    player_id_json_name = "player_id"
    player_name_json_name = "player_name"
    current_mmr_json_name = "current_mmr"
    for player_data in json_data:
        #Corrupt data check
        if player_id_json_name not in player_data or player_name_json_name not in player_data or current_mmr_json_name not in player_data:
            return None, []
        #Corrupt data check
        
        if UtilityFunctions.isint(player_data[player_id_json_name]):
            player_data[player_id_json_name] = int(player_data[player_id_json_name])
            
        if UtilityFunctions.isint(player_data[current_mmr_json_name]):
            player_data[current_mmr_json_name] = int(player_data[current_mmr_json_name])

        
        if not isinstance(player_data[player_id_json_name], int):
            return None, []
        
        if not isinstance(player_data[current_mmr_json_name], int):
            return None, []
        
        
        jsonLookupName = getLookup(player_data[player_name_json_name])
        for lookupName, lounge_name, score in lounge_names_mapping:
            if lookupName == jsonLookupName:
                mappings[lounge_name] = (player_data[player_id_json_name], score, player_data[current_mmr_json_name])
                break
    
    #Final incorrect data check
    missing = []
    for _, lounge_name, score in lounge_names_mapping:
        if lounge_name not in mappings:
            missing.append(lounge_name)
    
    return mappings, missing
            
#Takes a list of players, returns that list of player's matched to their player IDs
async def getPlayerIDs(mogi_players: List[Tuple[str, int]], is_rt=True, mogiPlayerAmount=12) -> Dict[str, int]:
    """mogi_players is a list of players. The tuples in this list are as follows:
    Index 0: The player's lounge name
    Index 1: The player's score (can set this index to 0 if scores are irrelevant)
    
    Set is_rt to True for rts and False for cts
    """
    
    lounge_names = [getLookup(data[0]) for data in mogi_players]
    lounge_names_mapping = []
    for i in range(len(mogi_players)):
        lounge_names_mapping.append((lounge_names[i], mogi_players[i][0], mogi_players[i][1]))
    
    full_url = lounge_mmr_api_url
    if is_rt:
        full_url = addFilter(full_url, "ladder_type", ["rt"])
    else:
        full_url = addFilter(full_url, "ladder_type", ["ct"])
    full_url = addFilter(full_url, "player_names", lounge_names)
    data = await getJSONData(full_url)
    
    
    if data is None:
        print("Bad request to 255MP's Lounge Player Data API... The website is either down or went offline for a split second. Try again.")
        return None, None
    if "error" in data:
        print("Bad request to 255MP's Lounge Player Data API... The website gave back corrupt data. Try again. If this continues, you really need to tell Bad Wolf.")
        return None, None
    if "status" not in data or data["status"] != "success":
        print("Bad request to 255MP's Lounge Player Data API... The website gave back corrupt data. Try again. If this continues, you really need to tell Bad Wolf.")
        return None, None
    if "results" not in data or not isinstance(data["results"], list):
        print("Bad request to 255MP's Lounge Player Data API... The website gave back corrupt data. Try again. If this continues, you really need to tell Bad Wolf.")
        return None, None
    
    return _reverseEngineerResults(lounge_names_mapping, data["results"])
    
    
    
    
    