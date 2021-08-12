from typing import List, Dict
code = None
loungeAPIURL = "https://mariokartboards.com/lounge/api/wiimmfi.php"

import aiohttp
from datetime import datetime

async def getOnlineData(full_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(full_url) as r:
            if r.status == 200:
                js = await r.json()
                return js

def addFilter(url, filter_type, data):
    result = url
    result += "&" + filter_type + "="
    result += ",".join(data)
    #result = urllib.parse.quote(result)
    return result

def parseData(data:List[Dict], loungeVerifiedOnly=True):
    if data is None:
        print("Bad request to 255MP's Wiimmfi API... Data was None.")
        return None, None
    if "error" in data:
        print("Bad request to 255MP's Wiimmfi API... Error in data.")
        return None, None
    if "status" not in data or data["status"] != "success":
        print("Bad request to 255MP's Wiimmfi API... Status didn't exist or wasn't success.")
        return None, None
    if "results" not in data or not isinstance(data["results"], list):
        print("Bad request to 255MP's Wiimmfi API... Results didn't exist or weren't a list")
        return None, None
    data_results = data["results"]
    
    id_lounge = {}
    fc_id = {}
    cur_time = datetime.now()
    for player in data_results:
        if loungeVerifiedOnly:
            if player['lounge_verified']:
                id_lounge[player['discord_user_id']] = player['name']
                fc_id[player['fc']] = (player['discord_user_id'], cur_time)
        else:
            if player['verified']:
                id_lounge[player['discord_user_id']] = player['name']
                fc_id[player['fc']] = (player['discord_user_id'], cur_time)
    return id_lounge, fc_id


async def getByDiscordIDs(discordIDs:List[str], loungeVerifiedOnly=True):
    fullAPIURL = loungeAPIURL + "?code=" + code
    fullURL = addFilter(fullAPIURL, "discord_user_ids", discordIDs)
    data = None
    try:
        data = await getOnlineData(fullURL)
    except:
        pass
    return parseData(data, loungeVerifiedOnly)
    
async def getByLoungeNames(loungeNames:List[str], loungeVerifiedOnly=True):
    fullAPIURL = loungeAPIURL + "?code=" + code
    fullURL = addFilter(fullAPIURL, "player_names", loungeNames)
    data = None
    try:
        data = await getOnlineData(fullURL)
    except:
        pass
    return parseData(data, loungeVerifiedOnly)

async def getByFCs(FCs:List[str], loungeVerifiedOnly=True):
    fullAPIURL = loungeAPIURL + "?code=" + code
    fullURL = addFilter(fullAPIURL, "fcs", FCs)
    data = None
    try:
        data = await getOnlineData(fullURL)
    except:
        pass
    return parseData(data, loungeVerifiedOnly)