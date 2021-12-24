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
import shutil
import os
import asyncio

#from xml.dom.minidom import parse, parseString
import lxml.objectify


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
MII_PHOTO_CACHE = {}
REQUEST_TIME_OUT_SECONDS = 5
MII_DEFAULT_CACHE_TIME = timedelta(minutes=10)
MII_PHOTO_CACHE_TIME = timedelta(minutes=10)
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

def photo_cache_is_expired(last_access_time):
    return (datetime.now() - last_access_time) > MII_PHOTO_CACHE_TIME 
 
def has_mii_photo_cached(fc):
    if fc not in MII_PHOTO_CACHE:
        return False
    if photo_cache_is_expired(MII_PHOTO_CACHE[fc]):
        return False
    return os.path.exists(f"{common.MIIS_CACHE_PATH}{fc}.png")

def update_mii_photo_cache(fc):
    MII_PHOTO_CACHE[fc] = datetime.now()
        

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

def parse_sake_xml_check_corrupt(sake_response):
    pid_mapping = {}
    try:
        main_value_array = sake_response["{http://schemas.xmlsoap.org/soap/envelope/}Body"]["{http://gamespy.net/sake}SearchForRecordsResponse"]["{http://gamespy.net/sake}values"]
    except AttributeError:
        return False
    else:
        if not all(arv.tag == "{http://gamespy.net/sake}ArrayOfRecordValue" for arv in main_value_array.iterchildren()):
            return False
        for record_array in main_value_array.iterchildren():
            owner_id = None
            mii_data = None
            if not all(rv.tag == "{http://gamespy.net/sake}RecordValue" for rv in record_array.iterchildren()):
                return False
            
            for record_value in record_array.iterchildren():
                try:
                    mii_data = record_value["{http://gamespy.net/sake}binaryDataValue"]["{http://gamespy.net/sake}value"].text
                except:
                    pass
                try:
                    owner_id = int(record_value["{http://gamespy.net/sake}intValue"]["{http://gamespy.net/sake}value"].text)
                except Exception as e:
                    pass

            if not isinstance(owner_id, int) or not isinstance(mii_data, str):
                return False
            pid_mapping[owner_id] = mii_data
            
    return pid_mapping
                        
    
    
def format_sake_xml_response(sake_response):
    try:
        xml = lxml.objectify.fromstring(sake_response, base_url="")
        
        return xml
    except SyntaxError:
        print("Malformed XML message:", repr(sake_response))
        return None
   
async def get_mii_data_for_pids(pids:Dict[int, str]) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(wiimmfi_sake, headers=SAKE_HEADERS, data=get_sake_post_data(pids), ssl=common.sslcontext, timeout=REQUEST_TIME_OUT_SECONDS) as data:
                sake_response = await data.content.read()
                sake_response = format_sake_xml_response(sake_response)
                result_check = parse_sake_xml_check_corrupt(sake_response)
                if result_check is False:
                    update_pulling_mii_failed()
                    return None
                return result_check
                
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
    if len(fcs) == 0:
        return {}
    pids_mapping = {wiifc(fix_fc_text(fc), b'RMCJ')[0]:fc for fc in fcs}
    mii_datas = await get_mii_data_for_pids(pids_mapping)
    if mii_datas is None:
        return None
    result = {}
    for pid in mii_datas:
        if pid in pids_mapping:
            mii_data_hex = base64.b64decode(mii_datas[pid])
            temp = binascii.hexlify(mii_data_hex)
            result[pids_mapping[pid]] = (mii_data_hex, str(temp)[2:-1])
    return result

def get_mii_file_names(fc, message_id):
    cache_file_name = fc + ".png"
    real_file_name = str(message_id) + "_" + cache_file_name
    mii_cache_folder_path = common.MIIS_CACHE_PATH
    folder_path = common.MIIS_PATH
    cache_download_path = mii_cache_folder_path + cache_file_name
    full_download_path = folder_path + real_file_name
    return cache_download_path, full_download_path, folder_path, real_file_name

async def download_mii_photo(fc, mii_hex_str, message_id, picture_width=512):
    cache_download_path, full_download_path, _, _ = get_mii_file_names(fc, message_id)
    success = await miirender.download_mii(mii_hex_str, cache_download_path, picture_width=picture_width)
    if success:
        update_mii_photo_cache(fc)
        return True
    if success is None:
        return MII_DOWNLOAD_FAILURE_ERROR_MESSAGE

def copy_cache_photo_and_get_mii(mii_bytes, mii_hex, fc, message_id):
    cache_download_path, full_download_path, folder_path, real_file_name = get_mii_file_names(fc, message_id)
    shutil.copy2(cache_download_path, full_download_path)
    return Mii.Mii(mii_bytes, mii_hex, folder_path, real_file_name, fc)
    
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
    
    fc_results = {}
    need_to_download_mii_photos = {}
    for fc, ((mii_bytes, mii_hex_str), _) in found_data.items():
        if not has_mii_photo_cached(fc):
            need_to_download_mii_photos[fc] = mii_bytes, mii_hex_str
    
    #Make Miis out of the fcs we already have cached
    for fc in found_data:
        if fc not in need_to_download_mii_photos:
            fc_results[fc] = copy_cache_photo_and_get_mii(found_data[fc][0][0], found_data[fc][0][1], fc, message_id)
    
    #Download mii photos for the ones we have missing
    max_concurrent = 6
    fcs_missing_miis = list(need_to_download_mii_photos)
    missing_fc_chunks = [fcs_missing_miis[i:i+max_concurrent] for i in range(len(fcs_missing_miis))[::max_concurrent]]
    for missing_fc_chunk in missing_fc_chunks:
        future_to_fc = {download_mii_photo(fc, need_to_download_mii_photos[fc][1], message_id, picture_width):fc for fc in missing_fc_chunk}
        results = await asyncio.gather(*future_to_fc)
        for fc, mii_pull_result in zip(missing_fc_chunk, results):
            if not isinstance(mii_pull_result, str):
                fc_results[fc] = copy_cache_photo_and_get_mii(need_to_download_mii_photos[fc][0], need_to_download_mii_photos[fc][1], fc, message_id)
   
    return fc_results

if __name__ == "__main__":
    while False:
        next_mii_data = input("Enter next wiimmfi sake data: ")
        try:
            temp = miirender.format_mii_data(binascii.hexlify(base64.b64decode(next_mii_data)))
            print(temp)
        except Exception as e:
            print(e)
        
        
    #sake_response = '''<?xml version="1.0"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><SearchForRecordsResponse xmlns="http://gamespy.net/sake"><SearchForRecordsResult>Success</SearchForRecordsResult><values><ArrayOfRecordValue><RecordValue><binaryDataValue><value>QBYAeQB1AGkAYQB6AHUAAABuAGUANEAlh0aSUxjNd/YgBIpBcP3g2iByDMgAYZgPcLAAiiUFAAAAAAAAAAAAAAAAAAAAAAAAAAAM3AAYuzMGz77WUk1DSgEnAAAYEF5r</value></binaryDataValue></RecordValue><RecordValue><intValue><value>362415797</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>wAAARABHJgUAbQBpAGwAYQAqAAAAAEAYhUqel2gZLqAgBH5AAb0osiAvDqAQaZgwZKMAiiUEAAAAAAAAAAAAAAAAAAAAAAAAAADvgwABtqrWzpVwUk1DSgEOAAAZUGOh</value></binaryDataValue></RecordValue><RecordValue><intValue><value>600199960</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>wAoAQgBCMK0w4zDzMLsw6wAAAAAAAEBAhfj/fWT2RPwgBI4AAX0EtCBwDkAAYZhPeK8AiiUEAAAAAAAAAAAAAAAAAAAAAAAAAADlkAAPYr1GzpT2Uk1DSgEDAAAenmSA</value></binaryDataValue></RecordValue><RecordValue><intValue><value>600244530</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>gBYAUwAxJccAQwBvAG8AawBpAGUAAEBAheIMUTjkx8sABHxgMX0moiBsKEASSbhNAIoAioUaAAAAAAAAAAAAAAAAAAAAAAAAAAASNgAQ6JUa31/4Uk1DRQAAAAAAW1NZ</value></binaryDataValue></RecordValue><RecordValue><intValue><value>372179566</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>gBYAWgAtACAAAABpAAAAAABlAGwAbEBAhyI7VDqJcHkEBIEgUX0GpAiMCGAUSXhtZooAiiUEAAAAAAAAAAAAAAAAAAAAAAAAAABBvQAeyPuQ30exUk1DUGAFAAAq6APM</value></binaryDataValue></RecordValue><RecordValue><intValue><value>600565835</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>wAAAUwAgAFAAcgBvAGQAaQBnAHkAAAwQghBI6UeoWGGEJzeIMuHOMCBQDoAAeJgQhOAAiiUEAEgAYQByAGwAZQB5AAAAAAAAAACAzQACjAdyz0sZUk1DUAAAAAAAW1NZ</value></binaryDataValue></RecordValue><RecordValue><intValue><value>600697536</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>wBYAQwB5AG4AdABoAGkAYQAAAAAAAFAGh0WBp2vUYSkABBnAAb0oolxsYEATSZiNeIoAiiUEAAAAAAAAAAAAAAAAAAAAAAAAAADMmAADsVga3xtSUk1DRSsEAAAMVtNS</value></binaryDataValue></RecordValue><RecordValue><intValue><value>600823787</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>QA0AUgBlAG0AaQAAAAAAAAAAAAAAAAAAh3OeezqF8zogBh/XuUAooiBxDGQQeJgQYMMAiiUEAAAAAAAAAAAAAAAAAAAAAAAAAACSfwAB7PVQ3rv7Uk1DUE4CAAAlWQmI</value></binaryDataValue></RecordValue><RecordValue><intValue><value>600869535</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>gAAwczD8MGEw6TDWJgUAQgAAAAAAAEBAhtDMESevV/IABEJAMb0oogiMCEAUSbiNAIoAiiUEAAAAAAAAAAAAAAAAAAAAAAAAAAB61wAWDQ42379pUk1DSgENAAAZgmND</value></binaryDataValue></RecordValue><RecordValue><intValue><value>601042581</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>gBYATgBZAAAAAAAAAAAAAAAAAAAAAEBAh0aJ61kXzOcABEIAMb0IogiMCEAUSbiNAIoAiiUEAAAAAAAAAAAAAAAAAAAAAAAAAAD8kgAVRpCWzx5KUk1DUDUJAAAdAR8u</value></binaryDataValue></RecordValue><RecordValue><intValue><value>601083403</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>gBYAQgBpAHQAYwBoAFMAcABpAGMAYWBAht2PZH+/Lw8ABEpAMX0GohBsBGAVQZhNAIoAiiUEAAAAAAAAAAAAAAAAAAAAAAAAAABsMQABWzQGzqVYUk1DSgEOAAAZUGOh</value></binaryDataValue></RecordValue><RecordValue><intValue><value>601143984</value></intValue></RecordValue></ArrayOfRecordValue><ArrayOfRecordValue><RecordValue><binaryDataValue><value>gBYAWABAAAAAAAAAAAAAAAAAAAAAAH8Ah2cOYBfUFcAABH9AMb0oogiMCEAUSbiNYIQAiiUEAAAAAAAAAAAAAAAAAAAAAAAAAACOOAAMoneyzqe6Uk1DUEEPAADrWHdx</value></binaryDataValue></RecordValue><RecordValue><intValue><value>601310791</value></intValue></RecordValue></ArrayOfRecordValue></values></SearchForRecordsResponse></soap:Body></soap:Envelope>'''
    #sake_response = format_sake_xml_response(sake_response)
    #print("Formatted...")
    #print(type(sake_response))
    result_1 = common.run_async_function_no_loop(get_miis(["4086-2278-0250"], "1234566"))
    print(result_1)
    common.run_async_function_no_loop(asyncio.sleep(5))
    result_2 = common.run_async_function_no_loop(get_miis(["4086-2278-0250"], "123"))
    print(result_2)
    common.run_async_function_no_loop(asyncio.sleep(5))
    result_3 = common.run_async_function_no_loop(get_miis(["4086-2278-0250", "1981-6893-9681"], "1234566"))
    print(result_3)
    