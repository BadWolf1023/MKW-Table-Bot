'''
Created on Jul 30, 2020

@author: willg
'''
import codecs
import re
from datetime import timedelta
from typing import List, Union, Tuple

from bs4 import BeautifulSoup

import common
import URLCacher
import WiimmfiParser
from Race import Race
import SmartTypes as ST
import TimerDebuggers

class RoomLoadStatus:
    DOES_NOT_EXIST = object()
    NO_KNOWN_FCS = object()
    HAS_NO_RACES = object()
    NO_ROOM_LOADED = object()
    SUCCESS = object()
    SUCCESS_BUT_NO_WAR = object()
    FAILURE_CODES = {DOES_NOT_EXIST, HAS_NO_RACES, NO_ROOM_LOADED, NO_KNOWN_FCS}
    SUCCESS_CODES = {SUCCESS, SUCCESS_BUT_NO_WAR}
    def __init__(self, status):
        self.status = status
        
    def __bool__(self):
        # The sets of error codes might not be mutually exclusive in the future, so we'll do a standard if else check
        if self.was_success():
            return True
        elif self.was_failure():
            return False
        else:
            return False

    def was_success(self):
        return self.status in RoomLoadStatus.SUCCESS_CODES
    def was_failure(self):
        return self.status in RoomLoadStatus.FAILURE_CODES

cache_length = timedelta(seconds=30)
url_cacher = URLCacher.URLCacher()


WIIMMFI_URL = 'https://wiimmfi.de'
MKWX_URL = 'https://wiimmfi.de/stats/mkwx'
if common.USING_LINUX_PROXY:
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
f"{SUB_MKWX_URL}r0000010":("Room to test component suggestions with (ties).", f"{common.SAVED_ROOMS_DIR}Ties_Testing.html")
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


async def get_room_HTML(room_link: str) -> str:
    if room_link in special_test_cases:
        description, local_file_path = special_test_cases[room_link]
        with codecs.open(local_file_path, "r", "utf-8") as fp:
            return fix_cloudflare_email(fp.read())

    temp = await url_cacher.get_url(room_link, cache_length)
    return fix_cloudflare_email(temp)


async def _get_mkwx_soup() -> BeautifulSoup:
    mkwx_HTML = await url_cacher.get_url(MKWX_URL, cache_length)
    return BeautifulSoup(fix_cloudflare_email(mkwx_HTML), "html.parser")


async def get_mkwx_soup() -> BeautifulSoup:
    if common.STUB_MKWX:
        with codecs.open(common.STUB_MKWX_FILE_NAME, "r", "utf-8") as fp:
            return BeautifulSoup(fix_cloudflare_email(fp.read()), "html.parser")
    return await _get_mkwx_soup()


async def get_room_soup(rxx: str) -> Union[BeautifulSoup, None]:
    room_HTML = await get_room_HTML(SUB_MKWX_URL + rxx)
    temp = BeautifulSoup(room_HTML, "html.parser")
    if temp.find(text="No match found!") is None:
        return temp


async def get_front_race_by_fc(fcs: List[str]) -> Tuple[RoomLoadStatus, Union[Race, None]]:
    parser = WiimmfiParser.FrontPageParser(await get_mkwx_soup())
    for front_page_race in parser.get_front_room_races():
        for fc in fcs:
            if front_page_race.hasFC(fc):
                return RoomLoadStatus(RoomLoadStatus.SUCCESS), front_page_race
    return RoomLoadStatus(RoomLoadStatus.DOES_NOT_EXIST), None


async def get_front_race_smart(needle: Union[str, List[str]], hit_lounge_api=False) -> Tuple[RoomLoadStatus, Union[Race, None], ST.SmartLookupTypes]:
    smart_type = ST.SmartLookupTypes(needle, allowed_types=ST.SmartLookupTypes.PLAYER_LOOKUP_TYPES)
    if hit_lounge_api:
        await smart_type.lounge_api_update()
    fcs = smart_type.get_fcs()
    if fcs is None:
        return RoomLoadStatus(RoomLoadStatus.NO_KNOWN_FCS), None, smart_type
    status_code, front_race = await get_front_race_by_fc(fcs)
    if status_code and hit_lounge_api:
        await ST.SmartLookupTypes(front_race.getFCs(), allowed_types=ST.SmartLookupTypes.PLAYER_LOOKUP_TYPES).lounge_api_update()
    return status_code, front_race, smart_type


async def get_races_for_rxx(rxx: str, hit_lounge_api=False) -> Tuple[RoomLoadStatus, str, List[Race]]:
    room_page_soup = await get_room_soup(rxx)
    if room_page_soup is None:
        return RoomLoadStatus(RoomLoadStatus.DOES_NOT_EXIST), rxx, []
    room_page_parser = WiimmfiParser.RoomPageParser(room_page_soup)
    if not room_page_parser.has_races():
        return RoomLoadStatus(RoomLoadStatus.HAS_NO_RACES), rxx, []
    if hit_lounge_api:
        await ST.SmartLookupTypes(room_page_parser.get_all_fcs(), allowed_types=ST.SmartLookupTypes.PLAYER_LOOKUP_TYPES).lounge_api_update()
    return RoomLoadStatus(RoomLoadStatus.SUCCESS), rxx, room_page_parser.get_room_races()


async def get_races_by_fcs(fcs: List[str], hit_lounge_api=False) -> Tuple[RoomLoadStatus, Union[None, str], List[Race]]:
    status_code, front_page_race = await get_front_race_by_fc(fcs)
    if not status_code:
        return status_code, None, []
    rxx = front_page_race.get_rxx()
    return await get_races_for_rxx(rxx, hit_lounge_api)


# load_me can be an FC, or rxx number, or discord name. Order of checking is the following:
# list of FCs, rxx, FC, Discord name
# If no FC or discord name can be found on the front page, (None, []) is returned
# If the FC or discord name or rxx number is found, but the room page has not played any races yet, (rxx, []) is returned
# Otherwise, if the lookup was successful and there have been races played, (rxx, [Race]) is returned
@TimerDebuggers.timer_coroutine
async def get_races_smart(load_me: Union[str, List[str]], hit_lounge_api=False) ->  Tuple[RoomLoadStatus, Union[None, str], List[Race], ST.SmartLookupTypes]:
    smart_type = ST.SmartLookupTypes(load_me, allowed_types=ST.SmartLookupTypes.ROOM_LOOKUP_TYPES)
    if smart_type.is_rxx():
        return *await get_races_for_rxx(load_me, hit_lounge_api), smart_type
    if hit_lounge_api:
        await smart_type.lounge_api_update()
    fcs = smart_type.get_fcs()
    if fcs is None:
        return RoomLoadStatus(RoomLoadStatus.NO_KNOWN_FCS), None, [], smart_type
    return *await get_races_by_fcs(fcs, hit_lounge_api), smart_type


if __name__ == '__main__':
    from time import sleep
    #for i in range(100):
    soup = common.run_async_function_no_loop(get_mkwx_soup())
    parser_obj = WiimmfiParser.FrontPageParser(soup)
    #sleep(int(cache_length.total_seconds())+1)

    #ctgp_wws = sr.get_CTGP_WWs()
    #for ctgp_ww in ctgp_wws:
    #    print(ctgp_ww.get_room_name(), ctgp_ww.getRoomRating())
    #print(FrontPageParser.get_embed_text_for_race(ctgp_wws, 0)[1])
