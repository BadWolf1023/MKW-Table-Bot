'''
Created on Jul 30, 2020

@author: willg
'''
from bs4 import BeautifulSoup, NavigableString
import re
from datetime import datetime, timedelta
import UserDataProcessing
import aiohttp
import codecs

current_mkwx_soups = None
mkwx_soup_last_updated = None
mkwx_cache_time = timedelta(seconds=10)



wiimmfi_url = 'https://wiimmfi.de'
mkwxURL = 'https://wiimmfi.de/stats/mkwx'
submkwxURL = f"{mkwxURL}/list/"
special_test_cases = {f"{submkwxURL}r0000000":("Special room: Room has times with high deltas and a race with times that are the same as another race's times", "testing_rooms/SameTimeHighDelta.html")}


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def getRoomHTML(roomLink):
    print(str(datetime.now().time()) + ": getRoomHTML(" + roomLink + ") is making an HTTPS request.")
    
    if roomLink in special_test_cases:
        description, local_file_path = special_test_cases[roomLink]
        fp = codecs.open(local_file_path, "r", "utf-8")
        html_data = fp.read()
        fp.close()
        return html_data
        
    async with aiohttp.ClientSession() as session:
        return await fetch(session, roomLink)


async def __getMKWXSoupCall__():
    print(str(datetime.now().time()) + ": getMKWXSoup() is making an HTTPS request.")
    async with aiohttp.ClientSession() as session:
        mkwxHTML = await fetch(session, mkwxURL)
        return BeautifulSoup(mkwxHTML, "html.parser")


async def getMKWXSoup():
    global current_mkwx_soups
    global mkwx_soup_last_updated
    if current_mkwx_soups is None or \
    mkwx_soup_last_updated is None or \
    (datetime.now() - mkwx_cache_time) > mkwx_soup_last_updated:
        if current_mkwx_soups is None:
            current_mkwx_soups = []
        current_mkwx_soups.append( await __getMKWXSoupCall__() )
        mkwx_soup_last_updated = datetime.now()
        
    if current_mkwx_soups is not None:
        while len(current_mkwx_soups) >= 5:
            current_mkwx_soups[0].decompose()
            del current_mkwx_soups[0]
    return current_mkwx_soups[-1]



async def getrLIDSoup(rLID):
    roomHTML = await getRoomHTML(submkwxURL + rLID)
    temp = BeautifulSoup(roomHTML, "html.parser")
    if temp.find(text="No match found!") is None:
        return temp
    return None
        
def _is_rLID(roomID):
    return re.match("^r[0-9]{7}$", roomID) is not None

def _is_fc(fc):
    return re.match("^[0-9]{4}[-][0-9]{4}[-][0-9]{4}$", fc.strip()) is not None

#getRoomLink old name
async def getRoomData(rid_or_rlid):
    if _is_rLID(rid_or_rlid): #It is a unique rxxxxxxx number given
        #Check if the rLID is a valid link (bogus input check, or the link may have expired)
        rLIDSoup = await getrLIDSoup(rid_or_rlid)
        if rLIDSoup is not None:
            return submkwxURL + rid_or_rlid, rid_or_rlid, rLIDSoup
        else:
            return None, None, None
        
    #Normal room ID given, go find the link for the list
    mkwxSoup = await getMKWXSoup()
        
    roomIDSpot = mkwxSoup.find(text=rid_or_rlid)
    if roomIDSpot is None:
        return None, None, None
    link = str(roomIDSpot.find_previous('a')['data-href'])
    rLID = link.split("/")[-1]
    rLIDSoup = await getrLIDSoup(rLID)
    return wiimmfi_url + link, rLID, rLIDSoup #link example: /stats/mkwx/list/r1279851


#async def getAllSurfaceRoomData():
    

async def getMKWXHTMLDataByFC(fcs):
    soup = await getMKWXSoup()
    fcSpot = None
    for fc in fcs:
        fcSpot = soup.find(text=fc)
        if fcSpot is not None:
            break
        
    if fcSpot is None:
        return None
    #found the FC, now go get the room
    levels = [fcSpot.parent.parent.parent]
    del fcSpot
    #should run until we hit the roomID, but in cases of corrupt HTML, we don't want an infinite loop. So eventually, this will stop when there is no previous siblings
    returnNone = False
    while True:
        #print("\n\n=====================================================\n")
        
        levels.append(levels[-1].previous_sibling)
        #print(correctLevel)
        if levels[-1] is None:
            returnNone = True
            break
        if isinstance(levels[-1], NavigableString):
            continue
        if 'id' in levels[-1].attrs:
            break
    
    while len(levels) > 1:
        del levels[0]
        
    if returnNone:
        del levels[0]
        return None
    return levels.pop()



#getRoomLinkByFC old name
async def getRoomDataByFC(fcs):
    soup = await getMKWXSoup()
    fcSpot = None
    for fc in fcs:
        fcSpot = soup.find(text=fc)
        if fcSpot is not None:
            break
        
    if fcSpot is None:
        return None, None, None
    
    #found the FC, now go get the room
    correctLevel = fcSpot.parent.parent.parent
    #print(correctLevel)
    #should run until we hit the roomID, but in cases of corrupt HTML, we don't want an infinite loop. So eventually, this will stop when there is no previous siblings
    while True:
        #print("\n\n=====================================================\n")
        correctLevel = correctLevel.previous_sibling
        #print(correctLevel)
        if correctLevel is None:
            return None, None, None
        if isinstance(correctLevel, NavigableString):
            continue
        if 'id' in correctLevel.attrs:
            break
    link = correctLevel.find('a')['data-href']
    rLID = link.split("/")[-1]
    rLIDSoup = await getrLIDSoup(rLID)
    return wiimmfi_url + link, rLID, rLIDSoup #link example: /stats/mkwx/list/r1279851

#load_me can be an FC, roomID or rxxxxxx number, or discord name. Order of checking is the following: 
#Discord name, rxxxxxxx, FC, roomID
async def getRoomDataSmart(load_me):
    if not isinstance(load_me, list):
        load_me = load_me.strip().lower()
        if _is_rLID(load_me):
            return await getRoomData(load_me)
        
        if _is_fc(load_me):
            return await getRoomDataByFC([load_me])
        
        FCs = UserDataProcessing.getFCsByLoungeName(load_me)
        return await getRoomDataByFC(FCs)
        
    if isinstance(load_me, list):
        return await getRoomDataByFC(load_me)
    

async def getRoomHTMLDataSmart(load_me):
    if not isinstance(load_me, list):
        load_me = load_me.strip().lower()
        
        if _is_fc(load_me):
            return await getMKWXHTMLDataByFC([load_me])
        
        
        FCs = UserDataProcessing.getFCsByLoungeName(load_me)
        return await getMKWXHTMLDataByFC(FCs)
        
    if isinstance(load_me, list):
        return await getMKWXHTMLDataByFC(load_me)


#soups is a list of beautiful soup objects
def combineSoups(soups):
    last_soup = None
    for soup_num, soup in enumerate(soups):
        if soup_num == 0:
            last_soup = soup
        else:
            table_body = last_soup.find('table')
            table_body.append(soup.find('table'))
            
    while len(soups) > 0:
        del soups[0]
    
    return last_soup
    
