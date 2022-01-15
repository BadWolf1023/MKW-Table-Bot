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
import UserDataProcessing
import UtilityFunctions
import WiimmfiParser
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
f"{SUB_MKWX_URL}r0000008":("Room with email protected tags", f"{common.SAVED_ROOMS_DIR}email_protected.html")
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

    temp = await url_cacher.get_url(room_link, long_cache_length)
    return fix_cloudflare_email(temp)


async def _get_mkwx_soup() -> BeautifulSoup:
    mkwx_HTML = await url_cacher.get_url(MKWX_URL, long_cache_length)
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


async def get_front_race_by_fc(fcs: List[str]) -> Union[Race, None]:
    parser = WiimmfiParser.FrontPageParser(await get_mkwx_soup())
    for front_page_race in parser.get_front_room_races():
        for fc in fcs:
            if front_page_race.hasFC(fc):
                return front_page_race


# load_me can be an FC, roomID or rxxxxxx number, or discord name. Order of checking is the following: 
# Discord name, rxxxxxxx, FC, roomID
async def get_front_race_smart(load_me: Union[str, List[str]]) -> Union[Race, None]:
    if not isinstance(load_me, list):
        load_me = load_me.strip().lower()

        if UtilityFunctions.is_fc(load_me):
            return await get_front_race_by_fc([load_me])

        FCs = UserDataProcessing.getFCsByLoungeName(load_me)
        return await get_front_race_by_fc(FCs)

    if isinstance(load_me, list):
        return await get_front_race_by_fc(load_me)


async def get_races_for_rxx(rxx: str) -> Union[Tuple[None, None], Tuple[str, List[Race]]]:
    room_page_soup = await get_room_soup(rxx)
    if room_page_soup is None:
        return None, None
    room_page_parser = WiimmfiParser.RoomPageParser(room_page_soup)
    return rxx, room_page_parser.get_room_races()


async def get_races_by_fcs(fcs: List[str]) -> Union[Tuple[None, None], Tuple[str, List[Race]]]:
    front_page_race = await get_front_race_by_fc(fcs)
    if front_page_race is None:
        return None, None
    rxx = front_page_race.get_rxx()
    room_races = await get_races_for_rxx(rxx)
    return rxx, room_races


# load_me can be an FC, or rxxxxxx number, or discord name. Order of checking is the following:
# list of FCs, rxxxxxxx, FC, Discord name,
async def get_races_smart(load_me: Union[str, List[str]]) -> Union[Tuple[None, None], Tuple[str, List[Race]]]:
    if not isinstance(load_me, list):
        load_me = load_me.strip().lower()
        if UtilityFunctions.is_rxx(load_me):
            return await get_races_for_rxx(load_me)

        if UtilityFunctions.is_fc(load_me):
            return await get_races_by_fcs([load_me])

        FCs = UserDataProcessing.getFCsByLoungeName(load_me)
        return await get_races_by_fcs(FCs)

    if isinstance(load_me, list):
        return await get_races_by_fcs(load_me)


if __name__ == '__main__':
    soup = common.run_async_function_no_loop(get_mkwx_soup())
    parser_obj = WiimmfiParser.FrontPageParser(soup)

    #ctgp_wws = sr.get_CTGP_WWs()
    #for ctgp_ww in ctgp_wws:
    #    print(ctgp_ww.roomID, ctgp_ww.getRoomRating())
    #print(FrontPageParser.get_embed_text_for_race(ctgp_wws, 0)[1])
