'''
Created on Jul 30, 2020
@author: willg
'''
import codecs
import re
from datetime import timedelta
from typing import List, Union, Tuple

from bs4 import BeautifulSoup, NavigableString
import common
import URLCacher
import UserDataProcessing
import UtilityFunctions
# import WiimmfiParser
from Race import Race

cache_length = timedelta(seconds=30)
long_cache_length = timedelta(seconds=45)
url_cacher = URLCacher.URLCacher()


WIIMMFI_URL = 'https://wiimmfi.de'
MKWX_URL = 'https://wiimmfi.de/stats/mkwx'
if "mkwx_proxy_url" in common.properties:
    MKWX_URL = common.properties['mkwx_proxy_url']
SUB_MKWX_URL = f"{MKWX_URL}/list/"

special_test_cases = {
f"{SUB_MKWX_URL}r0000000":("Special room: Room has times with high deltas and a race with times that are the same as another race's times", f"{common.SAVED_ROOMS_DIR}SameTimeHighDelta.html"),
f"{SUB_MKWX_URL}r0000001":("Table Bot Challenge Room One", f"{common.SAVED_ROOMS_DIR}TableBotTestOne.html"),
f"{SUB_MKWX_URL}r0000002":("Table Bot Challenge Room Two", f"{common.SAVED_ROOMS_DIR}TableBotTestTwo.html"),
f"{SUB_MKWX_URL}r0000003":("Table Bot Remove Race Test w/ quickedit", f"{common.SAVED_ROOMS_DIR}removerace_one.html"),
f"{SUB_MKWX_URL}r0000004":("Table Bot Remove Race Test w/ quickedit, 2nd room to merge", f"{common.SAVED_ROOMS_DIR}removerace_two.html"),
f"{SUB_MKWX_URL}r0000005":("Clean room with no errors.", f"{common.SAVED_ROOMS_DIR}clean_room.html"),
f"{SUB_MKWX_URL}r0000006":("Tag in brackets.", f"{common.SAVED_ROOMS_DIR}tag_in_brackets.html"),
f"{SUB_MKWX_URL}r0000007":("Room with an unknown track name (SHA name).", f"{common.SAVED_ROOMS_DIR}unknown_track.html"),
f"{SUB_MKWX_URL}r0000008":("Room with email protected tags", f"{common.SAVED_ROOMS_DIR}email_protected.html"),
f"{SUB_MKWX_URL}r0000009":("Room to test component suggestions with.", f"{common.SAVED_ROOMS_DIR}SuggestionComponentsTesting.html"),
f"{SUB_MKWX_URL}r0000010":("Room to test component suggestions with (ties).", f"{common.SAVED_ROOMS_DIR}Ties_Testing.html"),
}

# https://github.com/jslirola/cloudflare-email-decoder/blob/master/ced/lib/processing.py
def decode_email(encoded_string: str) -> str:
    r = int(encoded_string[:2], 16)
    return ''.join([chr(int(encoded_string[i:i + 2], 16) ^ r) for i in range(2, len(encoded_string), 2)])


def fix_cloudflare_email(text: str) -> str:
    email_regex = 'data-cfemail=\"([^\"]+)\"'
    tag_regex = r'<a [^>]*="\/cdn-cgi\/l\/email-protection"[^>]*>([^<]+)<\/a>'
    out = []
    for line in text.split("\n"):
        m = re.search(email_regex, line)
        if m:
            line = re.sub(tag_regex, decode_email(m.group(1)), line)
        out.append(line)
    return "\n".join(out)

async def getRoomHTML(roomLink):
    if roomLink in special_test_cases:
        description, local_file_path = special_test_cases[roomLink]
        fp = codecs.open(local_file_path, "r", "utf-8")
        html_data = fp.read()
        fp.close()
        return fix_cloudflare_email(html_data)
        
    temp = await url_cacher.get_url(roomLink, cache_length=long_cache_length)
    return fix_cloudflare_email(temp)


async def __getMKWXSoupCall__():
    mkwxHTML = await url_cacher.get_url(MKWX_URL, cache_length=long_cache_length)
    return BeautifulSoup(fix_cloudflare_email(mkwxHTML), "html.parser")

async def getMKWXSoup():
    if common.STUB_MKWX:
        fp = codecs.open(common.STUB_MKWX_FILE_NAME, "r", "utf-8")
        html_data = fp.read()
        fp.close()
        return BeautifulSoup(fix_cloudflare_email(html_data), "html.parser")
    return await __getMKWXSoupCall__()

async def getrLIDSoup(rLID):
    roomHTML = await getRoomHTML(SUB_MKWX_URL + rLID)
    temp = BeautifulSoup(roomHTML, "html.parser")
    if temp.find(text="No match found!") is None:
        return temp
    return None
        


#getRoomLink old name
async def getRoomData(rid_or_rlid):
    if UtilityFunctions.is_rLID(rid_or_rlid): #It is a unique rxxxxxxx number given
        #Check if the rLID is a valid link (bogus input check, or the link may have expired)
        rLIDSoup = await getrLIDSoup(rid_or_rlid)
        if rLIDSoup is not None:
            return SUB_MKWX_URL + rid_or_rlid, rid_or_rlid, rLIDSoup
        else:
            return None, None, None
        
    #Normal room ID given, go find the link for the list
    mkwxSoup = await getMKWXSoup()
        
    roomIDSpot = mkwxSoup.find(text=rid_or_rlid)
    if roomIDSpot is None:
        return None, None, None
    link = str(roomIDSpot.find_previous('a')[common.HREF_HTML_NAME])
    rLID = link.split("/")[-1]
    rLIDSoup = await getrLIDSoup(rLID)
    return WIIMMFI_URL + link, rLID, rLIDSoup #link example: /stats/mkwx/list/r1279851



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
    link = correctLevel.find('a')[common.HREF_HTML_NAME]
    rLID = link.split("/")[-1]
    rLIDSoup = await getrLIDSoup(rLID)
    return WIIMMFI_URL + link, rLID, rLIDSoup #link example: /stats/mkwx/list/r1279851

#load_me can be an FC, roomID or rxxxxxx number, or discord name. Order of checking is the following: 
#Discord name, rxxxxxxx, FC, roomID
async def getRoomDataSmart(load_me):
    if not isinstance(load_me, list):
        load_me = load_me.strip().lower()
        if UtilityFunctions.is_rLID(load_me):
            return await getRoomData(load_me)
        
        if UtilityFunctions.is_fc(load_me):
            return await getRoomDataByFC([load_me])
        
        FCs = UserDataProcessing.getFCsByLoungeName(load_me)
        return await getRoomDataByFC(FCs)
        
    if isinstance(load_me, list):
        return await getRoomDataByFC(load_me)
    

async def getRoomHTMLDataSmart(load_me):
    if not isinstance(load_me, list):
        load_me = load_me.strip().lower()
        
        if UtilityFunctions.is_fc(load_me):
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