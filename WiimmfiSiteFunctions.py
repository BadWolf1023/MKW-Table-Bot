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
    FAILED_REQUEST = object()
    NOT_ON_FRONT_PAGE = object()
    NO_KNOWN_FCS = object()
    HAS_NO_RACES = object()
    NO_ROOM_LOADED = object()
    SUCCESS = object()
    SUCCESS_BUT_NO_WAR = object()
    FAILURE_CODES = {FAILED_REQUEST, NOT_ON_FRONT_PAGE, HAS_NO_RACES, NO_ROOM_LOADED, NO_KNOWN_FCS}
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


async def get_room_HTML(room_link: str) -> Union[str, None]:
    '''Upon a successful request, returns HTML string of a given link with all of the cloudflare emails cleaned up.
    If the request is not successful, returns None'''
    if room_link in special_test_cases:
        description, local_file_path = special_test_cases[room_link]
        with codecs.open(local_file_path, "r", "utf-8") as fp:
            return fix_cloudflare_email(fp.read())

    html_text = await url_cacher.get_url(room_link, cache_length)
    return None if html_text is None else fix_cloudflare_email(html_text)


async def _get_mkwx_soup() -> Union[BeautifulSoup, None]:
    '''Returns Beautifulsoup version of main Wiimmfi.de mkwx page with all the cloudflare emails fixed.
    The returned page may or may not be a cached version.
    If the request to the page faile, None is returned'''
    mkwx_HTML = await url_cacher.get_url(MKWX_URL, cache_length)
    return None if mkwx_HTML is None else BeautifulSoup(fix_cloudflare_email(mkwx_HTML), "html.parser")


async def get_mkwx_soup() -> Tuple[RoomLoadStatus, Union[BeautifulSoup, None]]:
    '''RETURNS FAILED_REQUEST, SUCCESS
    Returns Beautifulsoup version of main Wiimmfi.de mkwx page with all the cloudflare emails fixed.
    The returned page may or may not be a cached version.
    If common.STUB_MKWX is enabled, the mkwx page in the testing_rooms directory will be used rather than making a request for the Wiimmfi.de mkwx page
    If the request to the page failed, None is returned
    '''
    if common.STUB_MKWX:
        with codecs.open(common.STUB_MKWX_FILE_NAME, "r", "utf-8") as fp:
            return RoomLoadStatus(RoomLoadStatus.SUCCESS), BeautifulSoup(fix_cloudflare_email(fp.read()), "html.parser")
    mkwx_soup = await _get_mkwx_soup()
    if mkwx_soup is None:
        return RoomLoadStatus(RoomLoadStatus.FAILED_REQUEST), None
    return RoomLoadStatus(RoomLoadStatus.SUCCESS), mkwx_soup


async def get_room_soup(rxx: str) -> Tuple[RoomLoadStatus, Union[BeautifulSoup, None]]:
    '''RETURNS FAILED_REQUEST, HAS_NO_RACES, SUCCESS'''
    room_HTML = await get_room_HTML(SUB_MKWX_URL + rxx)
    if room_HTML is None:
        return RoomLoadStatus(RoomLoadStatus.FAILED_REQUEST), None
    temp = BeautifulSoup(room_HTML, "html.parser")
    if temp.find(text="No match found!") is None:
        return RoomLoadStatus(RoomLoadStatus.SUCCESS), temp
    return RoomLoadStatus(RoomLoadStatus.HAS_NO_RACES), None


async def get_front_race_by_fc(fcs: List[str]) -> Tuple[RoomLoadStatus, Union[Race, None]]:
    '''RETURNS NOT_ON_FRONT_PAGE, FAILED_REQUEST, SUCCESS'''
    status, mkwx_soup = await get_mkwx_soup()
    if not status:
        return status, None
    parser = WiimmfiParser.FrontPageParser(mkwx_soup)
    for front_page_race in parser.get_front_room_races():
        for fc in fcs:
            if front_page_race.hasFC(fc):
                return RoomLoadStatus(RoomLoadStatus.SUCCESS), front_page_race
    return RoomLoadStatus(RoomLoadStatus.NOT_ON_FRONT_PAGE), None


async def get_front_race_smart(smart_type: ST.SmartLookupTypes, hit_lounge_api=False) -> Tuple[RoomLoadStatus, Union[Race, None]]:
    '''RETURNS NOT_ON_FRONT_PAGE, NO_KNOWN_FCS, FAILED_REQUEST, SUCCESS'''
    if hit_lounge_api:
        await smart_type.lounge_api_update()
    fcs = smart_type.get_fcs()
    if fcs is None:
        return RoomLoadStatus(RoomLoadStatus.NO_KNOWN_FCS), None
    status_code, front_race = await get_front_race_by_fc(fcs)
    if status_code and hit_lounge_api:
        await ST.SmartLookupTypes(front_race.getFCs(), allowed_types=ST.SmartLookupTypes.PLAYER_LOOKUP_TYPES).lounge_api_update()
    return status_code, front_race


async def get_races_for_rxx(rxx: str, hit_lounge_api=False) -> Tuple[RoomLoadStatus, str, List[Race]]:
    '''RETURNS HAS_NO_RACES, FAILED_REQUEST, SUCCESS'''
    status, room_page_soup = await get_room_soup(rxx)
    if not status:
        return status, rxx, []
    room_page_parser = WiimmfiParser.RoomPageParser(room_page_soup)
    if not room_page_parser.has_races():
        return RoomLoadStatus(RoomLoadStatus.HAS_NO_RACES), rxx, []
    if hit_lounge_api:
        await ST.SmartLookupTypes(room_page_parser.get_all_fcs(), allowed_types=ST.SmartLookupTypes.PLAYER_LOOKUP_TYPES).lounge_api_update()
    return RoomLoadStatus(RoomLoadStatus.SUCCESS), rxx, room_page_parser.get_room_races()


async def get_races_by_fcs(fcs: List[str], hit_lounge_api=False) -> Tuple[RoomLoadStatus, Union[None, str], List[Race]]:
    '''RETURNS NOT_ON_FRONT_PAGE, HAS_NO_RACES, FAILED_REQUEST, SUCCESS'''
    status_code, front_page_race = await get_front_race_by_fc(fcs)
    if not status_code:
        return status_code, None, []
    rxx = front_page_race.get_rxx()
    return await get_races_for_rxx(rxx, hit_lounge_api)


@TimerDebuggers.timer_coroutine
async def get_races_smart(smart_type: ST.SmartLookupTypes, hit_lounge_api=False) ->  Tuple[RoomLoadStatus, Union[None, str], List[Race]]:
    '''RETURNS NOT_ON_FRONT_PAGE, HAS_NO_RACES, NO_KNOWN_FCS, FAILED_REQUEST, SUCCESS'''
    if smart_type.is_rxx():
        return await get_races_for_rxx(smart_type.modified_original, hit_lounge_api)
    if hit_lounge_api:
        await smart_type.lounge_api_update()
    fcs = smart_type.get_fcs()
    if fcs is None:
        return RoomLoadStatus(RoomLoadStatus.NO_KNOWN_FCS), None, []
    return await get_races_by_fcs(fcs, hit_lounge_api)
