'''
Created on Jul 14, 2021

@author: willg

This module provides asynchronous functions to easily shorten URLS using bit.ly.

A bitly account with an API key must be set up for this module to work.
'''
import aiohttp
import common
import json  

BITLY_API_TOKEN = ""

BITLY_URL_SHORTEN_API_URL = "https://api-ssl.bitly.com/v4/shorten"
BITLY_URL_SHORTEN_API_HEADERS =  {}

class URLShortenFailure(Exception):
    pass

async def get_shortened_url_from_response(response):
    try:
        resp_json = await response.json()
        assert isinstance(resp_json["link"], str)
        return resp_json["link"]
    except:
        raise URLShortenFailure("Bitly gave back corrupt JSON.")
    
async def shorten_url(url:str):
    async with aiohttp.ClientSession(headers=BITLY_URL_SHORTEN_API_HEADERS) as session:
        post_data = build_url_shortening_data(url)
        async with session.post(BITLY_URL_SHORTEN_API_URL, data=str(post_data)) as response:
            if response.status != 200:
                raise URLShortenFailure(str(await response.json()))
            return await get_shortened_url_from_response(response)

def build_url_shortening_data(url:str):
    data_dict = {"long_url": url}
    return json.dumps(data_dict, indent = 4)



#Call this function to refresh the module's global parameters after changing them
def reload_module():
    BITLY_URL_SHORTEN_API_HEADERS.clear()
    BITLY_URL_SHORTEN_API_HEADERS.update({
            "Authorization": f"Bearer {BITLY_API_TOKEN}",
            'Content-Type': 'application/json'
        })

def __private_load__():
    def read_next_token(file_handle, seperation_key = ":") -> str:
        return file_handle.readline().strip("\n").split(seperation_key)[1].strip()
    
    global BITLY_API_TOKEN
    with open(common.PRIVATE_INFO_FILE, "r") as f:
        read_next_token(f)
        read_next_token(f)
        read_next_token(f)
        BITLY_API_TOKEN = read_next_token(f)
        reload_module()
      
async def __shorten_test_url__(url):  
    print(await shorten_url(url))
    
if __name__ == "__main__":
    __private_load__()
    common.run_async_function_no_loop(__shorten_test_url__("https://dev.bitly.com"))
