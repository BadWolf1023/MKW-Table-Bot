'''
Created on Apr 3, 2021

@author: willg
'''
import hashlib
import aiohttp
import base64
import binascii
from typing import Tuple
import Mii
import miirender
#import requests
import common
from datetime import timedelta, datetime
from typing import Set, List, Dict

from xml.dom.minidom import parse, parseString

wiimmfi_sake = 'http://mariokartwii.sake.gs.wiimmfi.de/SakeStorageServer/StorageServer.asmx'
NO_MII_ERROR_MESSAGE = "No user could be found."
MII_DOWNLOAD_FAILURE_ERROR_MESSAGE = "An unknown error occurred. The rendering server might be down."

SAKE_POST_DATA ="""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ns1="http://gamespy.net/sake">
  <SOAP-ENV:Body>
    <ns1:SearchForRecords>
      <ns1:gameid>1687</ns1:gameid>
      <ns1:secretKey>9Rmy</ns1:secretKey>
      <ns1:loginTicket>23c715d620f986c22Pwwii</ns1:loginTicket>
      <ns1:tableid>FriendInfo</ns1:tableid>
      <ns1:filter>{}</ns1:filter>
      <ns1:sort>recordid</ns1:sort>
      <ns1:offset>0</ns1:offset>
      <ns1:max>{}</ns1:max>
      <ns1:surrounding>0</ns1:surrounding>
      <ns1:ownerids></ns1:ownerids>
      <ns1:cacheFlag>0</ns1:cacheFlag>
      <ns1:fields>
        <ns1:string>info</ns1:string>
        <ns1:string>ownerid</ns1:string>
      </ns1:fields>
    </ns1:SearchForRecords>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

#Add Content-Length: if requests doesn't already add this or if SAKE server gives issues
SAKE_HEADERS = {"Host":"mariokartwii.sake.gs.wiimmfi.de",
                "User-Agent":"GameSpyHTTP/1.0",
                "Connection":"close",
                "Content-Type": "text/xml",
                "SOAPAction":"http://gamespy.net/sake/SearchForRecords"}

MII_CACHE = {}
REQUEST_TIME_OUT_SECONDS = 5
MII_DEFAULT_CACHE_TIME = timedelta(minutes=10)
MIN_FAILURES_BEFORE_BACKOFF = 3
BACK_OFF_SECONDS_AMOUNT = 20
DYNAMIC_CACHER_COOLDOWN = timedelta(hours=2)
MAXIMUM_FAILURES = 30
MII_DYNAMIC_CACHER = [datetime.now(), 0, MII_DEFAULT_CACHE_TIME] #date of last reset
from copy import copy

def update_pulling_mii_failed():
    MII_DYNAMIC_CACHER[1] += 1
    update_dynamic_cacher()
    
def update_dynamic_cacher():
    if MII_DYNAMIC_CACHER[1] > MIN_FAILURES_BEFORE_BACKOFF:
        MII_DYNAMIC_CACHER[2] = timedelta(seconds=(BACK_OFF_SECONDS_AMOUNT*(MII_DYNAMIC_CACHER[1]-MIN_FAILURES_BEFORE_BACKOFF))) + MII_DEFAULT_CACHE_TIME
        
def reset_dynamic_cacher_if_needed():
    if (datetime.now() - DYNAMIC_CACHER_COOLDOWN) > MII_DYNAMIC_CACHER[0]:
        MII_DYNAMIC_CACHER[0] = datetime.now()
        MII_DYNAMIC_CACHER[1] = 0
        MII_DYNAMIC_CACHER[2] = MII_DEFAULT_CACHE_TIME

def cache_time_expired(last_access_time):
    return (datetime.now() - last_access_time) > MII_DYNAMIC_CACHER[2]

def update_mii_cache(mii_datas):
    for fc, (mii_bytes, mii_hex_str) in mii_datas.items():
        MII_CACHE[fc] = [(mii_bytes, mii_hex_str), datetime.now()]

def get_unexpired_cached_mii_datas(fcs:Set[str]) -> Set[str]:
    if MII_DYNAMIC_CACHER[1] > MAXIMUM_FAILURES:
        return None, None
    result = set()
    for fc in fcs:
        if fc in MII_CACHE:
            if not cache_time_expired(MII_CACHE[fc][1]):
                result.add(fc)
    return result, (len(result) == len(fcs))

def get_sake_post_data(player_ids):
    player_id_args = [f"ownerid={pid}" for pid in player_ids]
    return SAKE_POST_DATA.format(" || ".join(player_id_args), len(player_ids))

def fix_fc_text(fc:str) -> int:
    #Takes an FC in the format xxxx-xxxx-xxxx and converts it into a usable int for wiifc
    return int(fc.replace("-",""))

def wiifc(pid, id4) -> Tuple[int, int]:
    ''' Return a tuple containing the 32-bit PID and the
        resulting friend code using the Wii algorithm. '''
    name = bytes([
        (pid >>  0) & 0xFF,
        (pid >>  8) & 0xFF,
        (pid >> 16) & 0xFF,
        (pid >> 24) & 0xFF,
        int(id4[3]),
        int(id4[2]),
        int(id4[1]),
        int(id4[0])])
    hash_ = int(hashlib.md5(name).hexdigest()[:2], 16) >> 1
    return (pid & 0xFFFFFFFF), ((hash_ << 32) | (pid & 0xFFFFFFFF))

def mii_data_is_corrupt(mii_data:str):
    return mii_data == b''

def format_sake_xml_response(sake_response):
    return parseString(sake_response)

async def get_mii_data_for_pids(pids:Dict[int, str]) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(wiimmfi_sake, headers=SAKE_HEADERS, data=get_sake_post_data(pids), ssl=common.sslcontext, timeout=REQUEST_TIME_OUT_SECONDS) as data:
                sake_response = str(await data.content.read())
                print(sake_response)
                sake_response = format_sake_xml_response(sake_response)
                print(sake_response)
                #miidatahex = base64.b64decode(miidatab64[399:527])
                #encode = binascii.hexlify(miidatahex)
                #if mii_data_is_corrupt(encode):
                #    update_pulling_mii_failed()
                #    return None
                #return (miidatahex, str(encode)[2:-1])
    except:
        update_pulling_mii_failed()
        return None

async def get_mii_data_for_fcs(fcs:Set[str]):
    pids_mapping = {wiifc(fix_fc_text(fc), b'RMCJ')[0]:fc for fc, _ in fcs}
    mii_datas = await get_mii_data_for_pids(pids_mapping)
    if mii_datas is None:
        return None
    result = {}
    for pid in mii_datas:
        result[pids_mapping[pid]] = mii_datas[pid]
    return result

async def get_miis(fcs:List[str], message_id:str, picture_width=512):
    reset_dynamic_cacher_if_needed()
    if len(fcs) == 0:
        return {}
    fcs = set(fcs)
    
    fcs_in_cache, all_miis_cached = get_unexpired_cached_mii_datas(fcs)
    if all_miis_cached is not None or all_miis_cached is False:
        uncached_mii_fcs = fcs.difference(fcs_in_cache)
        mii_datas = await get_mii_data_for_fcs(uncached_mii_fcs)
        if mii_datas is None:
            return NO_MII_ERROR_MESSAGE
        update_mii_cache(mii_datas)
    
    found_fcs, _ = get_unexpired_cached_mii_datas(fcs)
    if found_fcs is None:
        return NO_MII_ERROR_MESSAGE
    found_data = {fc:copy(MII_CACHE[fc]) for fc in found_fcs}
        
    if len(found_data) == 0:
        return NO_MII_ERROR_MESSAGE
    
    for fc, ((mii_bytes, mii_hex_str), _) in found_data.items():
        file_name = message_id + "_" + fc + '.png'
        folder_path = common.MIIS_PATH
        full_download_path = folder_path + file_name
        success = await miirender.download_mii(mii_hex_str, full_download_path, picture_width=picture_width)
        if success is None:
            return MII_DOWNLOAD_FAILURE_ERROR_MESSAGE
        return Mii.Mii(mii_bytes, mii_hex_str, folder_path, file_name, fc)


"""
#======================== The functions below are the same as above, except they are BLOCKING ========================
def get_mii_data_from_pid_blocking(playerid:int) -> str:
    try:
        mii_data = requests.post(wiimmfi_sake, headers=SAKE_HEADERS, data=get_sake_post_data(playerid), verify=common.certifi.where(), timeout=REQUEST_TIME_OUT_SECONDS)
        miidatab64 = str(mii_data.content)
        miidatahex = base64.b64decode(miidatab64[399:527])
        encode = binascii.hexlify(miidatahex)
        return (miidatahex, str(encode)[2:-1]) if not mii_data_is_corrupt(encode) else (None, None)
    except:
        update_pulling_mii_failed()
        return None, None

def get_mii_data_blocking(fc:str):
    pid, _ = wiifc(fix_fc_text(fc), b'RMCJ')
    return get_mii_data_from_pid_blocking(pid)

def get_mii_blocking(fc:str, message_id:str, picture_width=512):
    reset_dynamic_cacher_if_needed()
    mii_bytes, mii_hex_str, should_use_cache = get_mii_data_if_cached(fc)
    if not should_use_cache:
        mii_bytes, mii_hex_str = get_mii_data_blocking(fc)
        mii_cache_update(fc, mii_bytes, mii_hex_str)
        
    if mii_bytes is None:
        return NO_MII_ERROR_MESSAGE
    else:
        file_name = message_id + "_" + fc + '.png'
        folder_path = common.MIIS_PATH
        full_download_path = folder_path + file_name
        success = miirender.download_mii_blocking(mii_hex_str, full_download_path, picture_width=picture_width)
        if success is None:
            return MII_DOWNLOAD_FAILURE_ERROR_MESSAGE
        return Mii.Mii(mii_bytes, mii_hex_str, folder_path, file_name, fc)
"""
if __name__ == "__main__":
    while True:
        next_mii_data = input("Enter next wiimmfi sake data: ")
        try:
            temp = miirender.format_mii_data(binascii.hexlify(base64.b64decode(next_mii_data)))
            print(temp)
        except Exception as e:
            print(e)