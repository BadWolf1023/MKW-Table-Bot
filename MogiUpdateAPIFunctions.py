'''
Created on Sep 23, 2020

@author: willg
'''

from typing import List, Dict, Tuple
import aiohttp

lounge_mmr_api_url = 'https://mariokartboards.com/lounge/json/player.php'


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
    try:
        if len(json_data) != len(lounge_names_mapping):
            pass
    #I'm not going to bother specifying specific exceptions since this is a simple test for corrupt data
    #A few different exception types could be thrown here, like the data type doesn't have len, but they mean the same thing: corrupt data
    except:
        return None, [] #Corrupt data
        
    mappings = {}
    for player_data in json_data:
        #Corrupt data check
        if "pid" not in player_data or "name" not in player_data or "current_mmr" not in player_data:
            return None, []
        #Corrupt data check
        if isinstance(player_data["pid"], str) and player_data["pid"].isnumeric():
            player_data["pid"] = int(player_data["pid"])
            
        if isinstance(player_data["current_mmr"], str) and player_data["current_mmr"].isnumeric():
            player_data["current_mmr"] = int(player_data["current_mmr"])

        
        if not isinstance(player_data["pid"], int):
            return None, []
        
        if not isinstance(player_data["current_mmr"], int):
            return None, []
        
        
        jsonLookupName = getLookup(player_data["name"])
        for lookupName, lounge_name, score in lounge_names_mapping:
            if lookupName == jsonLookupName:
                mappings[lounge_name] = (player_data["pid"], score, player_data["current_mmr"])
                break
    
    #Final incorrect data check
    missing = []
    for _, lounge_name, score in lounge_names_mapping:
        if lounge_name not in mappings:
            missing.append(lounge_name)
    
    return mappings, missing
            
#Takes a list of players, returns that list of player's matched to their player IDs
async def getPlayerIDs(mogi_players: List[Tuple[str, int]], is_rt=True, mogiPlayerAmount=12) -> Dict[str, int]:
    #Don't even ping the API if this clearly isn't a mogi
    
    lounge_names = [getLookup(data[0]) for data in mogi_players]
    lounge_names_mapping = []
    for i in range(len(mogi_players)):
        lounge_names_mapping.append((lounge_names[i], mogi_players[i][0], mogi_players[i][1]))
    
    full_url = lounge_mmr_api_url
    if is_rt:
        full_url = addFilter(full_url, "type", ["rt"])
    else:
        full_url = addFilter(full_url, "type", ["ct"])
    full_url = addFilter(full_url, "name", lounge_names)
    data = await getJSONData(full_url)
    
    
    if data == None:
        print("Bad request to Lounge API... The website is either down or went offline for a split second. Try again.")
        return None, None
    if "error" in data:
        print("Bad request to Lounge API... The website gave back corrupt data. Try again. If this continues, you really need to tell Bad Wolf.")
        return None, None
    
    return _reverseEngineerResults(lounge_names_mapping, data)
    
    
    
    
    