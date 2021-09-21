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

TINYURL_URL_SHORTEN_API_URL = "https://tinyurl.com/api-create.php?url="

class URLShortenFailure(Exception):
    pass

async def get_shortened_url_from_response(response):
    try:
        resp_json = await response.json()
        assert isinstance(resp_json["link"], str)
        return resp_json["link"]
    except:
        raise URLShortenFailure("Bitly gave back corrupt JSON.")
    
async def bitly_shorten_url(url:str):
    async with aiohttp.ClientSession(headers=BITLY_URL_SHORTEN_API_HEADERS) as session:
        post_data = build_url_bitly_shortening_data(url)
        async with session.post(BITLY_URL_SHORTEN_API_URL, data=str(post_data)) as response:
            if response.status != 200:
                raise URLShortenFailure(str(await response.json()))
            return await get_shortened_url_from_response(response)
        
async def tinyurl_shorten_url(url:str):
    async with aiohttp.ClientSession() as session:
        full_url = TINYURL_URL_SHORTEN_API_URL + url
        async with session.get(full_url) as response:
            if response.status != 200:
                raise URLShortenFailure(f"Tiny URL failed. Status code: {response.status}")
            return await response.text()

def build_url_bitly_shortening_data(url:str):
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
    with open(common.PRIVATE_INFO_FILE, "r", encoding="utf-8") as f:
        read_next_token(f)
        read_next_token(f)
        read_next_token(f)
        BITLY_API_TOKEN = read_next_token(f)
        reload_module()
      
async def __shorten_test_url__(url):  
    print(await tinyurl_shorten_url(url))
    
if __name__ == "__main__":
    __private_load__()
    common.run_async_function_no_loop(__shorten_test_url__("https://www.mkwlounge.gg/ladder/tabler.php?type=rt&import=%7B%22format%22%3A%222%22%2C%22tier%22%3A%22Tier%201%22%2C%22teams%22%3A%5B%7B%22players%22%3A%5B%7B%22player_id%22%3A1943%2C%22races%22%3A12%2C%22score%22%3A25%7D%2C%7B%22player_id%22%3A2270%2C%22races%22%3A12%2C%22score%22%3A14%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A3522%2C%22races%22%3A12%2C%22score%22%3A21%7D%2C%7B%22player_id%22%3A2033%2C%22races%22%3A12%2C%22score%22%3A5%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A2749%2C%22races%22%3A12%2C%22score%22%3A16%7D%2C%7B%22player_id%22%3A2964%2C%22races%22%3A12%2C%22score%22%3A8%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A3231%2C%22races%22%3A12%2C%22score%22%3A13%7D%2C%7B%22player_id%22%3A3182%2C%22races%22%3A12%2C%22score%22%3A11%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A3191%2C%22races%22%3A12%2C%22score%22%3A15%7D%2C%7B%22player_id%22%3A2665%2C%22races%22%3A12%2C%22score%22%3A5%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A3565%2C%22races%22%3A12%2C%22score%22%3A8%7D%2C%7B%22player_id%22%3A3555%2C%22races%22%3A12%2C%22score%22%3A5%7D%5D%7D%5D%7D"))
