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
TINYURL_API_TOKEN = None

BITLY_URL_SHORTEN_API_URL = "https://api-ssl.bitly.com/v4/shorten"
BITLY_URL_SHORTEN_API_HEADERS =  {}

TINYURL_URL_SHORTEN_API_URL = "https://tinyurl.com/api-create.php?url="
TINYURL_SPECIAL_URL_SHORTEN_API_URL = 'https://api.tinyurl.com/create?api_token={0}'

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
        async with session.post(BITLY_URL_SHORTEN_API_URL, data=str(post_data), ssl=common.sslcontext) as response:
            if response.status != 200:
                raise URLShortenFailure(str(await response.json()))
            return await get_shortened_url_from_response(response)
        
async def tinyurl_shorten_url(url: str):
    async with aiohttp.ClientSession() as session:
        full_url = TINYURL_URL_SHORTEN_API_URL + url
        async with session.get(full_url, ssl=common.sslcontext) as response:
            if response.status != 200:
                raise URLShortenFailure(f"TinyURL failed. Status code: {response.status}")
            return await response.text()

async def tinyurl_shorten_url_special(url: str):
    request_url = TINYURL_SPECIAL_URL_SHORTEN_API_URL.format(TINYURL_API_TOKEN)
    request_body = {
            "url": url
        }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=request_url, data=request_body, ssl=common.sslcontext) as res:
            json = await res.json()
            if res.status != 200:
                raise URLShortenFailure(f"TinyURL failed. Status code: {res.status}. Errors: {json['errors']}")
            return json['data']['tiny_url']

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
    
    global BITLY_API_TOKEN, TINYURL_API_TOKEN
    with open(common.PRIVATE_INFO_FILE, "r", encoding="utf-8") as f:
        read_next_token(f)
        read_next_token(f)
        read_next_token(f)
        BITLY_API_TOKEN = read_next_token(f)
        TINYURL_API_TOKEN = read_next_token(f)
        # reload_module()
      
async def __shorten_test_url__(url, special=False):
    shorten_test = tinyurl_shorten_url_special if special else tinyurl_shorten_url
    print(await shorten_test(url))
    
if __name__ == "__main__":
    __private_load__()
    common.run_async_function_no_loop(__shorten_test_url__("https://www.mkwlounge.gg/ladder/tabler.php?type=rt&import=%7B%22format%22%3A%222%22%2C%22tier%22%3A%22Tier%201%22%2C%22teams%22%3A%5B%7B%22players%22%3A%5B%7B%22player_id%22%3A1943%2C%22races%22%3A12%2C%22score%22%3A25%7D%2C%7B%22player_id%22%3A2270%2C%22races%22%3A12%2C%22score%22%3A14%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A3522%2C%22races%22%3A12%2C%22score%22%3A21%7D%2C%7B%22player_id%22%3A2033%2C%22races%22%3A12%2C%22score%22%3A5%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A2749%2C%22races%22%3A12%2C%22score%22%3A16%7D%2C%7B%22player_id%22%3A2964%2C%22races%22%3A12%2C%22score%22%3A8%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A3231%2C%22races%22%3A12%2C%22score%22%3A13%7D%2C%7B%22player_id%22%3A3182%2C%22races%22%3A12%2C%22score%22%3A11%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A3191%2C%22races%22%3A12%2C%22score%22%3A15%7D%2C%7B%22player_id%22%3A2665%2C%22races%22%3A12%2C%22score%22%3A5%7D%5D%7D%2C%7B%22players%22%3A%5B%7B%22player_id%22%3A3565%2C%22races%22%3A12%2C%22score%22%3A8%7D%2C%7B%22player_id%22%3A3555%2C%22races%22%3A12%2C%22score%22%3A5%7D%5D%7D%5D%7D"))
    common.run_async_function_no_loop(__shorten_test_url__(special=True, url="https://gb.hlorenzi.com/table?data=%23title%2060%20races%0AFFA%0A%E3%81%AB%E3%82%93%E3%81%92%E3%82%93%E3%82%92%E3%82%84%E3%82%81%E3%82%8B%E3%81%9E%EF%BC%81%200%7C35%7C41%7C31%7C33%7C15%7C30%7C57%7C36%7C46%7C34%7C27%7C60%7C13%7C0%0A%E3%81%B2%E3%81%8B%E3%81%A1%E3%82%83%E3%82%93%200%7C0%7C0%7C0%7C0%7C12%7C25%7C43%7C37%7C15%7C29%7C31%7C17%7C0%7C0%0AP%CF%82%C2%A5%C2%A2H%CE%B8%E2%98%86MK%CF%8E%200%7C0%7C0%7C0%7C0%7C0%7C0%7C20%7C37%7C22%7C40%7C29%7C24%7C8%7C0%0AKomossa%200%7C0%7C0%7C0%7C20%7C26%7C31%7C23%7C12%7C5%7C24%7C21%7C17%7C0%7C0%0Al%CE%B1g1422%200%7C0%7C0%7C0%7C0%7C0%7C0%7C17%7C19%7C17%7C0%7C0%7C28%7C43%7C28%0A%EF%81%B8%20rona%EF%81%A9%200%7C0%7C0%7C53%7C28%7C47%7C17%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%0A%3F%3F%3F%200%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C17%7C15%7C38%7C23%7C21%7C13%0ACl%C3%A9ment%E2%98%86XR%200%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C15%7C48%7C52%0A%E2%99%AAW%CF%83f%CF%83%200%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C36%7C44%7C24%7C0%7C0%7C0%0AJake%2024%7C24%7C26%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C16%7C12%0A%E3%82%AD%E3%83%8C%E3%83%88%E3%83%B3%200%7C0%7C0%7C25%7C32%7C36%7C9%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%0ALed%200%7C13%7C23%7C19%7C0%7C0%7C22"))