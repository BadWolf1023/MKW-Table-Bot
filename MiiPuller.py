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
import requests
import common
from datetime import timedelta, datetime



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
      <ns1:filter>ownerid={}</ns1:filter>
      <ns1:sort>recordid</ns1:sort>
      <ns1:offset>0</ns1:offset>
      <ns1:max>1</ns1:max>
      <ns1:surrounding>0</ns1:surrounding>
      <ns1:ownerids></ns1:ownerids>
      <ns1:cacheFlag>0</ns1:cacheFlag>
      <ns1:fields>
        <ns1:string>info</ns1:string>
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
MII_CACHE_TIME = timedelta(minutes=1)

def cache_time_expired(last_access_time, cache_time=MII_CACHE_TIME):
    return (datetime.now() - last_access_time) > cache_time

def mii_cache_update(fc, mii_bytes, mii_hex_str):
    if mii_bytes is not None and mii_hex_str is not None:
        MII_CACHE[fc] = [(mii_bytes, mii_hex_str), datetime.now()]

def get_mii_data_if_cached(fc):
    if fc in MII_CACHE:
        if not cache_time_expired(MII_CACHE[fc][1]):
            return MII_CACHE[fc][0]
    return None, None

def get_sake_post_data(player_id):
    return SAKE_POST_DATA.format(player_id)

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

async def get_mii_data_from_pid(pid:int) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(wiimmfi_sake, headers=SAKE_HEADERS, data=get_sake_post_data(pid), ssl=common.sslcontext) as data:
            miidatab64 = str(await data.content.read())
            miidatahex = base64.b64decode(miidatab64[399:527])
            encode = binascii.hexlify(miidatahex)
            return (miidatahex, str(encode)[2:-1]) if not mii_data_is_corrupt(encode) else (None, None)
    return None, None

async def get_mii_data(fc:str):
    pid, _ = wiifc(fix_fc_text(fc), b'RMCJ')
    return await get_mii_data_from_pid(pid)

async def get_mii(fc:str, message_id:str, picture_width=512):
    mii_bytes, mii_hex_str = get_mii_data_if_cached(fc)
    if mii_bytes is None or mii_hex_str is None:
        mii_bytes, mii_hex_str = await get_mii_data(fc)
    mii_cache_update(fc, mii_bytes, mii_hex_str)
        
    if mii_bytes is None:
        return NO_MII_ERROR_MESSAGE
    else:
        
        file_name = message_id + "_" + fc + '.png'
        folder_path = common.MIIS_PATH
        full_download_path = folder_path + file_name
        success = await miirender.download_mii(mii_hex_str, full_download_path, picture_width=picture_width)
        if success is None:
            return MII_DOWNLOAD_FAILURE_ERROR_MESSAGE
        return Mii.Mii(mii_bytes, mii_hex_str, folder_path, file_name, fc)



#======================== The functions below are the same as above, except they are BLOCKING ========================
def get_mii_data_from_pid_blocking(playerid:int) -> str:
    try:
        mii_data = requests.post(wiimmfi_sake, headers=SAKE_HEADERS, data=get_sake_post_data(playerid), verify=common.certifi.where())
        miidatab64 = str(mii_data.content)
        miidatahex = base64.b64decode(miidatab64[399:527])
        encode = binascii.hexlify(miidatahex)
        return (miidatahex, str(encode)[2:-1]) if not mii_data_is_corrupt(encode) else (None, None)
    except:
        return None, None

def get_mii_data_blocking(fc:str):
    pid, _ = wiifc(fix_fc_text(fc), b'RMCJ')
    return get_mii_data_from_pid_blocking(pid)

def get_mii_blocking(fc:str, message_id:str, picture_width=512):
    mii_bytes, mii_hex_str = get_mii_data_if_cached(fc)
    if mii_bytes is None or mii_hex_str is None:
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
